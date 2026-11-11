from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

from scripts.cambonos_lib.artifacts import validate_recovered_artifacts_for_build
from scripts.cambonos_lib.common import CambonosError


class RecoveredBuildValidationTests(unittest.TestCase):
    def test_recovered_package_is_bound_to_signed_manifest_and_rehashed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_path = root / "manifest.json"
            manifest_path.write_text('{"signed":"fixture"}')
            signature_path = root / "manifest.json.sig"
            signature_path.write_bytes(b"sig")
            public_key = root / "keyring.gpg"
            trusted = root / "trusted"
            recovered_dir = root / "recovered"
            recovered_dir.mkdir()

            filename = "cambonos-one-1.0.0-1-any.pkg.tar.zst"
            archive = recovered_dir / filename
            detached = recovered_dir / (filename + ".sig")
            archive.write_bytes(b"package-bytes")
            detached.write_bytes(b"signature-bytes")
            digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            package_record = {
                "version": "1.0.0-1", "pkgver": "1.0.0", "pkgrel": "1",
                "epoch": "0", "architecture": "any",
                "package_file": filename, "package_hash": digest(archive),
                "signature_file": filename + ".sig", "signature_hash": digest(detached),
                "build_fingerprint": "a" * 64, "build_input_hash": "b" * 64,
                "build_recipe_hash": "c" * 64, "channel_profile_hash": "d" * 64,
                "dependency_fingerprints": {},
            }
            previous = {"channels": {"testing": {"packages": {"cambonos-one": package_record}}}}
            report_record = {
                "name": "cambonos-one", **package_record,
                "signature_verified": True, "metadata_verified": True,
            }
            report = {
                "schema_version": 1, "channel": "testing", "architecture": "x86_64",
                "manifest_signature_verified": True,
                "manifest_sha256": digest(manifest_path),
                "summary": {"recovered": 1, "failed": 0},
                "packages": [report_record],
            }
            (recovered_dir / "recovery-report.json").write_text(json.dumps(report))

            with (
                patch("scripts.cambonos_lib.artifacts.verify_previous_manifest_signature"),
                patch("scripts.cambonos_lib.artifacts.load_previous_manifest", return_value=previous),
                patch("scripts.cambonos_lib.artifacts._signing_subkeys", return_value=({"F" * 16}, {"F" * 16: "P" * 16})),
                patch("scripts.cambonos_lib.artifacts.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")),
                patch("scripts.cambonos_lib.artifacts._verify_detached_signature") as verify_sig,
                patch("scripts.cambonos_lib.artifacts._verify_package_metadata") as verify_metadata,
            ):
                loaded, artifacts = validate_recovered_artifacts_for_build(
                    manifest_path, signature_path, public_key, trusted,
                    "testing", recovered_dir, "arch-image",
                )
            self.assertIs(loaded, previous)
            self.assertEqual(artifacts["cambonos-one"], (archive, detached))
            verify_sig.assert_called_once()
            verify_metadata.assert_called_once()

    def test_recovery_report_for_another_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "manifest.json"
            manifest.write_text('{"manifest":1}')
            signature = root / "manifest.sig"
            signature.write_bytes(b"sig")
            recovered = root / "recovered"
            recovered.mkdir()
            (recovered / "recovery-report.json").write_text(json.dumps({
                "schema_version": 1, "channel": "testing", "architecture": "x86_64",
                "manifest_signature_verified": True, "manifest_sha256": "0" * 64,
                "summary": {"recovered": 0, "failed": 0}, "packages": [],
            }))
            previous = {"channels": {"testing": {"packages": {}}}}
            with (
                patch("scripts.cambonos_lib.artifacts.verify_previous_manifest_signature"),
                patch("scripts.cambonos_lib.artifacts.load_previous_manifest", return_value=previous),
            ):
                with self.assertRaisesRegex(CambonosError, "no está vinculado"):
                    validate_recovered_artifacts_for_build(
                        manifest, signature, root / "keyring.gpg", root / "trusted",
                        "testing", recovered, "arch-image",
                    )


if __name__ == "__main__":
    unittest.main()
