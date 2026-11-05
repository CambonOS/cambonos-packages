from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.common import CambonosError, sha256_directory, sha256_file
from cambonos_lib.manifest import (
    load_previous_manifest, package_source_records, validate_version_policy,
    verify_build_manifest, write_build_manifest, verify_previous_manifest_signature,
)
from cambonos_lib.models import Package


HASH_A = "a" * 64
HASH_B = "b" * 64


def previous_manifest(packages=None):
    packages = packages if packages is not None else {
        "sample": {"version": "1.0-1", "source_hash": HASH_A, "package_hash": HASH_B}
    }
    return {
        "schema_version": 1,
        "publication": {"architecture": "x86_64"},
        "channels": {
            "stable": {"branch": "main", "packages": packages},
            "testing": {"branch": "dev", "packages": packages},
        },
    }


class ManifestTests(unittest.TestCase):
    def test_directory_hash_changes_with_content(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "PKGBUILD").write_text("pkgrel=1\n")
            first = sha256_directory(directory)
            (directory / "PKGBUILD").write_text("pkgrel=2\n")
            self.assertNotEqual(first, sha256_directory(directory))

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_source_change_without_version_change_fails(self, _compare):
        current = {"sample": {"version": "1.0-1", "source_hash": HASH_B}}
        with self.assertRaises(CambonosError):
            validate_version_policy(current, previous_manifest(), "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=-1)
    def test_source_change_with_version_increase_passes(self, _compare):
        current = {"sample": {"version": "1.0-2", "source_hash": HASH_B}}
        validate_version_policy(current, previous_manifest(), "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=1)
    def test_version_downgrade_fails_even_when_source_is_unchanged(self, _compare):
        current = {"sample": {"version": "1.0-1", "source_hash": HASH_A}}
        with self.assertRaises(CambonosError):
            validate_version_policy(current, previous_manifest(), "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_same_source_and_version_ignores_binary_hash(self, _compare):
        current = {"sample": {
            "version": "1.0-1", "source_hash": HASH_A, "package_hash": HASH_A,
        }}
        validate_version_policy(current, previous_manifest(), "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_new_package_is_allowed(self, _compare):
        current = {"new-package": {"version": "1.0-1", "source_hash": HASH_A}}
        validate_version_policy(current, previous_manifest(), "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_removed_package_does_not_block_channel(self, _compare):
        validate_version_policy({}, previous_manifest(), "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_stable_and_testing_are_independent(self, _compare):
        current = {
            "stable": {"packages": {"sample": {"version": "1.0-1", "source_hash": HASH_A}}},
            "testing": {"packages": {"sample": {"version": "1.0-1", "source_hash": HASH_B}}},
        }
        with self.assertRaises(CambonosError):
            for channel in ("stable", "testing"):
                validate_version_policy(
                    current[channel]["packages"], previous_manifest(), channel, "image"
                )

    def test_package_source_records_contains_source_identity_not_binary_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "PKGBUILD").write_text("pkgname=sample\n")
            package = Package(
                name="sample", directory=directory, pkgver="1.2", pkgrel="3",
                epoch="2", architecture=("any",),
            )
            records = package_source_records({"sample": package})
            self.assertEqual(records["sample"]["version"], "2:1.2-3")
            self.assertEqual(records["sample"]["source_hash"], sha256_directory(directory))
            self.assertNotIn("package_hash", records["sample"])

    def test_load_previous_manifest_accepts_valid_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(previous_manifest()))
            self.assertEqual(load_previous_manifest(path), previous_manifest())

    def test_load_previous_manifest_none_means_bootstrap(self):
        self.assertIsNone(load_previous_manifest(None))

    def test_load_previous_manifest_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"; path.write_text("{")
            with self.assertRaises(CambonosError):
                load_previous_manifest(path)

    def test_load_previous_manifest_rejects_wrong_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = previous_manifest(); data["schema_version"] = 999
            path = Path(temporary) / "manifest.json"; path.write_text(json.dumps(data))
            with self.assertRaises(CambonosError):
                load_previous_manifest(path)

    def test_load_previous_manifest_rejects_invalid_source_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = previous_manifest()
            data["channels"]["stable"]["packages"]["sample"]["source_hash"] = "bad"
            path = Path(temporary) / "manifest.json"; path.write_text(json.dumps(data))
            with self.assertRaises(CambonosError):
                load_previous_manifest(path)

    def test_load_previous_manifest_rejects_wrong_branch(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = previous_manifest(); data["channels"]["testing"]["branch"] = "main"
            path = Path(temporary) / "manifest.json"; path.write_text(json.dumps(data))
            with self.assertRaises(CambonosError):
                load_previous_manifest(path)

    def test_write_and_verify_build_manifest_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / "out"; output.mkdir()
            packages = root / "packages"; packages.mkdir()
            archive = packages / "sample-1.0-1-any.pkg.tar.zst"
            archive.write_bytes(b"package payload")
            record = {
                "version": "1.0-1", "source_hash": HASH_A,
                "package_hash": sha256_file(archive), "package_file": archive.name,
            }
            path = write_build_manifest(
                output, "stable", "main", "c" * 40, "x86_64", "arch-image",
                {"sample": record}, {"sample": "environment"},
            )
            verified = verify_build_manifest(path, packages)
            self.assertEqual(verified["packages"]["sample"], record)

    def test_verify_build_manifest_rejects_modified_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); packages = root / "packages"; packages.mkdir()
            archive = packages / "sample-1-any.pkg.tar.zst"; archive.write_bytes(b"original")
            data = {"schema_version": 1, "packages": {"sample": {
                "version": "1-1", "source_hash": HASH_A,
                "package_hash": sha256_file(archive), "package_file": archive.name,
            }}}
            manifest = root / "manifest.json"; manifest.write_text(json.dumps(data))
            archive.write_bytes(b"tampered")
            with self.assertRaisesRegex(CambonosError, "SHA256 incorrecto"):
                verify_build_manifest(manifest, packages)

    def test_verify_build_manifest_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); packages = root / "packages"; packages.mkdir()
            data = {"schema_version": 1, "packages": {"sample": {
                "version": "1-1", "source_hash": HASH_A, "package_hash": HASH_B,
                "package_file": "../outside.pkg.tar.zst",
            }}}
            manifest = root / "manifest.json"; manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(CambonosError, "nombre de artefacto no válido"):
                verify_build_manifest(manifest, packages)

    def test_verify_build_manifest_rejects_missing_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); packages = root / "packages"; packages.mkdir()
            data = {"schema_version": 1, "packages": {"sample": {
                "version": "1-1", "source_hash": HASH_A,
                "package_file": "sample-1-1-any.pkg.tar.zst",
            }}}
            manifest = root / "manifest.json"; manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(CambonosError, "package_hash"):
                verify_build_manifest(manifest, packages)

    def test_verify_build_manifest_rejects_empty_package_map(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); packages = root / "packages"; packages.mkdir()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "packages": {}}))
            with self.assertRaises(CambonosError):
                verify_build_manifest(manifest, packages)

    def test_previous_manifest_signature_requires_manifest_and_signature(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(CambonosError, "falta el manifiesto anterior"):
                verify_previous_manifest_signature(
                    root / "manifest.json", root / "manifest.json.sig",
                    root / "public.gpg", root / "trusted",
                )

    def test_previous_manifest_signature_requires_public_key_material(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_text("{}")
            (root / "manifest.json.sig").write_bytes(b"signature")
            with self.assertRaisesRegex(CambonosError, "no existe el certificado público"):
                verify_previous_manifest_signature(
                    root / "manifest.json", root / "manifest.json.sig",
                    root / "public.gpg", root / "trusted",
                )

    def test_previous_manifest_signature_requires_ownertrust_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_text("{}")
            (root / "manifest.json.sig").write_bytes(b"signature")
            (root / "public.gpg").write_bytes(b"public key")
            with self.assertRaisesRegex(CambonosError, "no existe el ownertrust"):
                verify_previous_manifest_signature(
                    root / "manifest.json", root / "manifest.json.sig",
                    root / "public.gpg", root / "trusted",
                )


if __name__ == "__main__":
    unittest.main()
