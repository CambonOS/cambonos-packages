from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cambonos_lib.common import CambonosError
from scripts.cambonos_lib.shadow import compare_build_with_recovered, write_shadow_report


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(char: str) -> str:
    return char * 64


class ShadowComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.build = self.root / "build"
        self.packages_dir = self.build / "packages"
        self.packages_dir.mkdir(parents=True)
        self.recovered = self.root / "recovered"
        self.recovered.mkdir()
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text("signed manifest fixture", encoding="utf-8")
        self.manifest_signature = self.root / "manifest.json.sig"
        self.manifest_signature.write_bytes(b"signature")
        self.public_key = self.root / "cambonos.gpg"
        self.public_key.write_bytes(b"public key")
        self.trusted = self.root / "cambonos-trusted"
        self.trusted.write_text("trusted")
        self.current_records = {}
        self.previous_records = []

    def tearDown(self):
        self.temp.cleanup()

    def add_current(self, name: str, *, fp: str, input_hash: str,
                    package_data: bytes = b"current", version: str = "1.0.0-1"):
        filename = f"{name}-1.0.0-1-any.pkg.tar.zst"
        (self.packages_dir / filename).write_bytes(package_data)
        self.current_records[name] = {
            "version": version,
            "pkgver": "1.0.0",
            "pkgrel": "1",
            "epoch": "0",
            "architecture": "any",
            "source_hash": fingerprint("1"),
            "build_input_hash": input_hash,
            "build_recipe_hash": fingerprint("2"),
            "channel_profile_hash": fingerprint("3"),
            "dependency_fingerprints": {},
            "build_fingerprint": fp,
            "package_file": filename,
            "package_hash": digest(package_data),
        }

    def add_previous(self, name: str, *, fp: str | None, input_hash: str | None,
                     package_data: bytes = b"current", version: str = "1.0.0-1"):
        filename = f"{name}-1.0.0-1-any.pkg.tar.zst"
        signature_name = filename + ".sig"
        signature_data = f"signature-{name}".encode()
        (self.recovered / filename).write_bytes(package_data)
        (self.recovered / signature_name).write_bytes(signature_data)
        record = {
            "name": name,
            "version": version,
            "architecture": "any",
            "package_file": filename,
            "package_hash": digest(package_data),
            "signature_file": signature_name,
            "signature_hash": digest(signature_data),
            "signature_verified": True,
            "metadata_verified": True,
            "build_fingerprint": fp,
            "build_input_hash": input_hash,
            "pkgver": "1.0.0",
            "pkgrel": "1",
            "epoch": "0",
            "source_hash": fingerprint("1"),
            "build_recipe_hash": fingerprint("2"),
            "channel_profile_hash": fingerprint("3"),
            "dependency_fingerprints": {},
        }
        self.previous_records.append(record)

    def compare(self):
        with patch("scripts.cambonos_lib.shadow.verify_previous_manifest_signature"), patch(
            "scripts.cambonos_lib.shadow.load_previous_manifest", return_value=json.loads(self.manifest.read_text())
        ):
            return compare_build_with_recovered(
                self.build, self.recovered, self.manifest, self.manifest_signature,
                self.public_key, self.trusted,
            )

    def finish(self):
        build_manifest = {
            "schema_version": 1,
            "channel": "testing",
            "branch": "dev",
            "commit": "a" * 40,
            "architecture": "x86_64",
            "image": "arch-image@sha256:abc",
            "packages": self.current_records,
            "build_environment": {},
        }
        (self.build / "build-manifest.json").write_text(
            json.dumps(build_manifest), encoding="utf-8"
        )
        signed_packages = {record["name"]: {key: value for key, value in record.items() if key != "name" and key not in {"signature_verified", "metadata_verified"}} for record in self.previous_records}
        previous_manifest = {
            "schema_version": 1,
            "publication": {"architecture": "x86_64"},
            "channels": {
                "testing": {"branch": "dev", "packages": signed_packages},
                "stable": {"branch": "main", "packages": signed_packages},
            },
        }
        self.manifest.write_text(json.dumps(previous_manifest), encoding="utf-8")
        recovery_report = {
            "schema_version": 1,
            "channel": "testing",
            "architecture": "x86_64",
            "manifest_sha256": digest(self.manifest.read_bytes()),
            "manifest_signature_verified": True,
            "packages": self.previous_records,
            "summary": {"recovered": len(self.previous_records), "failed": 0},
        }
        (self.recovered / "recovery-report.json").write_text(
            json.dumps(recovery_report), encoding="utf-8"
        )

    def test_identical_fingerprint_identity_and_binary_is_reusable(self):
        self.add_current("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.add_previous("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.finish()
        report = self.compare()
        self.assertEqual(report["packages"]["cambonos-demo"]["classification"], "reusable")
        self.assertFalse(report["publication_modified"])
        self.assertFalse(report["build_skipped"])

    def test_same_fingerprint_but_different_binary_is_mismatch(self):
        self.add_current("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"), package_data=b"new")
        self.add_previous("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"), package_data=b"old")
        self.finish()
        report = self.compare()
        self.assertEqual(report["packages"]["cambonos-demo"]["classification"], "binary_mismatch")

    def test_changed_inputs_are_distinguished_from_other_fingerprint_changes(self):
        self.add_current("cambonos-input", fp=fingerprint("c"), input_hash=fingerprint("c"))
        self.add_previous("cambonos-input", fp=fingerprint("b"), input_hash=fingerprint("b"))
        self.add_current("cambonos-recipe", fp=fingerprint("e"), input_hash=fingerprint("d"))
        self.add_previous("cambonos-recipe", fp=fingerprint("d"), input_hash=fingerprint("d"))
        self.finish()
        report = self.compare()
        self.assertEqual(report["packages"]["cambonos-input"]["classification"], "input_changed")
        self.assertEqual(report["packages"]["cambonos-recipe"]["classification"], "fingerprint_changed")

    def test_new_removed_and_legacy_packages_are_classified(self):
        self.add_current("cambonos-new", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.add_current("cambonos-legacy", fp=fingerprint("e"), input_hash=fingerprint("f"))
        self.add_previous("cambonos-old", fp=fingerprint("c"), input_hash=fingerprint("d"))
        self.add_previous("cambonos-legacy", fp=None, input_hash=None)
        self.finish()
        report = self.compare()
        classes = {name: value["classification"] for name, value in report["packages"].items()}
        self.assertEqual(classes["cambonos-new"], "new_package")
        self.assertEqual(classes["cambonos-old"], "removed_package")
        self.assertEqual(classes["cambonos-legacy"], "legacy_unverifiable")

    def test_recovered_artifact_is_rehashed_before_comparison(self):
        self.add_current("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.add_previous("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.finish()
        archive = self.recovered / self.previous_records[0]["package_file"]
        archive.write_bytes(b"tampered after recovery")
        with self.assertRaisesRegex(CambonosError, "ha cambiado desde su verificación"):
            self.compare()

    def test_channel_mismatch_is_rejected(self):
        self.add_current("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.add_previous("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.finish()
        report_path = self.recovered / "recovery-report.json"
        report = json.loads(report_path.read_text())
        report["channel"] = "stable"
        report_path.write_text(json.dumps(report))
        with self.assertRaisesRegex(CambonosError, "canales no coinciden"):
            self.compare()

    def test_recovery_report_must_match_signed_manifest_metadata(self):
        self.add_current("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.add_previous("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.finish()
        report_path = self.recovered / "recovery-report.json"
        report = json.loads(report_path.read_text())
        report["packages"][0]["build_fingerprint"] = fingerprint("c")
        report_path.write_text(json.dumps(report))
        with self.assertRaisesRegex(CambonosError, "no coincide con el manifiesto firmado"):
            self.compare()

    def test_recovery_report_must_reference_exact_signed_manifest(self):
        self.add_current("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.add_previous("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.finish()
        self.manifest.write_text(self.manifest.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(CambonosError, "no corresponde al manifiesto firmado"):
            self.compare()

    def test_build_without_fingerprint_is_rejected(self):
        self.add_current("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.add_previous("cambonos-demo", fp=fingerprint("a"), input_hash=fingerprint("b"))
        self.finish()
        build_manifest_path = self.build / "build-manifest.json"
        manifest = json.loads(build_manifest_path.read_text())
        del manifest["packages"]["cambonos-demo"]["build_fingerprint"]
        build_manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(CambonosError, "build_fingerprint ausente"):
            self.compare()

    def test_report_write_is_atomic_and_does_not_overwrite(self):
        output = self.root / "shadow-report.json"
        report = {"mode": "shadow-only"}
        self.assertEqual(write_shadow_report(report, output), output)
        with self.assertRaisesRegex(CambonosError, "ya existe"):
            write_shadow_report(report, output)
        self.assertEqual(json.loads(output.read_text()), report)


if __name__ == "__main__":
    unittest.main()
