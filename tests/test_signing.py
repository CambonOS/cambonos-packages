import sys
import unittest
from unittest.mock import patch

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.common import CambonosError
from cambonos_lib.signing import validate_source_version_policy


class SourceVersionPolicyTests(unittest.TestCase):
    def _manifests(self, *, old_version="1.0-1", new_version="1.0-1",
                   old_source="a" * 64, new_source="a" * 64,
                   old_binary="b" * 64, new_binary="b" * 64):
        previous = {"channels": {}}
        current = {}
        for channel in ("stable", "testing"):
            previous["channels"][channel] = {"packages": {
                "cambonos-example": {
                    "version": old_version,
                    "source_hash": old_source,
                    "package_hash": old_binary,
                }
            }}
            current[channel] = {"packages": {
                "cambonos-example": {
                    "version": new_version,
                    "source_hash": new_source,
                    "package_hash": new_binary,
                }
            }}
        return current, previous

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_same_source_same_version_allows_different_binary(self, _compare):
        current, previous = self._manifests(new_binary="c" * 64)
        validate_source_version_policy(current, previous, "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_same_source_same_version_allows_same_binary(self, _compare):
        current, previous = self._manifests()
        validate_source_version_policy(current, previous, "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_changed_source_same_version_fails(self, _compare):
        current, previous = self._manifests(new_source="d" * 64)
        with self.assertRaises(CambonosError):
            validate_source_version_policy(current, previous, "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=-1)
    def test_changed_source_with_version_increase_passes(self, _compare):
        current, previous = self._manifests(
            new_version="1.0-2", new_source="d" * 64, new_binary="c" * 64
        )
        validate_source_version_policy(current, previous, "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=1)
    def test_version_downgrade_fails_even_when_source_is_unchanged(self, _compare):
        current, previous = self._manifests(
            old_version="1.0-2", new_version="1.0-1"
        )
        with self.assertRaises(CambonosError):
            validate_source_version_policy(current, previous, "unused-image")

    @patch("cambonos_lib.manifest.compare_arch_versions", return_value=0)
    def test_channels_are_validated_independently(self, _compare):
        current, previous = self._manifests()
        current["testing"]["packages"]["cambonos-example"]["source_hash"] = "d" * 64
        with self.assertRaises(CambonosError):
            validate_source_version_policy(current, previous, "unused-image")


if __name__ == "__main__":
    unittest.main()
