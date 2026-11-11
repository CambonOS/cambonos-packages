"""Recover and verify immutable artifacts from a previous CambonOS publication."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .common import CambonosError, sha256_file, require_commands
from .config import ARCHITECTURE, DEFAULT_ARCH_IMAGE, MIRROR_BASE_URL
from .manifest import load_previous_manifest, verify_previous_manifest_signature
from .versioning import validate_package_version

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _package_filename(name: str, record: dict) -> str:
    pkgver = record.get("pkgver")
    pkgrel = record.get("pkgrel")
    architecture = record.get("architecture")
    epoch = record.get("epoch", "0")
    version = record.get("version")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9@._+-]+", name):
        raise CambonosError(f"nombre de paquete inválido en manifiesto: {name!r}")
    if not isinstance(pkgver, str) or not isinstance(pkgrel, str):
        raise CambonosError(f"pkgver/pkgrel ausentes o inválidos para {name}")
    if architecture not in {"any", ARCHITECTURE}:
        raise CambonosError(f"arquitectura de paquete no compatible para {name}: {architecture!r}")
    if not isinstance(epoch, str):
        raise CambonosError(f"epoch ausente o inválido para {name}")
    validate_package_version(pkgver, pkgrel, epoch)
    expected_version = f"{epoch}:{pkgver}-{pkgrel}" if epoch != "0" else f"{pkgver}-{pkgrel}"
    if version != expected_version:
        raise CambonosError(f"versión incoherente en manifiesto para {name}: {version!r}")
    expected = f"{name}-{pkgver}-{pkgrel}-{architecture}.pkg.tar.zst"
    if record.get("package_file") != expected:
        raise CambonosError(
            f"nombre de artefacto incoherente para {name}: "
            f"{record.get('package_file')!r}; esperado {expected!r}"
        )
    if record.get("signature_file") != expected + ".sig":
        raise CambonosError(f"nombre de firma incoherente para {name}")
    if not isinstance(record.get("package_hash"), str) or not _HASH_RE.fullmatch(record["package_hash"]):
        raise CambonosError(f"package_hash ausente o inválido para {name}")
    if not isinstance(record.get("signature_hash"), str) or not _HASH_RE.fullmatch(record["signature_hash"]):
        raise CambonosError(f"signature_hash ausente o inválido para {name}")
    return expected


def _download_https(url: str, destination: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise CambonosError("la recuperación de artefactos solo admite URLs HTTPS")
    request = Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "CambonOS-artifact-recovery/1"})
    try:
        with urlopen(request, timeout=90) as response, destination.open("wb") as output:
            final = urlparse(response.geturl())
            if final.scheme != "https" or final.netloc.lower() != parsed.netloc.lower():
                raise CambonosError("la descarga redirigió a un origen HTTPS distinto")
            shutil.copyfileobj(response, output, length=1024 * 1024)
    except CambonosError:
        raise
    except Exception as exc:  # urllib exposes several transport exceptions
        raise CambonosError(f"no se pudo descargar {url}: {exc}") from exc


def _signing_subkeys(public_key: Path) -> tuple[set[str], dict[str, str]]:
    result = subprocess.run(
        ["gpg", "--batch", "--show-keys", "--with-colons", "--with-subkey-fingerprint", str(public_key)],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise CambonosError("no se pudo inspeccionar el keyring público CambonOS")
    signers: set[str] = set()
    primaries: dict[str, str] = {}
    current_type = current_caps = current_validity = ""
    current_primary: str | None = None
    for line in result.stdout.splitlines():
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
                if current_validity not in {"r", "e", "d"}:
                    current_primary = fingerprint
            elif current_type == "sub" and "s" in current_caps and current_validity not in {"r", "e", "d"} and current_primary:
                signers.add(fingerprint)
                primaries[fingerprint] = current_primary
    if not signers:
        raise CambonosError("el keyring público no contiene subclaves de firma válidas")
    return signers, primaries


def _verify_detached_signature(
    signature: Path,
    artifact: Path,
    gnupghome: Path,
    allowed_signers: set[str],
    signer_primaries: dict[str, str],
    trusted_path: Path,
) -> None:
    result = subprocess.run(
        ["gpg", "--batch", "--homedir", str(gnupghome), "--status-fd", "1", "--verify", str(signature), str(artifact)],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise CambonosError(f"firma GPG inválida para {artifact.name}")
    valid = re.search(r"(?m)^\[GNUPG:\] VALIDSIG ([0-9A-F]+) ", result.stdout)
    signer = valid.group(1).upper() if valid else None
    if not signer or signer not in allowed_signers:
        raise CambonosError(f"{artifact.name}: firma no emitida por una subclave CambonOS autorizada")
    primary = signer_primaries.get(signer)
    trust_text = trusted_path.read_text(encoding="utf-8", errors="replace")
    if not primary or not re.search(rf"(?m)^{re.escape(primary)}:6:", trust_text):
        raise CambonosError(f"{artifact.name}: clave primaria sin ownertrust ultimate (6)")


def _verify_package_metadata(name: str, archive: Path, record: dict, image: str) -> None:
    """Inspect package identity with pacman inside the pinned Arch build image."""
    require_commands("docker")
    script = r'''
package_info="$(pacman -Qp /artifact.pkg.tar.zst)"
read -r actual_name actual_version <<< "${package_info}"
actual_arch="$(pacman -Qip /artifact.pkg.tar.zst | awk -F': ' '/^Architecture[[:space:]]*:/ {print $2; exit}')"
printf '%s\n%s\n%s\n' "${actual_name}" "${actual_version}" "${actual_arch}"
'''
    command = [
        "docker", "run", "--rm", "--network", "none",
        "--volume", f"{archive.resolve()}:/artifact.pkg.tar.zst:ro",
        image, "bash", "-euc", script,
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise CambonosError(f"no se pudo inspeccionar {archive.name}: {result.stderr.strip()}")
    identity = result.stdout.splitlines()
    expected = [name, record["version"], record["architecture"]]
    if identity != expected:
        raise CambonosError(
            f"{archive.name}: identidad del paquete incorrecta; "
            f"encontrado={identity}, esperado={expected}"
        )


def recover_previous_artifacts(
    manifest_path: Path,
    signature_path: Path,
    public_key_path: Path,
    trusted_path: Path,
    channel: str,
    output: Path,
    *,
    base_url: str = MIRROR_BASE_URL,
    image: str = DEFAULT_ARCH_IMAGE,
) -> dict:
    """Verify a signed previous publication and atomically recover its channel artifacts.

    This function never changes the mirror and refuses to overwrite an existing output.
    """
    if channel not in {"testing", "stable"}:
        raise CambonosError(f"canal no válido: {channel}")
    parsed_base = urlparse(base_url)
    if (
        parsed_base.scheme != "https" or not parsed_base.netloc
        or parsed_base.username or parsed_base.password
        or parsed_base.query or parsed_base.fragment
    ):
        raise CambonosError("base_url debe ser una URL HTTPS sin credenciales, query ni fragmento")
    for path, label in ((manifest_path, "manifiesto"), (signature_path, "firma"),
                        (public_key_path, "keyring público"), (trusted_path, "ownertrust")):
        if not path.is_file() or path.stat().st_size == 0:
            raise CambonosError(f"no existe o está vacío el archivo de {label}: {path}")
    verify_previous_manifest_signature(manifest_path, signature_path, public_key_path, trusted_path)
    previous = load_previous_manifest(manifest_path)
    channel_data = previous["channels"][channel]
    packages = channel_data["packages"]
    if not packages:
        raise CambonosError(f"el manifiesto anterior no contiene paquetes para {channel}")
    validated = {name: _package_filename(name, record) for name, record in packages.items()}

    require_commands("gpg", "gpgconf")
    allowed_signers, signer_primaries = _signing_subkeys(public_key_path)
    output = output.resolve()
    if output.exists():
        raise CambonosError(f"el destino de recuperación ya existe; no se sobrescribirá: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.recovery-", dir=output.parent))
    try:
        gnupghome = staging / ".gnupg"
        gnupghome.mkdir(mode=0o700)
        env = {**os.environ, "GNUPGHOME": str(gnupghome)}
        imported = subprocess.run(["gpg", "--batch", "--homedir", str(gnupghome), "--import", str(public_key_path)], text=True, capture_output=True, env=env, check=False)
        if imported.returncode:
            raise CambonosError("no se pudo importar el keyring público para verificar paquetes")
        recovered = []
        base = base_url.rstrip("/")
        for name, record in sorted(packages.items()):
            filename = validated[name]
            archive = staging / filename
            signature = staging / (filename + ".sig")
            for remote_name, destination, expected_hash in (
                (filename, archive, record["package_hash"]),
                (filename + ".sig", signature, record["signature_hash"]),
            ):
                url = f"{base}/{channel}/{ARCHITECTURE}/{quote(remote_name, safe='.-_')}"
                _download_https(url, destination)
                if sha256_file(destination) != expected_hash:
                    raise CambonosError(f"SHA-256 incorrecto al recuperar {channel}/{remote_name}")
            _verify_detached_signature(signature, archive, gnupghome, allowed_signers, signer_primaries, trusted_path)
            _verify_package_metadata(name, archive, record, image)
            recovered.append({
                "name": name,
                "version": record["version"],
                "architecture": record["architecture"],
                "package_file": filename,
                "package_hash": record["package_hash"],
                "signature_file": filename + ".sig",
                "signature_hash": record["signature_hash"],
                "signature_verified": True,
                "metadata_verified": True,
            })
        subprocess.run(
            ["gpgconf", "--homedir", str(gnupghome), "--kill", "gpg-agent"],
            text=True, capture_output=True, check=False,
        )
        shutil.rmtree(gnupghome, ignore_errors=True)
        report = {
            "schema_version": 1,
            "channel": channel,
            "manifest_sha256": sha256_file(manifest_path),
            "manifest_signature_verified": True,
            "architecture": ARCHITECTURE,
            "packages": recovered,
            "summary": {"recovered": len(recovered), "failed": 0},
        }
        (staging / "recovery-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(staging, output)
        return report
    except Exception:
        subprocess.run(
            ["gpgconf", "--homedir", str(staging / ".gnupg"), "--kill", "gpg-agent"],
            text=True, capture_output=True, check=False,
        )
        shutil.rmtree(staging, ignore_errors=True)
        raise
