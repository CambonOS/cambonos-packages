"""Publication manifest and version policy."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .common import CambonosError, compare_arch_versions, sha256_directory, sha256_file
from .config import MANIFEST_SCHEMA_VERSION
from .models import Package
from .versioning import validate_version_transition


def package_source_records(packages: dict[str, Package]) -> dict[str, dict]:
    from .planner import package_input_hash

    records = {}
    for name, package in sorted(packages.items()):
        version = f"{package.epoch}:{package.pkgver}-{package.pkgrel}" if package.epoch != "0" else f"{package.pkgver}-{package.pkgrel}"
        records[name] = {
            "version": version,
            "epoch": package.epoch,
            "pkgver": package.pkgver,
            "pkgrel": package.pkgrel,
            "architecture": list(package.architecture),
            "source_hash": sha256_directory(package.directory),
            "build_input_hash": package_input_hash(package),
        }
    return records


def load_previous_manifest(path: Path | None) -> dict | None:
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CambonosError(f"no se pudo leer el manifiesto anterior: {exc}") from exc
    if not isinstance(data, dict):
        raise CambonosError("el manifiesto anterior debe ser un objeto JSON")
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise CambonosError("versión de esquema del manifiesto anterior no compatible")
    channels = data.get("channels")
    if not isinstance(channels, dict) or set(channels) != {"stable", "testing"}:
        raise CambonosError("manifiesto anterior debe contener stable y testing")
    publication = data.get("publication")
    if not isinstance(publication, dict) or publication.get("architecture") != "x86_64":
        raise CambonosError("arquitectura del manifiesto anterior no compatible")
    expected_branches = {"stable": "main", "testing": "dev"}
    for channel, branch in expected_branches.items():
        record = channels[channel]
        if not isinstance(record, dict) or record.get("branch") != branch:
            raise CambonosError(f"rama incorrecta en el manifiesto anterior para {channel}")
        if not isinstance(record.get("packages"), dict):
            raise CambonosError(f"el manifiesto anterior no contiene paquetes válidos para {channel}")
        for name, package in record["packages"].items():
            if (
                not isinstance(package, dict)
                or not isinstance(package.get("version"), str)
                or not package.get("version")
                or not isinstance(package.get("source_hash"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", package["source_hash"])
                or not isinstance(package.get("package_hash"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", package["package_hash"])
            ):
                raise CambonosError(f"registro incompleto del paquete {channel}/{name}")
    return data


def validate_version_policy(
    current: dict[str, dict],
    previous: dict | None,
    channel: str,
    image: str,
) -> None:
    if previous is None:
        print(f"Primera publicación autorizada para {channel}; no hay manifiesto anterior.")
        return
    old_channel = previous["channels"].get(channel)
    if not isinstance(old_channel, dict) or not isinstance(old_channel.get("packages"), dict):
        raise CambonosError(f"el manifiesto anterior no contiene el canal {channel}")
    old_packages = old_channel["packages"]
    for name, new in current.items():
        old = old_packages.get(name)
        if old is None:
            print(f"Paquete nuevo en {channel}: {name}")
            continue
        old_version = old.get("version", "0")
        if old.get("build_input_hash") and new.get("build_input_hash"):
            changed = old["build_input_hash"] != new["build_input_hash"]
        else:
            # Legacy manifests cannot distinguish build inputs from documentation.
            # Keep the old conservative source-tree comparison for this transition.
            changed = old.get("source_hash") != new["source_hash"]
        try:
            comparison = validate_version_transition(
                old_version,
                new["pkgver"],
                new["pkgrel"],
                new["epoch"],
                image,
                comparator=compare_arch_versions,
            )
        except CambonosError as exc:
            raise CambonosError(f"{channel}/{name}: {exc}") from exc
        if comparison == 0:
            if changed:
                raise CambonosError(
                    f"{channel}/{name}: cambió el contenido fuente sin incrementar "
                    f"pkgver (versión {new['version']})"
                )
    removed = sorted(set(old_packages) - set(current))
    if removed:
        print(f"Paquetes que se retirarán de {channel}: {', '.join(removed)}")



def verify_previous_manifest_signature(
    manifest_path: Path,
    signature_path: Path,
    public_key_path: Path,
    trusted_path: Path,
) -> None:
    """Verify the previous Pages manifest using the current CambonOS public keyring."""
    import re
    import shutil
    import subprocess
    import tempfile

    if not manifest_path.is_file() or not signature_path.is_file():
        raise CambonosError("falta el manifiesto anterior o su firma detached")
    if not public_key_path.is_file() or public_key_path.stat().st_size == 0:
        raise CambonosError("no existe el certificado público CambonOS para verificar el manifiesto")
    if not trusted_path.is_file() or trusted_path.stat().st_size == 0:
        raise CambonosError("no existe el ownertrust CambonOS para verificar el manifiesto")
    if not shutil.which("gpg"):
        raise CambonosError("se necesita gpg para verificar la firma del manifiesto anterior")

    with tempfile.TemporaryDirectory(prefix="cambonos-manifest-verify-") as temp:
        home = Path(temp) / "gnupg"
        home.mkdir(mode=0o700)
        env = {**__import__("os").environ, "GNUPGHOME": str(home)}
        imported = subprocess.run(
            ["gpg", "--batch", "--import", str(public_key_path)],
            text=True, capture_output=True, env=env, check=False,
        )
        if imported.returncode:
            raise CambonosError("no se pudo importar la clave pública CambonOS para verificar el manifiesto")
        keys = subprocess.run(
            ["gpg", "--batch", "--show-keys", "--with-colons",
             "--with-subkey-fingerprint", str(public_key_path)],
            text=True, capture_output=True, check=False,
        )
        signing_primaries = {}
        current_type = None
        current_caps = ""
        current_validity = ""
        current_primary = None
        for line in keys.stdout.splitlines():
            fields = line.split(":")
            if fields[0] in {"pub", "sub"}:
                current_type = fields[0]
                current_validity = fields[1] if len(fields) > 1 else ""
                current_caps = fields[11] if len(fields) > 11 else ""
                if current_type == "pub":
                    current_primary = None
            elif fields[0] == "fpr" and len(fields) > 9:
                fingerprint = fields[9].upper()
                if current_type == "pub":
                    current_primary = (
                        fingerprint if current_validity not in {"r", "e", "d"} else None
                    )
                elif (
                    current_type == "sub" and "s" in current_caps
                    and current_validity not in {"r", "e", "d"} and current_primary
                ):
                    signing_primaries[fingerprint] = current_primary
        if not signing_primaries:
            raise CambonosError("el certificado público no contiene subclaves de firma")

        verified = subprocess.run(
            ["gpg", "--batch", "--status-fd", "1", "--verify",
             str(signature_path), str(manifest_path)],
            text=True, capture_output=True, env=env, check=False,
        )
        if verified.returncode:
            raise CambonosError("la firma del manifiesto anterior no es válida")
        valid = re.search(r"(?m)^\[GNUPG:\] VALIDSIG ([0-9A-F]+) ", verified.stdout)
        signer = valid.group(1).upper() if valid else None
        if not signer or signer not in signing_primaries:
            raise CambonosError(
                "el manifiesto no está firmado por una subclave de firma del keyring CambonOS actual"
            )
        primary = signing_primaries[signer]
        trust_text = trusted_path.read_text(errors="replace")
        if not re.search(rf"(?m)^{primary}:6:", trust_text):
            raise CambonosError("la clave primaria que firmó el manifiesto no tiene ownertrust ultimate (6)")


def write_build_manifest(
    output: Path,
    channel: str,
    branch: str,
    commit: str,
    architecture: str,
    image: str,
    packages: dict[str, dict],
    build_environment: dict,
) -> Path:
    data = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "channel": channel,
        "branch": branch,
        "commit": commit,
        "architecture": architecture,
        "image": image,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "packages": packages,
        "build_environment": build_environment,
    }
    path = output / "build-manifest.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def verify_build_manifest(path: Path, package_dir: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CambonosError(f"manifiesto de construcción inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise CambonosError("el manifiesto de construcción debe ser un objeto JSON")
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise CambonosError("esquema de manifiesto de construcción no compatible")
    packages = data.get("packages")
    if not isinstance(packages, dict) or not packages:
        raise CambonosError("el manifiesto de construcción no contiene paquetes")
    for name, record in packages.items():
        if not isinstance(record, dict):
            raise CambonosError(f"registro inválido para el paquete {name}")
        filename = record.get("package_file", "")
        if not isinstance(record.get("version"), str) or not record["version"]:
            raise CambonosError(f"versión ausente o inválida para {name}")
        if not isinstance(record.get("source_hash"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", record["source_hash"]
        ):
            raise CambonosError(f"source_hash ausente o inválido para {name}")
        if not isinstance(record.get("package_hash"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", record["package_hash"]
        ):
            raise CambonosError(f"package_hash ausente o inválido para {name}")
        if not isinstance(filename, str):
            raise CambonosError(f"nombre de artefacto no válido para {name}")
        candidate = Path(filename)
        if (
            not filename
            or candidate.is_absolute()
            or candidate.name != filename
            or ".." in candidate.parts
            or not filename.endswith(".pkg.tar.zst")
        ):
            raise CambonosError(f"nombre de artefacto no válido para {name}: {filename!r}")
        archive = package_dir / filename
        if not archive.is_file() or archive.is_symlink():
            raise CambonosError(f"falta el artefacto regular de {name}: {archive.name}")
        if sha256_file(archive) != record.get("package_hash"):
            raise CambonosError(f"SHA256 incorrecto para {archive.name}")
        if record.get("reused_from_publication") is True:
            signature_name = record.get("signature_file")
            signature_hash = record.get("signature_hash")
            if (
                not isinstance(signature_name, str)
                or signature_name != filename + ".sig"
                or not isinstance(signature_hash, str)
                or not re.fullmatch(r"[0-9a-f]{64}", signature_hash)
            ):
                raise CambonosError(f"metadata de firma preservada inválida para {name}")
            signature_path = package_dir / signature_name
            if (
                not signature_path.is_file() or signature_path.is_symlink()
                or sha256_file(signature_path) != signature_hash
            ):
                raise CambonosError(f"firma preservada ausente o SHA256 incorrecto para {name}")
    return data
