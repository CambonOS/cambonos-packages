"""Conservative, read-only build planning for CambonOS packages."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from .build import build_order
from .common import CambonosError
from .config import ARCHITECTURE
from .models import Package
from .validation import dependency_name, extract_function

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_hash(value: object) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _validate_payload_symlink(
    package: Package,
    path: Path,
    payload_root: Path,
    seen: set[Path] | None = None,
) -> str:
    """Return a symlink target without dereferencing absolute rootfs links.

    Absolute targets in a package payload are paths in the target system's root
    namespace (for example /usr/lib/systemd/system/foo.service), not paths on
    the build runner. Hash their literal value and never follow them.
    Relative targets must resolve inside files/.
    """
    try:
        target = os.readlink(path)
    except OSError as exc:
        raise CambonosError(
            f"{package.name}: no se pudo leer un enlace simbólico de build: {path}"
        ) from exc

    if os.path.isabs(target):
        if not path.is_relative_to(payload_root):
            raise CambonosError(
                f"{package.name}: enlace absoluto permitido únicamente en files/: {path} -> {target}"
            )
        return target

    root = payload_root.resolve()
    visited = set() if seen is None else seen
    link_path = path.absolute()
    if link_path in visited:
        raise CambonosError(
            f"{package.name}: enlace simbólico roto o cíclico en entradas de build: {path}"
        )
    visited.add(link_path)

    candidate = Path(os.path.abspath(path.parent / target))
    if not candidate.is_relative_to(root):
        raise CambonosError(
            f"{package.name}: enlace simbólico relativo fuera de files/: {path} -> {target}"
        )
    if candidate.is_symlink():
        _validate_payload_symlink(package, candidate, payload_root, visited)
        return target

    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise CambonosError(
            f"{package.name}: enlace simbólico roto o cíclico en entradas de build: {path}"
        ) from exc
    if not resolved.is_relative_to(root):
        raise CambonosError(
            f"{package.name}: enlace simbólico relativo fuera de files/: {path} -> {target}"
        )
    return target


def package_input_hash(package: Package) -> str:
    """Hash build payload, including safe symlinks and excluding documentation."""
    digest = hashlib.sha256()
    candidates = [package.directory / "PKGBUILD"]
    candidates.extend(sorted(package.directory.glob("*.install")))
    payload = package.directory / "files"
    if payload.is_dir():
        # Include symlinked files and directories, but never recurse through them.
        candidates.extend(sorted(
            path for path in payload.rglob("*")
            if path.is_symlink() or path.is_file()
        ))
    metadata = package.directory / ".cambonos-source.json"
    if metadata.is_file() or metadata.is_symlink():
        candidates.append(metadata)

    root = package.directory.resolve()
    for path in sorted(set(candidates), key=lambda item: item.relative_to(package.directory).as_posix()):
        try:
            relative_path = path.relative_to(package.directory)
            stat = path.lstat()
        except (OSError, ValueError) as exc:
            raise CambonosError(
                f"{package.name}: no se pudo inspeccionar una entrada de build: {path}"
            ) from exc
        relative = relative_path.as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(str(stat.st_mode & 0o777).encode("ascii"))
        if path.is_symlink():
            target = _validate_payload_symlink(package, path, payload)
            encoded_target = target.encode("utf-8")
            digest.update(b"L")
            digest.update(len(encoded_target).to_bytes(4, "big"))
            digest.update(encoded_target)
        elif path.is_file():
            if not path.resolve().is_relative_to(root):
                raise CambonosError(
                    f"{package.name}: entrada de build fuera del árbol del paquete: {path}"
                )
            data = path.read_bytes()
            digest.update(b"F")
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        else:
            raise CambonosError(
                f"{package.name}: tipo de entrada de build no compatible: {path}"
            )
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
        expected_version = (
            f"{package.epoch}:{package.pkgver}-{package.pkgrel}"
            if package.epoch != "0" else f"{package.pkgver}-{package.pkgrel}"
        )
        expected_arch = "any" if "any" in package.architecture else ARCHITECTURE
        expected_file = (
            f"{name}-{package.pkgver}-{package.pkgrel}-{expected_arch}.pkg.tar.zst"
        )
        reusable = (
            isinstance(old, dict)
            and old.get("build_fingerprint") == fingerprint
            and old.get("version") == expected_version
            and old.get("architecture") == expected_arch
            and old.get("package_file") == expected_file
            and isinstance(old.get("package_hash"), str)
            and bool(_HASH_RE.fullmatch(old["package_hash"]))
            and old.get("signature_file") == expected_file + ".sig"
            and isinstance(old.get("signature_hash"), str)
            and bool(_HASH_RE.fullmatch(old["signature_hash"]))
        )
        if reusable:
            reason = "fingerprint and package identity match; artifact requires cryptographic recovery verification"
        elif not isinstance(old, dict):
            reason = "new package: no previous publication record"
        elif not old.get("build_fingerprint"):
            reason = "previous publication has no build fingerprint"
        elif old.get("build_fingerprint") != fingerprint:
            reason = (
                "build inputs changed"
                if old.get("build_input_hash") != inputs_hash
                else "build recipe, environment, channel profile or dependency fingerprint changed"
            )
        else:
            reason = "package version, architecture or filename changed"
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
            "reason": reason,
        }
    return {
        "schema_version": 1,
        "mode": "plan-only",
        "channel": channel,
        "architecture": ARCHITECTURE,
        "image": image,
        "packages": records,
        "removed_packages": sorted(set(old_packages) - set(records)),
        "summary": {
            "build": sum(r["action"] == "build" for r in records.values()),
            "reuse_candidates": sum(r["action"] == "reuse-candidate" for r in records.values()),
            "removed": len(set(old_packages) - set(records)),
        },
    }
