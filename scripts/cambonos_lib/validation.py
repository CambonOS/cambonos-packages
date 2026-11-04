"""Static package validation. PKGBUILDs are not sourced on the host."""
from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path

from .common import CambonosError
from .config import ARCHITECTURE, REQUIRED_PACKAGES
from .models import Package


NAME_RE = re.compile(r"^[A-Za-z0-9@._+:-]+$")
def extract_scalar(text: str, name: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*([^\n#]+)", text)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\\\"'":
        value = value[1:-1]
    return value


def extract_array(text: str, name: str) -> list[str]:
    match = re.search(rf"(?ms)^\s*{re.escape(name)}\s*=\s*\((.*?)\)", text)
    if not match:
        return []
    body = re.sub(r"(?m)#.*$", "", match.group(1))
    try:
        return shlex.split(body, comments=False, posix=True)
    except ValueError as exc:
        raise CambonosError(f"no se pudo interpretar el array {name}: {exc}") from exc


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
            elif char == "\\\\" and quote != "'":
                escaped = True
            elif char == quote:
                quote = None
        else:
            if char in ("'", '"', "`"):
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
    result = subprocess.run(
        ["bash", "-n", str(path)], text=True, capture_output=True, check=False
    )
    return result.returncode == 0, result.stderr.strip()


def dependency_name(value: str) -> str | None:
    match = re.match(r"^([A-Za-z0-9@._+:-]+)", value)
    if not match:
        return None
    return match.group(1).split(":", 1)[0]


def discover_packages(source_root: Path) -> dict[str, Package]:
    package_root = source_root / "packages"
    if not package_root.is_dir():
        raise CambonosError(f"no existe el directorio {package_root}")
    packages: dict[str, Package] = {}
    for directory in sorted(p for p in package_root.iterdir() if p.is_dir()):
        if directory.is_symlink():
            raise CambonosError(f"los directorios de paquetes no pueden ser symlinks: {directory}")
        pkgb = directory / "PKGBUILD"
        if not pkgb.is_file() or pkgb.is_symlink():
            raise CambonosError(f"falta PKGBUILD regular en el directorio {directory.name}")
        text = pkgb.read_text(encoding="utf-8")
        name = extract_scalar(text, "pkgname") or ""
        if not name:
            raise CambonosError(f"{pkgb}: pkgname debe ser un valor escalar estático")
        if name != directory.name:
            raise CambonosError(f"{pkgb}: pkgname={name!r} no coincide con {directory.name!r}")
        if name in packages:
            raise CambonosError(f"nombre de paquete duplicado: {name}")
        pkgver = extract_scalar(text, "pkgver") or ""
        pkgrel = extract_scalar(text, "pkgrel") or ""
        epoch = extract_scalar(text, "epoch") or "0"
        arch = tuple(extract_array(text, "arch"))
        depends = tuple(extract_array(text, "depends"))
        makedepends = tuple(extract_array(text, "makedepends"))
        checkdepends = tuple(extract_array(text, "checkdepends"))
        optdepends = tuple(extract_array(text, "optdepends"))
        install_script = extract_scalar(text, "install")
        packages[name] = Package(
            name=name, directory=directory, pkgver=pkgver, pkgrel=pkgrel,
            epoch=epoch, architecture=arch, depends=depends,
            makedepends=makedepends, checkdepends=checkdepends,
            optdepends=optdepends, install_script=install_script,
        )
    if not packages:
        raise CambonosError(f"no se encontraron PKGBUILD en {package_root}")
    missing_required = REQUIRED_PACKAGES - packages.keys()
    if missing_required:
        raise CambonosError("faltan paquetes obligatorios: " + ", ".join(sorted(missing_required)))
    return packages


def validate_package(package: Package) -> list[str]:
    errors: list[str] = []
    directory = package.directory
    pkgb = directory / "PKGBUILD"
    text = pkgb.read_text(encoding="utf-8")
    good, message = bash_syntax(pkgb)
    if not good:
        errors.append(f"sintaxis Bash incorrecta en PKGBUILD: {message}")
        return errors
    if not package.pkgver or not package.pkgrel:
        errors.append("faltan pkgver o pkgrel")
    if "$" in package.pkgver or "$" in package.pkgrel or "$" in package.epoch:
        errors.append("pkgver, pkgrel y epoch deben ser valores estáticos")
    if not package.epoch.isdigit():
        errors.append("epoch debe ser un entero no negativo")
    if not NAME_RE.fullmatch(package.name):
        errors.append(f"nombre de paquete no válido: {package.name}")
    if not package.architecture or not set(package.architecture).intersection({ARCHITECTURE, "any"}):
        errors.append(f"arch debe incluir {ARCHITECTURE} o any")
    if re.search(r"(?m)^\s*(?:source|sha256sums)\s*=\s*\(", text):
        errors.append("este repositorio utiliza payloads locales en files/: no declarar source=() ni sha256sums=()")
    for array_name in ("depends", "makedepends", "checkdepends", "arch"):
        array_match = re.search(
            rf"(?ms)^\s*{array_name}\s*=\s*\((.*?)\)", text
        )
        scalar_match = re.search(rf"(?m)^\s*{array_name}\s*=\s*([^\n]+)", text)
        value = array_match.group(1) if array_match else (scalar_match.group(1) if scalar_match else "")
        if "$" in value:
            errors.append(f"{array_name} debe ser estático para permitir validación anticipada")
    body = extract_function(text, "package")
    if body is None:
        errors.append("no se encuentra package()")
        return errors
    refs = re.findall(r"""\$startdir/files/([^\s"']+)""", body)
    if re.search(r"\$startdir/files/(?:\$|\{)", body):
        errors.append("package() contiene rutas dinámicas bajo files/; utiliza rutas estáticas")
    if re.search(r"\$\{?(?:srcdir)\}?", body):
        errors.append("package() debe leer los payloads locales desde $startdir/files")
    for raw in refs:
        source = (directory / "files" / raw.rstrip("\\")).resolve()
        files_root = (directory / "files").resolve()
        if not source.is_relative_to(files_root):
            errors.append(f"referencia fuera de files/: {raw}")
        elif not source.is_file():
            errors.append(f"no existe el archivo fuente: files/{raw}")
    destinations = re.findall(r"""\$pkgdir(/[^\s"']+)""", body)
    for destination in destinations:
        if "/../" in destination or destination.endswith("/.."):
            errors.append(f"destino inseguro con '..': {destination}")
        elif not destination.startswith(("/usr/", "/etc/", "/opt/", "/var/", "/boot/", "/lib/", "/bin/", "/sbin/")):
            errors.append(f"destino de instalación fuera de rutas permitidas: {destination}")
    install_script = package.install_script
    if install_script:
        install_path = (directory / install_script).resolve()
        if not install_path.is_relative_to(directory.resolve()) or not install_path.is_file():
            errors.append(f"install={install_script!r} no existe o sale del directorio")
        else:
            ok, message = bash_syntax(install_path)
            if not ok:
                errors.append(f"sintaxis incorrecta en {install_script}: {message}")
    for script in sorted((directory / "files").rglob("*")) if (directory / "files").exists() else []:
        if script.is_file():
            try:
                with script.open("r", encoding="utf-8") as stream:
                    first = stream.readline().strip()
            except UnicodeDecodeError:
                continue
            if first.startswith("#!") and "bash" in first:
                ok, message = bash_syntax(script)
                if not ok:
                    errors.append(f"sintaxis incorrecta en {script.relative_to(directory)}: {message}")
    for hook in sorted((directory / "files").rglob("*.hook")) if (directory / "files").exists() else []:
        hook_text = hook.read_text(encoding="utf-8")
        required = ("[Trigger]", "[Action]", "Operation =", "Type =", "Target =", "When =", "Exec =")
        missing = [field for field in required if field not in hook_text]
        if missing:
            errors.append(f"hook {hook.relative_to(directory)} incompleto: {', '.join(missing)}")
    if package.name == "cambonos-keyring":
        key_file = directory / "files" / "cambonos.gpg"
        trust_file = directory / "files" / "cambonos-trusted"
        revoked_file = directory / "files" / "cambonos-revoked"
        if not key_file.is_file() or key_file.stat().st_size == 0:
            errors.append("cambonos-keyring: falta files/cambonos.gpg; sigue docs/GPG-SETUP.md")
        elif not trust_file.is_file() or trust_file.stat().st_size == 0:
            errors.append("cambonos-keyring: falta files/cambonos-trusted; sigue docs/GPG-SETUP.md")
        elif not revoked_file.is_file():
            errors.append("cambonos-keyring: falta files/cambonos-revoked")
        else:
            import shutil
            if not shutil.which("gpg"):
                errors.append("se necesita gpg para validar el material de cambonos-keyring")
            else:
                result = subprocess.run(
                    ["gpg", "--batch", "--show-keys", "--with-colons",
                     "--with-subkey-fingerprint", str(key_file)],
                    text=True, capture_output=True, check=False,
                )
                if result.returncode:
                    errors.append("files/cambonos.gpg no contiene un certificado OpenPGP válido")
                else:
                    primary = None
                    signing_primaries = []
                    current_type = None
                    current_caps = ""
                    current_validity = ""
                    for line in result.stdout.splitlines():
                        fields = line.split(":")
                        if fields[0] in {"pub", "sub"}:
                            current_type = fields[0]
                            current_validity = fields[1] if len(fields) > 1 else ""
                            current_caps = fields[11] if len(fields) > 11 else ""
                            if current_type == "pub":
                                primary = None
                        elif fields[0] == "fpr" and len(fields) > 9:
                            fingerprint = fields[9].upper()
                            if current_type == "pub":
                                primary = (
                                    fingerprint if current_validity not in {"r", "e", "d"} else None
                                )
                            elif (
                                current_type == "sub" and "s" in current_caps
                                and current_validity not in {"r", "e", "d"} and primary
                            ):
                                signing_primaries.append(primary)
                    if not signing_primaries:
                        errors.append("cambonos.gpg debe incluir una subclave de firma")
                    elif not any(
                        re.search(rf"(?m)^{re.escape(fingerprint)}:6:",
                                  trust_file.read_text(errors="replace"))
                        for fingerprint in signing_primaries
                    ):
                        errors.append(
                            "cambonos-trusted debe marcar como ultimate (6) la clave primaria "
                            "de alguna subclave de firma"
                        )
    return errors


def validate_all(packages: dict[str, Package]) -> None:
    errors: list[str] = []
    for name, package in sorted(packages.items()):
        package_errors = validate_package(package)
        for message in package_errors:
            errors.append(f"{name}: {message}")
    for package in packages.values():
        for raw in package.depends + package.makedepends + package.checkdepends + package.optdepends:
            dep = dependency_name(raw)
            if dep and dep.startswith("cambonos-") and dep not in packages:
                errors.append(f"{package.name}: dependencia interna sin paquete: {dep}")
    build_graph = {}
    for name, package in packages.items():
        has_check = extract_function(
            (package.directory / "PKGBUILD").read_text(encoding="utf-8"), "check"
        ) is not None
        build_dependencies = package.makedepends + (package.checkdepends if has_check else ())
        build_graph[name] = {
            dep for raw in build_dependencies
            if (dep := dependency_name(raw)) in packages
        }
    visiting, visited = set(), set()
    def visit(name: str, chain: list[str]) -> None:
        if name in visiting:
            start = chain.index(name) if name in chain else 0
            errors.append("ciclo de dependencias internas de construcción: " +
                          " -> ".join(chain[start:] + [name]))
            return
        if name in visited:
            return
        visiting.add(name)
        for dependency in sorted(build_graph[name]):
            visit(dependency, chain + [name])
        visiting.remove(name)
        visited.add(name)
    for name in sorted(build_graph):
        visit(name, [])
    if errors:
        raise CambonosError("validación estática fallida:\n- " + "\n- ".join(errors))
    print(f"Validación estática correcta: {len(packages)} paquetes.")
