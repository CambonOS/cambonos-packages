import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.common import sha256_directory
from cambonos_lib.manifest import validate_version_policy
from cambonos_lib.common import CambonosError


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
        current = {"sample": {"version": "1.0-1", "source_hash": "new"}}
        previous = {"channels": {"stable": {"packages": {
            "sample": {"version": "1.0-1", "source_hash": "old"}
        }}}}
        with self.assertRaises(CambonosError):
            validate_version_policy(current, previous, "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=-1)
    def test_source_change_with_version_increase_passes(self, _compare):
        current = {"sample": {"version": "1.0-2", "source_hash": "new"}}
        previous = {"channels": {"stable": {"packages": {
            "sample": {"version": "1.0-1", "source_hash": "old"}
        }}}}
        validate_version_policy(current, previous, "stable", "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=1)
    def test_version_downgrade_fails(self, _compare):
        current = {"sample": {"version": "1.0-1", "source_hash": "same"}}
        previous = {"channels": {"stable": {"packages": {
            "sample": {"version": "1.0-2", "source_hash": "same"}
        }}}}
        with self.assertRaises(CambonosError):
            validate_version_policy(current, previous, "stable", "unused-image")


if __name__ == "__main__":
    unittest.main()
