import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.common import CambonosError
from cambonos_lib.signing import validate_binary_immutability


class BinaryImmutabilityTests(unittest.TestCase):
    def _manifests(self, old_version="1.0-1", new_version="1.0-1",
                   old_hash="aaa", new_hash="aaa"):
        previous = {"channels": {}}
        current = {}
        for channel in ("stable", "testing"):
            previous["channels"][channel] = {
                "packages": {
                    "cambonos-example": {
                        "version": old_version,
                        "package_hash": old_hash,
                    }
                }
            }
            current[channel] = {
                "packages": {
                    "cambonos-example": {
                        "version": new_version,
                        "package_hash": new_hash,
                    }
                }
            }
        return current, previous

    def test_same_version_same_binary_passes(self):
        current, previous = self._manifests()
        validate_binary_immutability(current, previous)

    def test_same_version_different_binary_fails(self):
        current, previous = self._manifests(new_hash="bbb")
        with self.assertRaises(CambonosError):
            validate_binary_immutability(current, previous)

    def test_version_increase_allows_new_binary(self):
        current, previous = self._manifests(new_version="1.0-2", new_hash="bbb")
        validate_binary_immutability(current, previous)

    def test_channel_package_sets_are_independent(self):
        previous = {
            "channels": {
                "stable": {"packages": {"stable-only": {
                    "version": "1.0-1", "package_hash": "stable-hash"
                }}},
                "testing": {"packages": {"testing-only": {
                    "version": "2.0-1", "package_hash": "testing-hash"
                }}},
            }
        }
        current = {
            "stable": {"packages": {"stable-only": {
                "version": "1.0-1", "package_hash": "stable-hash"
            }}},
            "testing": {"packages": {"testing-only": {
                "version": "3.0-1", "package_hash": "new-testing-hash"
            }, "testing-new": {
                "version": "1.0-1", "package_hash": "new-package-hash"
            }}},
        }
        validate_binary_immutability(current, previous)


if __name__ == "__main__":
    unittest.main()
