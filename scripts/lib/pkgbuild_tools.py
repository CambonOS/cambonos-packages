#!/usr/bin/env python3
"""Static validation helpers for the CambonOS package monorepo.

The repository keeps local package payloads under each package's files/ tree.
PKGBUILDs install them directly from $startdir/files; no source=() or
sha256sums=() arrays are needed for these repository-local files.
"""
from __future__ import annotations

import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Payload:
    source_path: Path
    destination: str


def extract_scalar(text: str, name: str) -> Optional[str]:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*([^\n#]+)", text)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def extract_array(text: str, name: str) -> list[str]:
    """Read a simple static Bash array without evaluating the PKGBUILD."""
    match = re.search(rf"(?ms)^\s*{re.escape(name)}\s*=\s*\((.*?)\)", text)
    if not match:
        return []
    body = re.sub(r"(?m)#.*$", "", match.group(1))
    try:
        return shlex.split(body, comments=False, posix=True)
    except ValueError as exc:
        raise ValueError(f"no se pudo interpretar el array {name}: {exc}") from exc


def extract_function(text: str, name: str) -> Optional[str]:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*\(\s*\)\s*\{{", text)
    if not match:
        return None
    start, depth, quote, escaped, comment = match.end(), 1, None, False, False
    i = start
    while i < len(text):
        ch = text[i]
        if comment:
            if ch == "\n":
                comment = False
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\" and quote != "'":
                escaped = True
            elif ch == quote:
                quote = None
        else:
            if ch in ("'", '"', '`'):
                quote = ch
            elif ch == "#":
                comment = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i]
        i += 1
    raise ValueError(f"no se pudo localizar el cierre de {name}()")


def run_bash_n(path: Path) -> tuple[bool, str]:
    proc = subprocess.run(["bash", "-n", str(path)], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0, proc.stderr.strip()


def parse_direct_payloads(body: str, package_dir: Path) -> list[Payload]:
    """Find install -D... $startdir/files/... $pkgdir/... pairs.

    The accepted form is deliberately literal and auditable. Dynamic source
    paths are reported as unsupported rather than guessed by the validator.
    """
    payloads: list[Payload] = []
    body = re.sub(r"\\\s*\n", " ", body)
    pattern = re.compile(
        r'''\binstall\s+-D(?:[A-Za-z0-9]+)?\s+(["']?)\$startdir/files/([^"'\s]+)\1\s+(["']?)\$pkgdir(/[^"'\s]+)\3'''
    )
    for match in pattern.finditer(body):
        relative = match.group(2)
        destination = match.group(4)
        source_path = (package_dir / "files" / relative).resolve()
        files_root = (package_dir / "files").resolve()
        if not source_path.is_relative_to(files_root):
            raise ValueError(f"la fuente sale de files/: {relative!r}")
        payloads.append(Payload(source_path, destination))
    return payloads


def validate_package(package_dir: Path) -> tuple[int, int, set[str]]:
    errors = warnings = 0

    def err(msg: str) -> None:
        nonlocal errors
        errors += 1
        print(f"  ERROR: {msg}")

    def warn(msg: str) -> None:
        nonlocal warnings
        warnings += 1
        print(f"  AVISO: {msg}")

    def ok(msg: str) -> None:
        print(f"  OK: {msg}")

    pkgb = package_dir / "PKGBUILD"
    if not pkgb.is_file():
        err("falta PKGBUILD")
        return errors, warnings, set()

    text = pkgb.read_text(encoding="utf-8")
    syntax_ok, syntax_msg = run_bash_n(pkgb)
    if syntax_ok:
        ok("sintaxis Bash de PKGBUILD")
    else:
        err(f"sintaxis Bash incorrecta: {syntax_msg}")
        return errors, warnings, set()

    pkgname, pkgver, pkgrel = (extract_scalar(text, key) for key in ("pkgname", "pkgver", "pkgrel"))
    if not pkgname or pkgname != package_dir.name:
        err(f"pkgname ({pkgname!r}) no coincide con el directorio ({package_dir.name})")
    if not pkgver or not pkgrel:
        err("faltan pkgver o pkgrel")
    if pkgname and pkgver and pkgrel and pkgname == package_dir.name:
        ok(f"metadatos: {pkgname} {pkgver}-{pkgrel}")

    try:
        depends = extract_array(text, "depends")
    except ValueError as exc:
        err(str(exc))
        depends = []

    # For this repository design, source arrays would reintroduce makepkg's
    # local source staging/copying behavior and are therefore rejected.
    if re.search(r"(?m)^\s*(?:source|sha256sums)\s*=\s*\(", text):
        err("este repositorio instala payloads directamente desde files/: elimina source=() y sha256sums=()")

    try:
        body = extract_function(text, "package")
        if body is None:
            raise ValueError("no se encuentra la función package()")

        # Check that source references are static and rooted in $startdir/files.
        references = re.findall(r"\$startdir/files/([^\s\"']+)", body)
        dynamic_refs = re.findall(r"\$startdir/files/(?:\$|\{)", body)
        if dynamic_refs:
            warn("package() contiene rutas dinámicas bajo files/; requieren revisión manual")

        payloads = parse_direct_payloads(body, package_dir)
        parsed_sources = {payload.source_path for payload in payloads}
        referenced_sources = {
            (package_dir / "files" / item.rstrip('\\')).resolve()
            for item in references
        }
        if referenced_sources - parsed_sources:
            warn("hay referencias a files/ que no se reconocen como origen directo de install -D")

        for payload in payloads:
            if not payload.source_path.is_file():
                err(f"no existe el archivo fuente: {payload.source_path.relative_to(package_dir)}")

        if references and len(payloads) != len(references):
            warn(f"se detectaron {len(references)} referencia(s) a files/ y {len(payloads)} instalación(es) estática(s); revisar package()")
        elif payloads:
            ok(f"{len(payloads)} archivo(s) fuente(s) de files/ comprobados; sin staging de source")
        else:
            warn("no se detectaron instalaciones directas desde files/")

        dests = [payload.destination for payload in payloads]
        for dest in dests:
            if "/../" in dest or dest.endswith("/.."):
                err(f"destino inseguro con '..': {dest}")
            elif not dest.startswith(("/usr/", "/etc/", "/opt/", "/var/", "/boot/", "/lib/", "/bin/", "/sbin/")):
                err(f"destino $pkgdir fuera de rutas habituales: {dest}")
        sensitive = [d for d in dests if d.startswith(("/usr/lib/os-release", "/etc/arch-release", "/etc/xdg/fastfetch", "/etc/fastfetch"))]
        if sensitive:
            warn("revisar destinos que podrían sobrescribir archivos/configuración oficial: " + ", ".join(sensitive))
        if dests:
            ok(f"{len(dests)} destino(s) $pkgdir revisados")

        # Warn about unsupported source-dir use, which is no longer expected.
        if re.search(r"\$(?:\{srcdir\}|srcdir)(?:/|\})", body):
            err("package() todavía utiliza $srcdir; debe leer los payloads desde $startdir/files")
    except Exception as exc:
        err(str(exc))

    install_name = extract_scalar(text, "install")
    if install_name:
        install_path = (package_dir / install_name).resolve()
        if not install_path.is_relative_to(package_dir.resolve()) or not install_path.is_file():
            err(f"install={install_name!r} no existe o sale del directorio del paquete")
        else:
            good, message = run_bash_n(install_path)
            if good:
                ok(f"sintaxis Bash de {install_name}")
            else:
                err(f"sintaxis Bash incorrecta en {install_name}: {message}")
    else:
        ok("sin script install asociado")

    files_dir = package_dir / "files"
    if files_dir.is_dir():
        for script in sorted(p for p in files_dir.rglob("*") if p.is_file()):
            try:
                first_line = script.open("r", encoding="utf-8").readline().strip()
            except UnicodeDecodeError:
                continue
            if "bash" in first_line and first_line.startswith("#!"):
                good, message = run_bash_n(script)
                if good:
                    ok(f"sintaxis Bash de {script.relative_to(package_dir)}")
                else:
                    err(f"sintaxis Bash incorrecta en {script.relative_to(package_dir)}: {message}")

        for hook in sorted(files_dir.rglob("*.hook")):
            hook_text = hook.read_text(encoding="utf-8")
            required = ("[Trigger]", "[Action]", "Operation =", "Type =", "Target =", "When =", "Exec =")
            missing = [field for field in required if field not in hook_text]
            if missing:
                err(f"hook {hook.relative_to(package_dir)} incompleto; faltan: {', '.join(missing)}")
            else:
                ok(f"estructura básica del hook {hook.relative_to(package_dir)}")

    return errors, warnings, {
        re.match(r"^([A-Za-z0-9@._+:-]+)", dependency).group(1).split(":", 1)[0]
        for dependency in depends
        if re.match(r"^([A-Za-z0-9@._+:-]+)", dependency)
    }


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "validate":
        print("Uso: pkgbuild_tools.py validate <packages-dir>", file=sys.stderr)
        return 2
    packages_dir = Path(sys.argv[2]).resolve()
    if not packages_dir.is_dir():
        print(f"ERROR: no existe el directorio {packages_dir}", file=sys.stderr)
        return 1

    package_dirs = sorted(p for p in packages_dir.iterdir() if p.is_dir() and (p / "PKGBUILD").is_file())
    if not package_dirs:
        print(f"ERROR: no se encontraron PKGBUILD en {packages_dir}", file=sys.stderr)
        return 1

    package_names = {package.name for package in package_dirs}
    dependency_graph: dict[str, set[str]] = {}
    total_errors = total_warnings = checked = 0
    print(f"Validando {len(package_dirs)} paquete(s)...")

    for package in package_dirs:
        checked += 1
        print(f"\n==> {package.name}")
        errors, warnings, dependencies = validate_package(package)
        total_errors += errors
        total_warnings += warnings
        internal = dependencies & package_names
        dependency_graph[package.name] = internal
        missing_internal = sorted(dep for dep in dependencies if dep.startswith("cambonos-") and dep not in package_names)
        if missing_internal:
            total_errors += 1
            print("  ERROR: dependencias internas sin paquete correspondiente: " + ", ".join(missing_internal))
        if internal:
            print("  OK: dependencias internas: " + ", ".join(sorted(internal)))

    # Detect cycles among packages in this monorepo. Runtime dependency edges
    # are useful metadata, but cycles make installation and future packaging fragile.
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[str] = []

    def visit(name: str, chain: list[str]) -> None:
        if name in visiting:
            cycle_start = chain.index(name) if name in chain else 0
            cycles.append(" -> ".join(chain[cycle_start:] + [name]))
            return
        if name in visited:
            return
        visiting.add(name)
        for dependency in sorted(dependency_graph.get(name, set())):
            visit(dependency, chain + [name])
        visiting.remove(name)
        visited.add(name)

    for name in sorted(dependency_graph):
        visit(name, [])
    for cycle in cycles:
        total_errors += 1
        print(f"ERROR: ciclo de dependencias internas: {cycle}")

    print(f"\nResultado: {checked} paquete(s) revisado(s), {total_errors} error(es), {total_warnings} aviso(s).")
    if total_errors:
        print("Validación estática finalizada con errores.")
        return 1
    print("Validación estática completada correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
