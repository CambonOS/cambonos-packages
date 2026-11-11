"""Read-only comparison of freshly built packages with recovered publication artifacts."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from .common import CambonosError, sha256_file
from .config import ARCHITECTURE
from .manifest import (
    load_previous_manifest, verify_build_manifest, verify_previous_manifest_signature,
)

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_CLASSIFICATIONS = (
    "reusable",
    "input_changed",
    "fingerprint_changed",
    "binary_mismatch",
    "identity_mismatch",
    "legacy_unverifiable",
    "new_package",
    "removed_package",
)


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CambonosError(f"no se pudo leer {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise CambonosError(f"{label} debe ser un objeto JSON")
    return value


def _safe_artifact(directory: Path, filename: object, label: str) -> Path:
    if (
        not isinstance(filename, str) or not filename
        or Path(filename).is_absolute() or Path(filename).name != filename
        or ".." in Path(filename).parts
    ):
        raise CambonosError(f"nombre de archivo inválido en {label}: {filename!r}")
    path = directory / filename
    if not path.is_file():
        raise CambonosError(f"falta {label}: {path}")
    return path


def _validate_recovery(recovered_dir: Path) -> tuple[dict, dict[str, dict]]:
    report = _read_json(recovered_dir / "recovery-report.json", "recovery-report.json")
    if report.get("schema_version") != 1:
        raise CambonosError("esquema de recovery-report.json no compatible")
    channel = report.get("channel")
    if channel not in {"testing", "stable"}:
        raise CambonosError("canal ausente o inválido en recovery-report.json")
    if report.get("architecture") != ARCHITECTURE:
        raise CambonosError("arquitectura de recuperación no compatible")
    if report.get("manifest_signature_verified") is not True:
        raise CambonosError("el informe no confirma la verificación de la firma del manifiesto")
    summary = report.get("summary")
    records = report.get("packages")
    if (
        not isinstance(summary, dict) or summary.get("failed") != 0
        or not isinstance(records, list) or summary.get("recovered") != len(records)
        or not records
    ):
        raise CambonosError("informe de recuperación incompleto o con fallos")

    packages: dict[str, dict] = {}
    for record in records:
        if not isinstance(record, dict):
            raise CambonosError("registro inválido en recovery-report.json")
        name = record.get("name")
        if not isinstance(name, str) or not name or name in packages:
            raise CambonosError(f"nombre de paquete ausente o duplicado en recuperación: {name!r}")
        if record.get("signature_verified") is not True or record.get("metadata_verified") is not True:
            raise CambonosError(f"{name}: la recuperación no acredita firma y metadatos verificados")
        package = _safe_artifact(recovered_dir, record.get("package_file"), f"paquete recuperado de {name}")
        signature = _safe_artifact(recovered_dir, record.get("signature_file"), f"firma recuperada de {name}")
        package_hash = record.get("package_hash")
        signature_hash = record.get("signature_hash")
        if not isinstance(package_hash, str) or not _HASH_RE.fullmatch(package_hash):
            raise CambonosError(f"{name}: package_hash inválido en informe de recuperación")
        if not isinstance(signature_hash, str) or not _HASH_RE.fullmatch(signature_hash):
            raise CambonosError(f"{name}: signature_hash inválido en informe de recuperación")
        if sha256_file(package) != package_hash:
            raise CambonosError(f"{name}: el paquete recuperado ha cambiado desde su verificación")
        if sha256_file(signature) != signature_hash:
            raise CambonosError(f"{name}: la firma recuperada ha cambiado desde su verificación")
        fingerprint = record.get("build_fingerprint")
        if fingerprint is not None and (not isinstance(fingerprint, str) or not _HASH_RE.fullmatch(fingerprint)):
            raise CambonosError(f"{name}: build_fingerprint inválido en recuperación")
        packages[name] = record
    return report, packages


def _validate_build(build_dir: Path) -> tuple[dict, dict[str, dict]]:
    manifest_path = build_dir / "build-manifest.json"
    packages_dir = build_dir / "packages"
    manifest = verify_build_manifest(manifest_path, packages_dir)
    if manifest.get("channel") not in {"testing", "stable"}:
        raise CambonosError("canal ausente o inválido en build-manifest.json")
    if manifest.get("architecture") != ARCHITECTURE:
        raise CambonosError("arquitectura de build-manifest.json no compatible")
    packages = manifest.get("packages")
    if not isinstance(packages, dict) or not packages:
        raise CambonosError("build-manifest.json no contiene paquetes")
    for name, record in packages.items():
        if not isinstance(record, dict):
            raise CambonosError(f"registro de build inválido para {name}")
        fingerprint = record.get("build_fingerprint")
        if not isinstance(fingerprint, str) or not _HASH_RE.fullmatch(fingerprint):
            raise CambonosError(f"{name}: build_fingerprint ausente o inválido en build-manifest.json")
        for field in ("build_input_hash", "build_recipe_hash", "channel_profile_hash"):
            value = record.get(field)
            if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
                raise CambonosError(f"{name}: {field} ausente o inválido en build-manifest.json")
        if not isinstance(record.get("dependency_fingerprints"), dict):
            raise CambonosError(f"{name}: dependency_fingerprints ausente o inválido")
    return manifest, packages


def compare_build_with_recovered(
    build_dir: Path,
    recovered_dir: Path,
    manifest_path: Path,
    signature_path: Path,
    public_key_path: Path,
    trusted_path: Path,
) -> dict:
    """Compare a full build with recovered artifacts bound to a signed manifest."""
    build_manifest, current = _validate_build(build_dir.resolve())
    recovery_report, recovered = _validate_recovery(recovered_dir.resolve())
    verify_previous_manifest_signature(
        manifest_path.resolve(), signature_path.resolve(),
        public_key_path.resolve(), trusted_path.resolve(),
    )
    previous_manifest = load_previous_manifest(manifest_path.resolve())
    channel = build_manifest["channel"]
    if recovery_report["channel"] != channel:
        raise CambonosError(
            f"los canales no coinciden: build={channel}, recuperación={recovery_report['channel']}"
        )
    if build_manifest.get("architecture") != recovery_report.get("architecture"):
        raise CambonosError("la arquitectura del build y la recuperación no coincide")
    manifest_hash = sha256_file(manifest_path)
    if recovery_report.get("manifest_sha256") != manifest_hash:
        raise CambonosError("el informe de recuperación no corresponde al manifiesto firmado proporcionado")
    channels = previous_manifest.get("channels", {}) if isinstance(previous_manifest, dict) else {}
    channel_record = channels.get(channel, {}) if isinstance(channels, dict) else {}
    previous = channel_record.get("packages", {}) if isinstance(channel_record, dict) else {}
    if not isinstance(previous, dict) or not previous:
        raise CambonosError(f"el manifiesto firmado no contiene paquetes para {channel}")
    if set(recovered) != set(previous):
        raise CambonosError("los paquetes recuperados no coinciden con los del manifiesto firmado")
    for name, recovered_record in recovered.items():
        signed_record = previous[name]
        for field in (
            "version", "architecture", "package_file", "package_hash",
            "signature_file", "signature_hash", "build_fingerprint",
            "build_input_hash", "build_recipe_hash", "channel_profile_hash",
            "dependency_fingerprints",
        ):
            if recovered_record.get(field) != signed_record.get(field):
                raise CambonosError(
                    f"{name}: el informe de recuperación no coincide con el manifiesto firmado ({field})"
                )

    comparisons: dict[str, dict] = {}
    for name in sorted(set(current) | set(previous)):
        new = current.get(name)
        old = previous.get(name)
        if old is None:
            classification = "new_package"
            reason = "el paquete no existe en la publicación recuperada"
        elif new is None:
            classification = "removed_package"
            reason = "el paquete ya no forma parte del build actual"
        elif not old.get("build_fingerprint"):
            classification = "legacy_unverifiable"
            reason = "la publicación anterior no contiene build_fingerprint; no se puede autorizar reutilización"
        elif old["build_fingerprint"] != new["build_fingerprint"]:
            if old.get("build_input_hash") != new.get("build_input_hash"):
                classification = "input_changed"
                reason = "han cambiado las entradas del paquete"
            else:
                classification = "fingerprint_changed"
                reason = "han cambiado receta, entorno, perfil o dependencias de construcción"
        elif (
            old.get("version") != new.get("version")
            or old.get("architecture") != new.get("architecture")
            or old.get("package_file") != new.get("package_file")
        ):
            classification = "identity_mismatch"
            reason = "coincide el fingerprint, pero la identidad del paquete no coincide"
        elif old.get("package_hash") != new.get("package_hash"):
            classification = "binary_mismatch"
            reason = "mismo fingerprint con SHA-256 binario diferente"
        else:
            classification = "reusable"
            reason = "fingerprint, identidad y SHA-256 coinciden; conservar paquete y firma recuperados"

        comparisons[name] = {
            "classification": classification,
            "reason": reason,
            "previous_version": old.get("version") if old else None,
            "current_version": new.get("version") if new else None,
            "previous_build_fingerprint": old.get("build_fingerprint") if old else None,
            "current_build_fingerprint": new.get("build_fingerprint") if new else None,
            "previous_package_hash": old.get("package_hash") if old else None,
            "current_package_hash": new.get("package_hash") if new else None,
            "previous_signature_hash": old.get("signature_hash") if old else None,
            "recovered_signature_verified": recovered.get(name, {}).get("signature_verified") if old else None,
        }

    summary = {classification: 0 for classification in _CLASSIFICATIONS}
    for record in comparisons.values():
        summary[record["classification"]] += 1
    return {
        "schema_version": 1,
        "mode": "shadow-only",
        "channel": channel,
        "architecture": ARCHITECTURE,
        "build_commit": build_manifest.get("commit"),
        "build_image": build_manifest.get("image"),
        "recovered_manifest_sha256": manifest_hash,
        "publication_modified": False,
        "build_skipped": False,
        "packages": comparisons,
        "summary": summary,
    }


def write_shadow_report(report: dict, output: Path) -> Path:
    """Write a report atomically without overwriting an existing result."""
    output = output.resolve()
    if output.exists():
        raise CambonosError(f"el informe shadow ya existe; no se sobrescribirá: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Hard-link creation is atomic and fails if another process created
        # the destination after the initial existence check (no overwrite race).
        os.link(temporary, output)
        temporary.unlink()
    except FileExistsError as exc:
        temporary.unlink(missing_ok=True)
        raise CambonosError(f"el informe shadow ya existe; no se sobrescribirá: {output}") from exc
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return output
