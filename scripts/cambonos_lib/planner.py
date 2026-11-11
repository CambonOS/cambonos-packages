"""Conservative, read-only build planning for CambonOS packages."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .build import build_order
from .common import CambonosError
from .config import ARCHITECTURE
from .models import Package
from .validation import dependency_name, extract_function


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_hash(value: object) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def package_input_hash(package: Package) -> str:
    """Hash build payload, deliberately excluding package-level documentation."""
    digest = hashlib.sha256()
    candidates = [package.directory / "PKGBUILD"]
    candidates.extend(sorted(package.directory.glob("*.install")))
    payload = package.directory / "files"
    if payload.is_dir():
        candidates.extend(sorted(p for p in payload.rglob("*") if p.is_file()))
    metadata = package.directory / ".cambonos-source.json"
    if metadata.is_file():
        candidates.append(metadata)
    for path in candidates:
        if path.is_symlink():
            raise CambonosError(f"{package.name}: symlink no permitido en entradas de build: {path}")
        relative = path.relative_to(package.directory).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _build_dependencies(package: Package) -> set[str]:
    text = (package.directory / "PKGBUILD").read_text(encoding="utf-8")
    has_check = extract_function(text, "check") is not None
    values = package.makedepends + (package.checkdepends if has_check else ())
    return {name for raw in values if (name := dependency_name(raw))}


def _channel_profile(package: Package, channel: str) -> str:
    if package.name != "cambonos-pacman":
        return _json_hash({"profile": "common"})
    return _json_hash({
        "profile": channel,
        "pacman_config": (package.directory / "files/cambonos.conf").read_text(encoding="utf-8"),
        "testing_overlay": channel == "testing",
    })


def create_build_plan(
    packages: dict[str, Package],
    channel: str,
    image: str,
    previous_manifest: dict | None = None,
) -> dict:
    """Plan only; this function never builds, signs, or publishes artifacts."""
    if channel not in {"testing", "stable"}:
        raise CambonosError(f"canal no válido: {channel}")
    ordered = build_order(packages)
    old_packages = {}
    if isinstance(previous_manifest, dict):
        channels = previous_manifest.get("channels")
        if isinstance(channels, dict):
            channel_record = channels.get(channel, {})
            old_packages = channel_record.get("packages", {}) if isinstance(channel_record, dict) else {}
        else:
            old_packages = previous_manifest.get("packages", {})
    if not isinstance(old_packages, dict):
        raise CambonosError("el manifiesto anterior no contiene un mapa de paquetes válido")

    recipe_files = ("build.py", "validation.py", "common.py", "planner.py")
    recipe_hash = _json_hash({
        name: _digest(Path(__file__).with_name(name).read_bytes())
        for name in recipe_files
    })
    fingerprints: dict[str, str] = {}
    records: dict[str, dict] = {}
    for name in ordered:
        package = packages[name]
        deps = sorted(_build_dependencies(package) & packages.keys())
        dependency_fingerprints = {dep: fingerprints[dep] for dep in deps}
        inputs_hash = package_input_hash(package)
        profile_hash = _channel_profile(package, channel)
        fingerprint = _json_hash({
            "inputs": inputs_hash,
            "builder_recipe": recipe_hash,
            "image": image,
            "architecture": ARCHITECTURE,
            "channel_profile": profile_hash,
            "dependencies": dependency_fingerprints,
        })
        fingerprints[name] = fingerprint
        old = old_packages.get(name, {})
        reusable = (
            isinstance(old, dict)
            and old.get("build_fingerprint") == fingerprint
            and isinstance(old.get("package_hash"), str)
            and isinstance(old.get("package_file"), str)
            and isinstance(old.get("version"), str)
        )
        records[name] = {
            "action": "reuse-candidate" if reusable else "build",
            "build_fingerprint": fingerprint,
            "build_input_hash": inputs_hash,
            "build_recipe_hash": recipe_hash,
            "channel_profile_hash": profile_hash,
            "dependency_fingerprints": dependency_fingerprints,
            "previous_version": old.get("version") if isinstance(old, dict) else None,
            "previous_package_file": old.get("package_file") if isinstance(old, dict) else None,
            "previous_package_hash": old.get("package_hash") if isinstance(old, dict) else None,
            "artifact_verification_required": reusable,
            "reason": "fingerprint unchanged; artifact still requires retrieval and hash/signature verification" if reusable else (
                "no compatible fingerprint in previous manifest"
            ),
        }
    return {
        "schema_version": 1,
        "mode": "plan-only",
        "channel": channel,
        "architecture": ARCHITECTURE,
        "image": image,
        "packages": records,
        "summary": {
            "build": sum(r["action"] == "build" for r in records.values()),
            "reuse_candidates": sum(r["action"] == "reuse-candidate" for r in records.values()),
        },
    }
