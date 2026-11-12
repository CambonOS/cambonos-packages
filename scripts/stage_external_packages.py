#!/usr/bin/env python3
"""Stage separately maintained package sources at verified Git commits."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cambonos_lib.common import CambonosError
from cambonos_lib.validation import extract_scalar


EXTERNAL_PACKAGES = {
    "cambonos-installer": "https://github.com/CambonOS/cambonos-installer.git",
    "cambonos-mkiso": "https://github.com/CambonOS/cambonos-mkiso.git",
}


def _git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise CambonosError(f"falló git en {source}: {result.stderr.strip()}")
    return result.stdout.strip()


def _validate_symlinks(source: Path) -> None:
    airootfs = source / "files/profile/airootfs"
    for path in source.rglob("*"):
        if not path.is_symlink():
            continue
        if path.is_relative_to(airootfs):
            target = path.readlink()
            if target.is_absolute():
                continue
            relative_target = path.parent.relative_to(airootfs) / target
            normalized_target = Path(os.path.normpath(str(relative_target)))
            if ".." in normalized_target.parts:
                raise CambonosError(
                    f"symlink externo que escapa de airootfs: {path.relative_to(source)}"
                )
        elif not path.resolve().is_relative_to(source):
            raise CambonosError(
                f"symlink externo que escapa del checkout: {path.relative_to(source)}"
            )


def stage_external_package(
    source_root: Path,
    package_name: str,
    source_dir: Path,
    expected_commit: str,
) -> Path:
    """Copy one clean external checkout into the temporary package source tree."""
    expected_url = EXTERNAL_PACKAGES.get(package_name)
    if not expected_url:
        raise CambonosError(f"paquete externo no permitido: {package_name}")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", expected_commit):
        raise CambonosError(f"commit externo no válido para {package_name}")

    source = source_dir.resolve()
    if not source.is_dir():
        raise CambonosError(f"no existe el checkout externo: {source}")
    actual_url = _git(source, "remote", "get-url", "origin").removesuffix(".git")
    if actual_url != expected_url.removesuffix(".git"):
        raise CambonosError(f"origen Git incorrecto para {package_name}: {actual_url}")
    actual_commit = _git(source, "rev-parse", "HEAD")
    if actual_commit != expected_commit:
        raise CambonosError(
            f"checkout externo incorrecto para {package_name}: "
            f"se esperaba {expected_commit}, se encontró {actual_commit}"
        )
    if _git(source, "status", "--porcelain", "--untracked-files=all"):
        raise CambonosError(f"el checkout externo contiene cambios: {package_name}")
    _validate_symlinks(source)

    pkgb = source / "PKGBUILD"
    if not pkgb.is_file() or extract_scalar(pkgb.read_text(encoding="utf-8"), "pkgname") != package_name:
        raise CambonosError(f"{source}/PKGBUILD no declara pkgname={package_name}")

    package_parent = source_root / "packages"
    package_parent.mkdir(parents=True, exist_ok=True)
    destination = package_parent / package_name
    if destination.exists() or destination.is_symlink():
        raise CambonosError(f"ya existe el destino del paquete externo: {destination}")

    # Package provenance tracks the last commit that changed effective build
    # inputs, not the branch tip. README, tests and workflow-only commits must
    # not invalidate the package fingerprint or trigger a rebuild.
    build_input_paths = ["PKGBUILD", "LICENSE", "*.install", "files/"]
    for raw_reference in re.findall(
        r"\$startdir/([^\s\"']+)", pkgb.read_text(encoding="utf-8")
    ):
        relative = Path(raw_reference.rstrip("\\"))
        if relative.is_absolute() or ".." in relative.parts:
            raise CambonosError(
                f"referencia insegura en PKGBUILD externo de {package_name}: {raw_reference}"
            )
        if relative.parts and relative.parts[0] != "files":
            build_input_paths.append(relative.as_posix())
    input_commit = _git(
        source,
        "log",
        "-1",
        "--format=%H",
        expected_commit,
        "--",
        *sorted(set(build_input_paths)),
    )
    if not re.fullmatch(r"[0-9a-f]{40}", input_commit):
        raise CambonosError(f"no se pudo resolver el último commit de entradas de {package_name}")
    source_date_epoch = _git(source, "show", "-s", "--format=%ct", input_commit)
    if not source_date_epoch.isdigit():
        raise CambonosError(f"fecha de commit inválida para {package_name}")
    try:
        shutil.copytree(
            source,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )
        metadata = {
            "repository": expected_url.removesuffix(".git"),
            "commit": input_commit,
            "source_date_epoch": int(source_date_epoch),
        }
        (destination / ".cambonos-source.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--installer-source", type=Path, required=True)
    parser.add_argument("--installer-commit", required=True)
    parser.add_argument("--mkiso-source", type=Path, required=True)
    parser.add_argument("--mkiso-commit", required=True)
    args = parser.parse_args(argv)
    try:
        for package_name, source, commit in (
            ("cambonos-installer", args.installer_source, args.installer_commit),
            ("cambonos-mkiso", args.mkiso_source, args.mkiso_commit),
        ):
            staged = stage_external_package(
                args.source_root.resolve(), package_name, source, commit
            )
            print(f"Staged {package_name} from {commit}: {staged}")
    except CambonosError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())