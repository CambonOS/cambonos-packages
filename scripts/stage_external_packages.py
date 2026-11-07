#!/usr/bin/env python3
"""Stage separately maintained package sources at verified Git commits."""
from __future__ import annotations

import argparse
import json
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
    "cambonos-installer": "https://github.com/CambonOS/installer.git",
    "cambonos-mkiso": "https://github.com/CambonOS/iso.git",
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
    for path in source.rglob("*"):
        if path.is_symlink() and not path.resolve().is_relative_to(source):
            raise CambonosError(f"symlink externo que escapa del checkout: {path.relative_to(source)}")

    pkgb = source / "PKGBUILD"
    if not pkgb.is_file() or extract_scalar(pkgb.read_text(encoding="utf-8"), "pkgname") != package_name:
        raise CambonosError(f"{source}/PKGBUILD no declara pkgname={package_name}")

    package_parent = source_root / "packages"
    package_parent.mkdir(parents=True, exist_ok=True)
    destination = package_parent / package_name
    if destination.exists() or destination.is_symlink():
        raise CambonosError(f"ya existe el destino del paquete externo: {destination}")

    source_date_epoch = _git(source, "show", "-s", "--format=%ct", expected_commit)
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
            "commit": expected_commit,
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