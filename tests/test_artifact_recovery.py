from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cambonos_lib.artifacts import (
    _package_filename,
    _verify_package_metadata,
    recover_previous_artifacts,
)
from scripts.cambonos_lib.common import CambonosError


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_record(name: str = "cambonos-demo") -> tuple[dict, bytes, bytes]:
    archive_data = b"fake-zstd-package-content"
    signature_data = b"fake-detached-signature"
    filename = f"{name}-1.2.3-4-any.pkg.tar.zst"
    record = {
        "version": "1.2.3-4",
        "pkgver": "1.2.3",
        "pkgrel": "4",
        "epoch": "0",
        "architecture": "any",
        "source_hash": "a" * 64,
        "build_input_hash": "b" * 64,
        "package_file": filename,
        "package_hash": digest(archive_data),
        "signature_file": filename + ".sig",
        "signature_hash": digest(signature_data),
    }
    return record, archive_data, signature_data


class ArtifactRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.json"
        self.signature = self.root / "manifest.json.sig"
        self.public_key = self.root / "cambonos.gpg"
        self.trusted = self.root / "cambonos-trusted"
        self.manifest.write_text("{}")
        self.signature.write_bytes(b"manifest-signature")
        self.public_key.write_bytes(b"public-key")
        self.trusted.write_text("F" * 40 + ":6:\n")
        record, self.archive_data, self.signature_data = package_record()
        self.record = record
        self.previous = {
            "schema_version": 1,
            "publication": {"architecture": "x86_64"},
            "channels": {
                "testing": {"branch": "dev", "packages": {"cambonos-demo": record}},
                "stable": {"branch": "main", "packages": {"cambonos-demo": record}},
            },
        }
        self.output = self.root / "recovered"

    def tearDown(self):
        self.temp.cleanup()

    def _download(self, url: str, destination: Path) -> None:
        if url.endswith(".sig") and not url.endswith("manifest.json.sig"):
            destination.write_bytes(self.signature_data)
        else:
            destination.write_bytes(self.archive_data)

    def _run(self):
        with (
            patch("scripts.cambonos_lib.artifacts.verify_previous_manifest_signature"),
            patch("scripts.cambonos_lib.artifacts.load_previous_manifest", return_value=self.previous),
            patch("scripts.cambonos_lib.artifacts.require_commands"),
            patch("scripts.cambonos_lib.artifacts._signing_subkeys", return_value=({"S" * 40}, {"S" * 40: "F" * 40})),
            patch("scripts.cambonos_lib.artifacts._verify_detached_signature") as verify_signature,
            patch("scripts.cambonos_lib.artifacts._verify_package_metadata") as verify_metadata,
            patch("scripts.cambonos_lib.artifacts._download_https", side_effect=self._download),
            patch("scripts.cambonos_lib.artifacts.subprocess.run", return_value=__import__("subprocess").CompletedProcess([], 0, "", "")),
        ):
            report = recover_previous_artifacts(
                self.manifest, self.signature, self.public_key, self.trusted,
                "testing", self.output,
            )
        return report, verify_signature, verify_metadata

    def test_recovers_hash_verified_package_and_signature(self):
        report, verify_signature, verify_metadata = self._run()
        self.assertEqual(report["summary"], {"recovered": 1, "failed": 0})
        self.assertTrue(report["manifest_signature_verified"])
        self.assertEqual((self.output / self.record["package_file"]).read_bytes(), self.archive_data)
        self.assertEqual((self.output / self.record["signature_file"]).read_bytes(), self.signature_data)
        self.assertTrue((self.output / "recovery-report.json").is_file())
        verify_signature.assert_called_once()
        verify_metadata.assert_called_once()

    def test_rejects_hash_mismatch_and_leaves_no_output(self):
        self.record["package_hash"] = "0" * 64
        with self.assertRaisesRegex(CambonosError, "SHA-256 incorrecto"):
            self._run()
        self.assertFalse(self.output.exists())

    def test_rejects_existing_output_without_overwriting(self):
        self.output.mkdir()
        sentinel = self.output / "keep.txt"
        sentinel.write_text("keep")
        with self.assertRaisesRegex(CambonosError, "ya existe"):
            self._run()
        self.assertEqual(sentinel.read_text(), "keep")

    def test_rejects_inconsistent_package_filename(self):
        self.record["package_file"] = "other-1.2.3-4-any.pkg.tar.zst"
        with self.assertRaisesRegex(CambonosError, "nombre de artefacto incoherente"):
            _package_filename("cambonos-demo", self.record)

    def test_rejects_invalid_package_signature_and_cleans_staging(self):
        with patch("scripts.cambonos_lib.artifacts.verify_previous_manifest_signature"), \
             patch("scripts.cambonos_lib.artifacts.load_previous_manifest", return_value=self.previous), \
             patch("scripts.cambonos_lib.artifacts.require_commands"), \
             patch("scripts.cambonos_lib.artifacts._signing_subkeys", return_value=({"S" * 40}, {"S" * 40: "F" * 40})), \
             patch("scripts.cambonos_lib.artifacts._verify_detached_signature", side_effect=CambonosError("firma GPG inválida")), \
             patch("scripts.cambonos_lib.artifacts._download_https", side_effect=self._download), \
             patch("scripts.cambonos_lib.artifacts.subprocess.run", return_value=__import__("subprocess").CompletedProcess([], 0, "", "")):
            with self.assertRaisesRegex(CambonosError, "firma GPG inválida"):
                recover_previous_artifacts(
                    self.manifest, self.signature, self.public_key, self.trusted,
                    "testing", self.output,
                )
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".recovered.recovery-*")), [])

    def test_embedded_package_identity_is_checked(self):
        archive = self.root / self.record["package_file"]
        archive.write_bytes(self.archive_data)
        completed = __import__("subprocess").CompletedProcess(
            [], 0,
            "cambonos-demo\n1.2.3-4\nany\n",
            "",
        )
        with patch("scripts.cambonos_lib.artifacts.require_commands"), patch(
            "scripts.cambonos_lib.artifacts.subprocess.run", return_value=completed
        ):
            _verify_package_metadata("cambonos-demo", archive, self.record, "arch-image")
        wrong = __import__("subprocess").CompletedProcess(
            [], 0,
            "cambonos-demo\n1.2.3-5\nany\n",
            "",
        )
        with patch("scripts.cambonos_lib.artifacts.require_commands"), patch(
            "scripts.cambonos_lib.artifacts.subprocess.run", return_value=wrong
        ):
            with self.assertRaisesRegex(CambonosError, "identidad del paquete incorrecta"):
                _verify_package_metadata("cambonos-demo", archive, self.record, "arch-image")

    def test_rejects_signature_filename_mismatch(self):
        self.record["signature_file"] = "wrong.sig"
        with self.assertRaisesRegex(CambonosError, "nombre de firma incoherente"):
            _package_filename("cambonos-demo", self.record)

    def test_rejects_inconsistent_version_fields(self):
        self.record["version"] = "1.2.3-5"
        with self.assertRaisesRegex(CambonosError, "versión incoherente"):
            _package_filename("cambonos-demo", self.record)

    def test_rejects_non_https_base_url(self):
        with patch("scripts.cambonos_lib.artifacts.verify_previous_manifest_signature"), patch(
            "scripts.cambonos_lib.artifacts.load_previous_manifest", return_value=self.previous
        ):
            with self.assertRaisesRegex(CambonosError, "HTTPS"):
                recover_previous_artifacts(
                    self.manifest, self.signature, self.public_key, self.trusted,
                    "testing", self.output, base_url="http://example.invalid",
                )

    def test_refuses_empty_channel(self):
        self.previous["channels"]["testing"]["packages"] = {}
        with patch("scripts.cambonos_lib.artifacts.verify_previous_manifest_signature"), patch(
            "scripts.cambonos_lib.artifacts.load_previous_manifest", return_value=self.previous
        ):
            with self.assertRaisesRegex(CambonosError, "no contiene paquetes"):
                recover_previous_artifacts(
                    self.manifest, self.signature, self.public_key, self.trusted,
                    "testing", self.output,
                )


if __name__ == "__main__":
    unittest.main()
