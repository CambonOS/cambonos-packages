#!/usr/bin/env python3
"""CambonOS package repository manager.

Provides static validation, package building and transactional repository
publication. PKGBUILDs are never sourced during validation; makepkg executes
them only when the user explicitly requests a build or publication.
"""
from __future__ import annotations

import argparse
import fcntl
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
PACKAGES_DIR = ROOT / "packages"
DIST_DIR = ROOT / "dist"
OBSOLETE_PACKAGES = {"cambonos-base"}
PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9@._+:-]+$")
ARCH_RE = re.compile(r"^[A-Za-z0-9_]+$")


class CambonosError(RuntimeError):
    """Expected operational error suitable for a concise CLI message."""


@dataclass(frozen=True)
class Package:
    name: str
    directory: Path
    pkgver: str
    pkgrel: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class BuildArtifact:
    path: Path
    package_name: str


def info(message: str) -> None:
    print(f"\n==> {message}")


def warning(message: str) -> None:
    print(f"  AVISO: {message}")


def require_commands(*commands: str) -> None:
    missing = [command for command in commands if shutil.which(command) is None]
    if missing:
        raise CambonosError("faltan herramientas necesarias: " + ", ".join(missing))


def run(command: list[str], *, cwd: Path | None = None,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    print("  $ " + shlex.join(command))
    try:
        return subprocess.run(command, cwd=cwd, env=env, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise CambonosError(
            f"el comando terminó con código {exc.returncode}: {shlex.join(command)}"
        ) from exc


def extract_scalar(text: str, name: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*([^\n#]+)", text)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def extract_array(text: str, name: str) -> list[str]:
    """Parse simple static Bash arrays without evaluating a PKGBUILD."""
    match = re.search(rf"(?ms)^\s*{re.escape(name)}\s*=\s*\((.*?)\)", text)
    if not match:
        return []
    body = re.sub(r"(?m)#.*$", "", match.group(1))
    try:
        return shlex.split(body, comments=False, posix=True)
    except ValueError as exc:
        raise CambonosError(f"no se pudo interpretar el array {name}: {exc}") from exc


def dependency_name(value: str) -> str | None:
    match = re.match(r"^([A-Za-z0-9@._+:-]+)", value)
    if not match:
        return None
    return match.group(1).split(":", 1)[0]


def discover_packages() -> dict[str, Package]:
    if not PACKAGES_DIR.is_dir():
        raise CambonosError(f"no existe el directorio de paquetes: {PACKAGES_DIR}")
    packages: dict[str, Package] = {}
    for directory in sorted(p for p in PACKAGES_DIR.iterdir() if p.is_dir()):
        pkgb = directory / "PKGBUILD"
        if not pkgb.is_file():
            continue
        text = pkgb.read_text(encoding="utf-8")
        name = extract_scalar(text, "pkgname") or directory.name
        version = extract_scalar(text, "pkgver") or ""
        release = extract_scalar(text, "pkgrel") or ""
        dependencies = tuple(extract_array(text, "depends"))
        if name in packages:
            raise CambonosError(f"nombre de paquete duplicado: {name}")
        packages[name] = Package(name, directory, version, release, dependencies)
    if not packages:
        raise CambonosError(f"no se encontraron PKGBUILD en {PACKAGES_DIR}")
    return packages


def extract_function(text: str, name: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*\(\s*\)\s*\{{", text)
    if not match:
        return None
    start, depth, quote, escaped, comment = match.end(), 1, None, False, False
    i = start
    while i < len(text):
        char = text[i]
        if comment:
            if char == "\n":
                comment = False
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\" and quote != "'":
                escaped = True
            elif char == quote:
                quote = None
        else:
            if char in ("'", '"', '`'):
                quote = char
            elif char == "#":
                comment = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i]
        i += 1
    raise CambonosError(f"no se pudo localizar el cierre de {name}()")


def bash_syntax(path: Path) -> tuple[bool, str]:
    proc = subprocess.run(["bash", "-n", str(path)], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0, proc.stderr.strip()


def parse_payloads(body: str, package_dir: Path) -> list[tuple[Path, str]]:
    body = re.sub(r"\\\s*\n", " ", body)
    pattern = re.compile(
        r'''\binstall\s+-D(?:[A-Za-z0-9]+)?\s+(["']?)\$startdir/files/([^"'\s]+)\1\s+(["']?)\$pkgdir(/[^"'\s]+)\3'''
    )
    payloads: list[tuple[Path, str]] = []
    files_root = (package_dir / "files").resolve()
    for match in pattern.finditer(body):
        source = (package_dir / "files" / match.group(2)).resolve()
        if not source.is_relative_to(files_root):
            raise CambonosError(f"la fuente sale de files/: {match.group(2)!r}")
        payloads.append((source, match.group(4)))
    return payloads


def validate_one(package: Package) -> tuple[int, int]:
    errors = warnings = 0

    def err(message: str) -> None:
        nonlocal errors
        errors += 1
        print(f"  ERROR: {message}")

    def warn(message: str) -> None:
        nonlocal warnings
        warnings += 1
        warning(message)

    def ok(message: str) -> None:
        print(f"  OK: {message}")

    directory = package.directory
    pkgb = directory / "PKGBUILD"
    text = pkgb.read_text(encoding="utf-8")
    good, message = bash_syntax(pkgb)
    if good:
        ok("sintaxis Bash de PKGBUILD")
    else:
        err(f"sintaxis Bash incorrecta: {message}")
        return errors, warnings

    name = extract_scalar(text, "pkgname")
    version = extract_scalar(text, "pkgver")
    release = extract_scalar(text, "pkgrel")
    if name != directory.name:
        err(f"pkgname ({name!r}) no coincide con el directorio ({directory.name})")
    if not version or not release:
        err("faltan pkgver o pkgrel")
    elif name == directory.name:
        ok(f"metadatos: {name} {version}-{release}")

    try:
        depends = extract_array(text, "depends")
    except CambonosError as exc:
        err(str(exc))
        depends = []
    if re.search(r"(?m)^\s*(?:source|sha256sums)\s*=\s*\(", text):
        err("este repositorio instala payloads desde files/: elimina source=() y sha256sums=()")

    try:
        body = extract_function(text, "package")
        if body is None:
            raise CambonosError("no se encuentra la función package()")
        refs = re.findall(r"\$startdir/files/([^\s\"']+)", body)
        if re.search(r"\$startdir/files/(?:\$|\{)", body):
            warn("package() contiene rutas dinámicas bajo files/; requieren revisión manual")
        payloads = parse_payloads(body, directory)
        parsed_sources = {source for source, _ in payloads}
        referenced = {(directory / "files" / item.rstrip("\\")).resolve() for item in refs}
        if referenced - parsed_sources:
            warn("hay referencias a files/ que no se reconocen como origen directo de install -D")
        for source, _destination in payloads:
            if not source.is_file():
                err(f"no existe el archivo fuente: {source.relative_to(directory)}")
        if refs and len(payloads) != len(refs):
            warn(f"se detectaron {len(refs)} referencias a files/ y {len(payloads)} instalaciones estáticas")
        elif payloads:
            ok(f"{len(payloads)} archivo(s) fuente(s) de files/ comprobados")
        else:
            warn("no se detectaron instalaciones directas desde files/")

        destinations = [destination for _source, destination in payloads]
        for destination in destinations:
            if "/../" in destination or destination.endswith("/.."):
                err(f"destino inseguro con '..': {destination}")
            elif not destination.startswith(("/usr/", "/etc/", "/opt/", "/var/", "/boot/", "/lib/", "/bin/", "/sbin/")):
                err(f"destino $pkgdir fuera de rutas habituales: {destination}")
        if destinations:
            ok(f"{len(destinations)} destino(s) $pkgdir revisados")
        if re.search(r"\$(?:\{srcdir\}|srcdir)(?:/|\})", body):
            err("package() utiliza $srcdir; debe leer los payloads desde $startdir/files")
    except (CambonosError, ValueError) as exc:
        err(str(exc))

    install_name = extract_scalar(text, "install")
    if install_name:
        install_path = (directory / install_name).resolve()
        if not install_path.is_relative_to(directory.resolve()) or not install_path.is_file():
            err(f"install={install_name!r} no existe o sale del directorio del paquete")
        else:
            good, message = bash_syntax(install_path)
            if good:
                ok(f"sintaxis Bash de {install_name}")
            else:
                err(f"sintaxis Bash incorrecta en {install_name}: {message}")
    else:
        ok("sin script install asociado")

    files_dir = directory / "files"
    if files_dir.is_dir():
        for script in sorted(p for p in files_dir.rglob("*") if p.is_file()):
            try:
                first_line = script.open("r", encoding="utf-8").readline().strip()
            except UnicodeDecodeError:
                continue
            if first_line.startswith("#!") and "bash" in first_line:
                good, message = bash_syntax(script)
                if good:
                    ok(f"sintaxis Bash de {script.relative_to(directory)}")
                else:
                    err(f"sintaxis Bash incorrecta en {script.relative_to(directory)}: {message}")
        for hook in sorted(files_dir.rglob("*.hook")):
            hook_text = hook.read_text(encoding="utf-8")
            required = ("[Trigger]", "[Action]", "Operation =", "Type =", "Target =", "When =", "Exec =")
            missing = [field for field in required if field not in hook_text]
            if missing:
                err(f"hook {hook.relative_to(directory)} incompleto; faltan: {', '.join(missing)}")
            else:
                ok(f"estructura básica del hook {hook.relative_to(directory)}")
    return errors, warnings


def validate_selected(packages: dict[str, Package], selected: list[str]) -> None:
    errors = warnings = 0
    print(f"Validando {len(selected)} paquete(s)...")
    for name in selected:
        print(f"\n==> {name}")
        package_errors, package_warnings = validate_one(packages[name])
        errors += package_errors
        warnings += package_warnings
        for raw_dependency in packages[name].dependencies:
            dependency = dependency_name(raw_dependency)
            if dependency and dependency.startswith("cambonos-") and dependency not in packages:
                errors += 1
                print(f"  ERROR: dependencia interna sin paquete correspondiente: {dependency}")
    # Detect dependency cycles in the repository, even when only one package is selected.
    graph = {
        name: {dep for raw in pkg.dependencies if (dep := dependency_name(raw)) in packages}
        for name, pkg in packages.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str, chain: list[str]) -> None:
        nonlocal errors
        if name in visiting:
            start = chain.index(name) if name in chain else 0
            errors += 1
            print("ERROR: ciclo de dependencias internas: " + " -> ".join(chain[start:] + [name]))
            return
        if name in visited:
            return
        visiting.add(name)
        for dependency in sorted(graph[name]):
            visit(dependency, chain + [name])
        visiting.remove(name)
        visited.add(name)

    for name in sorted(packages):
        visit(name, [])
    print(f"\nResultado: {len(selected)} paquete(s) revisado(s), {errors} error(es), {warnings} aviso(s).")
    if errors:
        raise CambonosError("la validación estática ha encontrado errores")
    print("Validación estática completada correctamente.")


def select_packages(packages: dict[str, Package], requested: list[str] | None) -> list[str]:
    if not requested:
        return sorted(packages)
    unknown = sorted(set(requested) - packages.keys())
    if unknown:
        raise CambonosError("paquetes desconocidos: " + ", ".join(unknown))
    # Preserve user order while avoiding duplicate builds.
    return list(dict.fromkeys(requested))


def detect_arch(override: str | None) -> str:
    if override:
        arch = override
    else:
        arch = ""
        if shutil.which("pacman-conf"):
            proc = subprocess.run(["pacman-conf", "Architecture"], text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if proc.returncode == 0:
                arch = proc.stdout.splitlines()[0].strip() if proc.stdout.splitlines() else ""
        if not arch or arch == "auto":
            arch = os.uname().machine
    if not ARCH_RE.fullmatch(arch):
        raise CambonosError(f"arquitectura no válida: {arch!r}")
    return arch


def acquire_lock() -> int:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = DIST_DIR / ".cambonos-repository.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        os.close(fd)
        raise CambonosError("ya existe otro proceso construyendo o publicando CambonOS") from exc
    return fd


def makepkg_config(work_dir: Path, package_name: str) -> Path:
    base_config = Path("/etc/makepkg.conf")
    if not base_config.is_file():
        raise CambonosError("no existe /etc/makepkg.conf; ¿estás ejecutando esto en Arch Linux?")
    config = work_dir / f"makepkg-{package_name}.conf"
    build_dir = work_dir / "build" / package_name
    artifact_dir = work_dir / "artifacts" / package_name
    build_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    config.write_text(
        f'source {shlex.quote(str(base_config))}\n'
        f'BUILDDIR={shlex.quote(str(build_dir))}\n'
        f'PKGDEST={shlex.quote(str(artifact_dir))}\n',
        encoding="utf-8",
    )
    return config


def package_archive_name(path: Path) -> str:
    proc = subprocess.run(["pacman", "-Qqp", str(path)], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise CambonosError(f"pacman no puede leer la metadata de {path.name}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def build_packages(packages: dict[str, Package], selected: list[str], work_dir: Path,
                   arch: str, dry_run: bool) -> list[BuildArtifact]:
    if dry_run:
        info("DRY-RUN: construcción planificada; no se ejecutará makepkg")
        for name in selected:
            print(f"  Construiría: {name} ({packages[name].pkgver}-{packages[name].pkgrel})")
        return []
    require_commands("makepkg", "pacman", "bash")
    artifacts: list[BuildArtifact] = []
    for name in selected:
        package = packages[name]
        info(f"Construyendo {name} para {arch}")
        config = makepkg_config(work_dir, name)
        artifact_dir = work_dir / "artifacts" / name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        run(["makepkg", "--config", str(config), "--nodeps", "--cleanbuild",
             "--clean", "--force", "--noconfirm"], cwd=package.directory)
        package_artifacts = sorted(
            p for p in artifact_dir.glob("*.pkg.tar.*")
            if p.is_file() and not p.name.endswith(".sig")
        )
        if not package_artifacts:
            raise CambonosError(f"makepkg no generó ningún paquete para {name}")
        for artifact in package_artifacts:
            actual_name = package_archive_name(artifact)
            if actual_name != name:
                raise CambonosError(f"{name} generó un paquete inesperado: {actual_name} ({artifact.name})")
            print(f"  Preparado: {artifact.name}")
            artifacts.append(BuildArtifact(artifact, actual_name))
    return artifacts


def store_build_artifacts(artifacts: list[BuildArtifact], selected: list[str], arch: str) -> Path:
    """Persist build-only output without touching testing/stable repositories."""
    output = DIST_DIR / "build" / arch
    output.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = acquire_lock()
    try:
        with tempfile.TemporaryDirectory(prefix=f".{arch}.build-output.", dir=output.parent) as temp_name:
            temp_root = Path(temp_name)
            staged = temp_root / "output"
            backup = temp_root / "previous"
            if output.is_dir():
                shutil.copytree(output, staged, symlinks=True)
            else:
                staged.mkdir()
            existing = list_repository_packages(staged)
            for package_name in set(selected):
                for old_archive in existing.get(package_name, []):
                    old_archive.unlink(missing_ok=True)
                    Path(str(old_archive) + ".sig").unlink(missing_ok=True)
            for artifact in artifacts:
                destination = staged / artifact.path.name
                shutil.copy2(artifact.path, destination)
                signature = Path(str(artifact.path) + ".sig")
                if signature.is_file():
                    shutil.copy2(signature, Path(str(destination) + ".sig"))
            had_previous = output.exists()
            try:
                if had_previous:
                    os.replace(output, backup)
                os.replace(staged, output)
            except OSError:
                if had_previous and backup.exists() and not output.exists():
                    os.replace(backup, output)
                raise
    finally:
        os.close(lock_fd)
    return output


def list_repository_packages(repository: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    if not repository.exists():
        return result
    for archive in sorted(repository.glob("*.pkg.tar.*")):
        if archive.name.endswith(".sig") or not archive.is_file():
            continue
        name = package_archive_name(archive)
        result.setdefault(name, []).append(archive)
    return result


def verify_internal_dependencies(packages: dict[str, Package], selected: list[str],
                                 available_names: set[str]) -> None:
    for name in selected:
        for raw in packages[name].dependencies:
            dependency = dependency_name(raw)
            if dependency and dependency.startswith("cambonos-") and dependency not in available_names:
                raise CambonosError(
                    f"no se puede publicar {name}: {dependency} no está presente en el canal; "
                    "publica primero la dependencia o utiliza la publicación completa"
                )


def repository_database_name(channel: str) -> str:
    """Return the database basename pacman expects for this repository section."""
    return "cambonos-testing" if channel == "testing" else "cambonos"


def regenerate_database(repository: Path, database_dir: Path,
                        database_name: str) -> tuple[int, list[str]]:
    require_commands("repo-add", "pacman")
    grouped = list_repository_packages(repository)
    archives = sorted(path for paths in grouped.values() for path in paths)
    if not archives:
        raise CambonosError(f"no hay paquetes válidos para indexar en {repository}")
    database_dir.mkdir(parents=True, exist_ok=True)
    staged_db = database_dir / f"{database_name}.db.tar.gz"
    run(["repo-add", str(staged_db), *map(str, archives)])
    # repo-add creates .db/.files aliases (usually symlinks). Materialize them
    # as regular files, which is friendlier to static hosting such as Pages.
    for alias, target in ((f"{database_name}.db", f"{database_name}.db.tar.gz"),
                          (f"{database_name}.files", f"{database_name}.files.tar.gz")):
        target_path = database_dir / target
        alias_path = database_dir / alias
        if not target_path.is_file():
            raise CambonosError(f"repo-add no generó {target}")
        alias_path.unlink(missing_ok=True)
        shutil.copy2(target_path, alias_path)
    required_files = (
        f"{database_name}.db.tar.gz", f"{database_name}.db",
        f"{database_name}.files.tar.gz", f"{database_name}.files",
    )
    for required in required_files:
        if not (database_dir / required).is_file():
            raise CambonosError(f"no se generó el archivo de base de datos esperado: {required}")
    return len(archives), sorted(grouped)


def publish(packages: dict[str, Package], selected: list[str], artifacts: list[BuildArtifact],
            channel: str, arch: str, dry_run: bool) -> None:
    if channel not in {"testing", "stable"}:
        raise CambonosError("el canal debe ser 'testing' o 'stable'")
    live_repository = DIST_DIR / channel / arch
    database_name = repository_database_name(channel)
    info(f"Publicación en {channel}/{arch}")
    if dry_run:
        print(f"  Repositorio destino: {live_repository.relative_to(ROOT)}")
        for name in selected:
            print(f"  Reemplazaría/publicaría: {name}")
        print("  Conservaría los demás paquetes del canal.")
        print(f"  Regeneraría {database_name}.db, {database_name}.db.tar.gz, "
              f"{database_name}.files y {database_name}.files.tar.gz.")
        print("  Retiraría los paquetes obsoletos declarados: " + ", ".join(sorted(OBSOLETE_PACKAGES)))
        print("  No se ha modificado ningún archivo.")
        return

    if not artifacts:
        raise CambonosError("no hay artefactos construidos para publicar")
    require_commands("pacman", "repo-add")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    lock_fd = acquire_lock()
    try:
        live_repository.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f".{arch}.publish.", dir=live_repository.parent) as temp_name:
            temp_root = Path(temp_name)
            staged_repository = temp_root / "repository"
            staged_database = temp_root / "database"
            backup_repository = temp_root / "previous"
            if live_repository.is_dir():
                shutil.copytree(live_repository, staged_repository, symlinks=True)
            else:
                staged_repository.mkdir()

            existing = list_repository_packages(staged_repository)
            available_after = set(existing) | {artifact.package_name for artifact in artifacts}
            available_after -= OBSOLETE_PACKAGES
            verify_internal_dependencies(packages, selected, available_after)

            replace_names = set(selected) | OBSOLETE_PACKAGES
            for package_name in replace_names:
                for old_archive in existing.get(package_name, []):
                    old_archive.unlink(missing_ok=True)
                    old_archive.with_name(old_archive.name + ".sig").unlink(missing_ok=True)
                    # Signature naming convention is archive.pkg.tar.zst.sig.
                    Path(str(old_archive) + ".sig").unlink(missing_ok=True)

            for artifact in artifacts:
                destination = staged_repository / artifact.path.name
                shutil.copy2(artifact.path, destination)
                signature = Path(str(artifact.path) + ".sig")
                if signature.is_file():
                    shutil.copy2(signature, Path(str(destination) + ".sig"))

            count, names = regenerate_database(staged_repository, staged_database, database_name)
            database_files = (
                f"{database_name}.db.tar.gz", f"{database_name}.db",
                f"{database_name}.files.tar.gz", f"{database_name}.files",
            )
            for database_file in database_files:
                destination = staged_repository / database_file
                destination.unlink(missing_ok=True)
                shutil.copy2(staged_database / database_file, destination)

            # Remove database names from the previous convention/channel so
            # pacman and static hosting cannot encounter stale indexes.
            other_database_name = "cambonos" if database_name == "cambonos-testing" else "cambonos-testing"
            stale_files = (
                f"{other_database_name}.db.tar.gz", f"{other_database_name}.db",
                f"{other_database_name}.files.tar.gz", f"{other_database_name}.files",
            )
            for stale_file in stale_files:
                (staged_repository / stale_file).unlink(missing_ok=True)

            # Database signatures cannot be retained when the database content changes.
            for signature in (
                f"{database_name}.db.tar.gz.sig", f"{database_name}.files.tar.gz.sig",
                f"{database_name}.db.sig", f"{database_name}.files.sig",
                f"{other_database_name}.db.tar.gz.sig", f"{other_database_name}.files.tar.gz.sig",
                f"{other_database_name}.db.sig", f"{other_database_name}.files.sig",
            ):
                (staged_repository / signature).unlink(missing_ok=True)

            # Replace the complete architecture directory with rollback on error.
            had_previous = live_repository.exists()
            try:
                if had_previous:
                    os.replace(live_repository, backup_repository)
                os.replace(staged_repository, live_repository)
            except OSError:
                if had_previous and backup_repository.exists() and not live_repository.exists():
                    os.replace(backup_repository, live_repository)
                raise
            print(f"\nRepositorio {channel}/{arch} actualizado correctamente.")
            print(f"Paquetes indexados: {count}")
            print("Paquetes presentes: " + (", ".join(names) if names else "ninguno"))
    finally:
        os.close(lock_fd)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cambonos",
        description="Valida, construye y publica los paquetes del repositorio CambonOS.",
        epilog="Ejemplos: cambonos validate; cambonos build -p cambonos-release; "
               "cambonos publish --channel testing --dry-run",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("validate", "build", "publish"):
        sub = subparsers.add_parser(action, help={
            "validate": "validar paquetes sin modificarlos",
            "build": "validar y construir paquetes",
            "publish": "validar, construir y publicar paquetes",
        }[action])
        sub.add_argument("-p", "--package", action="append", dest="packages", metavar="NAME",
                         help="paquete a procesar; se puede repetir. Por defecto, todos.")
        if action != "validate":
            sub.add_argument("--arch", help="arquitectura destino (por defecto, detección automática)")
        sub.add_argument("--dry-run", action="store_true",
                         help="mostrar el plan sin construir ni modificar el repositorio")
        if action == "publish":
            sub.add_argument("--channel", required=True, choices=("testing", "stable"),
                             help="canal que recibirá los paquetes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        packages = discover_packages()
        selected = select_packages(packages, args.packages)
        if args.action == "validate":
            validate_selected(packages, selected)
            if args.dry_run:
                print("DRY-RUN: validación ejecutada; no se han realizado modificaciones.")
            return 0

        validate_selected(packages, selected)
        arch = detect_arch(args.arch)
        if args.action == "build":
            print(f"\nPlan: validar y construir {len(selected)} paquete(s) para {arch}.")
        else:
            print(f"\nPlan: validar, construir y publicar {len(selected)} paquete(s) en {args.channel}/{arch}.")
        if args.dry_run:
            build_packages(packages, selected, Path(tempfile.gettempdir()) / "cambonos-dry-run", arch, True)
            if args.action == "publish":
                publish(packages, selected, [], args.channel, arch, True)
            return 0

        if os.geteuid() == 0:
            raise CambonosError("no ejecutes makepkg como root; utiliza un usuario normal")
        with tempfile.TemporaryDirectory(prefix="cambonos-build-") as work_name:
            artifacts = build_packages(packages, selected, Path(work_name), arch, False)
            if args.action == "build":
                output = store_build_artifacts(artifacts, selected, arch)
                print(f"\nConstrucción completada: {len(artifacts)} artefacto(s).")
                print(f"Artefactos guardados en: {output.relative_to(ROOT)}")
            else:
                publish(packages, selected, artifacts, args.channel, arch, False)
        return 0
    except (CambonosError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
