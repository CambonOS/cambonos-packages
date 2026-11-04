"""GPG signing and verification. No package build scripts are executed here."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .common import CambonosError, run_command, sha256_file, require_commands
from .config import REPOSITORY_SECTION
from .manifest import (
    load_previous_manifest,
    verify_build_manifest,
    verify_previous_manifest_signature,
)
from .repository import create_repository
from .site import generate_directory_indexes, write_site_metadata, verify_site


def _fingerprints(path: Path) -> tuple[set[str], set[str], dict[str, str]]:
    result = run_command(
        ["gpg", "--batch", "--show-keys", "--with-colons",
         "--with-subkey-fingerprint", str(path)],
        capture=True,
    )
    all_fprs: set[str] = set()
    signing_fprs: set[str] = set()
    signing_primaries: dict[str, str] = {}
    current_type = None
    current_caps = ""
    current_validity = ""
    current_primary = None
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
            all_fprs.add(fingerprint)
            if current_type == "pub":
                current_primary = (
                    fingerprint if current_validity not in {"r", "e", "d"} else None
                )
            elif current_type == "sub" and "s" in current_caps and current_validity not in {"r", "e", "d"}:
                signing_fprs.add(fingerprint)
                if current_primary:
                    signing_primaries[fingerprint] = current_primary
    return all_fprs, signing_fprs, signing_primaries


def _secret_signing_fingerprints(gnupghome: Path) -> set[str]:
    result = run_command(
        ["gpg", "--batch", "--with-colons", "--with-subkey-fingerprint",
         "--list-secret-keys"],
        env={**os.environ, "GNUPGHOME": str(gnupghome)},
        capture=True,
    )
    found: set[str] = set()
    current_type = None
    current_caps = ""
    current_validity = ""
    for line in result.stdout.splitlines():
        fields = line.split(":")
        if fields[0] in {"sec", "ssb"}:
            current_type = fields[0]
            current_validity = fields[1] if len(fields) > 1 else ""
            current_caps = fields[11] if len(fields) > 11 else ""
        elif fields[0] == "fpr" and len(fields) > 9:
            if current_type == "ssb" and "s" in current_caps and current_validity not in {"r", "e", "d"}:
                found.add(fields[9].upper())
    return found


def _gpg(
    args: list[str],
    gnupghome: Path,
    passphrase_file: Path | None = None,
) -> subprocess.CompletedProcess:
    command = ["gpg", "--batch", "--homedir", str(gnupghome)]
    if passphrase_file:
        command += ["--pinentry-mode", "loopback", "--passphrase-file", str(passphrase_file)]
    return run_command(command + args, capture=True)


def _sign_file(path: Path, fingerprint: str, gnupghome: Path, passphrase_file: Path) -> Path:
    if not path.is_file():
        raise CambonosError(f"no existe el archivo que se intenta firmar: {path}")
    signature = Path(str(path) + ".sig")
    signature.unlink(missing_ok=True)
    _gpg(
        ["--local-user", fingerprint + "!", "--detach-sign",
         "--output", str(signature), str(path)],
        gnupghome,
        passphrase_file,
    )
    _gpg(["--verify", str(signature), str(path)], gnupghome)
    return signature


def _materialize_and_sign_aliases(repository: Path, database_name: str) -> None:
    for alias, target in (
        (f"{database_name}.db", f"{database_name}.db.tar.gz"),
        (f"{database_name}.files", f"{database_name}.files.tar.gz"),
    ):
        alias_path = repository / alias
        target_path = repository / target
        target_signature = Path(str(target_path) + ".sig")
        if not target_path.is_file() or not target_signature.is_file():
            raise CambonosError(f"falta la base de datos o firma {target}")
        alias_path.unlink(missing_ok=True)
        shutil.copy2(target_path, alias_path)
        shutil.copy2(target_signature, Path(str(alias_path) + ".sig"))


def validate_binary_immutability(
    channel_manifests: dict[str, dict],
    previous_manifest: dict,
) -> None:
    """Reject different package bytes published under an unchanged pacman version."""
    for channel in ("stable", "testing"):
        old_packages = previous_manifest["channels"][channel]["packages"]
        new_packages = channel_manifests[channel]["packages"]
        for name, new_record in new_packages.items():
            old_record = old_packages.get(name)
            if (
                old_record
                and old_record.get("version") == new_record.get("version")
                and old_record.get("package_hash") != new_record.get("package_hash")
            ):
                raise CambonosError(
                    f"{channel}/{name}: el binario cambió manteniendo la misma versión "
                    f"({new_record['version']}); incrementa pkgrel/pkgver"
                )


def sign_and_create_site(
    testing_root: Path,
    stable_root: Path,
    output_site: Path,
    private_key_text: str,
    passphrase: str,
    expected_fingerprint: str,
    image: str,
    expected_testing_commit: str,
    expected_stable_commit: str,
    pages_url: str,
    previous_manifest_path: Path | None = None,
    previous_manifest_signature_path: Path | None = None,
) -> None:
    require_commands("gpg", "gpgconf", "docker")
    if not private_key_text.strip() or not passphrase:
        raise CambonosError("faltan CAMBONOS_SIGNING_KEY o CAMBONOS_SIGNING_PASSPHRASE")
    expected_fingerprint = expected_fingerprint.replace(" ", "").upper()
    if not re.fullmatch(r"[0-9A-F]{40,64}", expected_fingerprint):
        raise CambonosError("CAMBONOS_SIGNING_FINGERPRINT no parece un fingerprint válido")

    if output_site.exists():
        shutil.rmtree(output_site)
    output_site.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="cambonos-gnupg-") as temp:
        gnupghome = Path(temp) / "gnupg"
        gnupghome.mkdir(mode=0o700)
        os.chmod(gnupghome, 0o700)
        key_file = Path(temp) / "signing-subkey.asc"
        passphrase_file = Path(temp) / "passphrase"
        key_file.write_text(private_key_text, encoding="utf-8")
        passphrase_file.write_text(passphrase, encoding="utf-8")
        os.chmod(key_file, 0o600)
        os.chmod(passphrase_file, 0o600)

        try:
            _gpg(["--import", str(key_file)], gnupghome)
            secret_signers = _secret_signing_fingerprints(gnupghome)
            if expected_fingerprint not in secret_signers:
                raise CambonosError(
                    "la clave importada no contiene la subclave privada de firma indicada "
                    "en CAMBONOS_SIGNING_FINGERPRINT"
                )

            channel_roots = {"testing": testing_root, "stable": stable_root}
            expected_commits = {
                "testing": expected_testing_commit,
                "stable": expected_stable_commit,
            }
            channel_manifests: dict[str, dict] = {}

            for channel, build_root in channel_roots.items():
                build_manifest = verify_build_manifest(
                    build_root / "build-manifest.json",
                    build_root / "packages",
                )
                if build_manifest.get("channel") != channel:
                    raise CambonosError(f"manifiesto recibido para el canal incorrecto: {channel}")
                if build_manifest.get("commit") != expected_commits[channel]:
                    raise CambonosError(
                        f"{channel}: el artefacto procede de {build_manifest.get('commit')}, "
                        f"pero se esperaba {expected_commits[channel]}"
                    )
                expected_branch = "dev" if channel == "testing" else "main"
                if build_manifest.get("branch") != expected_branch:
                    raise CambonosError(f"{channel}: rama de origen incorrecta")
                if build_manifest.get("architecture") != "x86_64":
                    raise CambonosError(f"{channel}: arquitectura incorrecta")
                if build_manifest.get("image") != image:
                    raise CambonosError(f"{channel}: imagen de construcción distinta de la configurada")
                if "cambonos-keyring" not in build_manifest.get("packages", {}):
                    raise CambonosError(f"{channel}: falta cambonos-keyring")

                for name, record in build_manifest["packages"].items():
                    archive = build_root / "packages" / record["package_file"]
                    _sign_file(archive, expected_fingerprint, gnupghome, passphrase_file)
                    record["signature_file"] = archive.name + ".sig"
                    record["signature_hash"] = sha256_file(Path(str(archive) + ".sig"))

                material_root = build_root / "keyring-material"
                material = material_root / "cambonos.gpg"
                trusted = material_root / "cambonos-trusted"
                revoked = material_root / "cambonos-revoked"
                if not material.is_file() or not trusted.is_file() or not revoked.is_file():
                    raise CambonosError(f"{channel}: falta material de cambonos-keyring")
                _all_fprs, signing_fprs, signing_primaries = _fingerprints(material)
                if expected_fingerprint not in signing_fprs:
                    raise CambonosError(
                        f"{channel}: cambonos-keyring no contiene la subclave de firma configurada"
                    )
                signing_primary = signing_primaries.get(expected_fingerprint)
                trust_text = trusted.read_text(errors="replace")
                if not signing_primary or not re.search(
                    rf"(?m)^{signing_primary}:6:", trust_text
                ):
                    raise CambonosError(
                        f"{channel}: cambonos-trusted no concede ownertrust ultimate (6) "
                        "a la clave primaria"
                    )

                repository = output_site / channel / "x86_64"
                create_repository(build_root, repository, channel, image)
                database_name = REPOSITORY_SECTION[channel]

                for archive in sorted(repository.glob("*.pkg.tar.*")):
                    if archive.name.endswith(".sig"):
                        continue
                    signature = Path(str(archive) + ".sig")
                    if not signature.is_file():
                        raise CambonosError(f"falta firma de paquete: {archive.name}")
                    _gpg(["--verify", str(signature), str(archive)], gnupghome)

                _sign_file(
                    repository / f"{database_name}.db.tar.gz",
                    expected_fingerprint, gnupghome, passphrase_file,
                )
                _sign_file(
                    repository / f"{database_name}.files.tar.gz",
                    expected_fingerprint, gnupghome, passphrase_file,
                )
                _materialize_and_sign_aliases(repository, database_name)

                for signature in sorted(repository.glob("*.sig")):
                    target = Path(str(signature)[:-4])
                    if target.is_file():
                        _gpg(["--verify", str(signature), str(target)], gnupghome)

                build_manifest["packages"] = {
                    name: record
                    for name, record in sorted(build_manifest["packages"].items())
                }
                build_manifest["repository"] = {
                    "database": f"{database_name}.db",
                    "database_signature": f"{database_name}.db.sig",
                    "package_count": len(build_manifest["packages"]),
                }
                channel_manifest_path = output_site / channel / "manifest.json"
                channel_manifest_path.write_text(
                    __import__("json").dumps(build_manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                _sign_file(
                    channel_manifest_path, expected_fingerprint, gnupghome, passphrase_file
                )
                channel_manifests[channel] = build_manifest

            if bool(previous_manifest_path) != bool(previous_manifest_signature_path):
                raise CambonosError("deben proporcionarse juntos el manifiesto anterior y su firma")
            if previous_manifest_path is not None:
                testing_material = testing_root / "keyring-material"
                verify_previous_manifest_signature(
                    previous_manifest_path,
                    previous_manifest_signature_path,
                    testing_material / "cambonos.gpg",
                    testing_material / "cambonos-trusted",
                )
                previous = load_previous_manifest(previous_manifest_path)
                validate_binary_immutability(channel_manifests, previous)

            write_site_metadata(output_site, channel_manifests, pages_url)
            global_manifest_path = output_site / "metadata" / "manifest.json"
            _sign_file(
                global_manifest_path, expected_fingerprint, gnupghome, passphrase_file
            )
            generated, preserved = generate_directory_indexes(output_site)
            print(
                f"Índices del mirror generados: {generated}; "
                f"páginas manuales conservadas: {preserved}."
            )
            verify_site(output_site)
        finally:
            subprocess.run(
                ["gpgconf", "--homedir", str(gnupghome), "--kill", "gpg-agent"],
                text=True,
                capture_output=True,
                check=False,
            )
