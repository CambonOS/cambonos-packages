import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.config import ARCHITECTURE, BRANCH_CHANNELS, DEFAULT_ARCH_IMAGE, MIRROR_BASE_URL, REQUIRED_PACKAGES


class ConfigTests(unittest.TestCase):
    def test_branch_channel_mapping(self):
        self.assertEqual(BRANCH_CHANNELS, {"main": "stable", "dev": "testing"})

    def test_arch_and_image_are_pinned(self):
        self.assertEqual(ARCHITECTURE, "x86_64")
        self.assertIn("@sha256:", DEFAULT_ARCH_IMAGE)

    def test_canonical_mirror_origin(self):
        self.assertEqual(MIRROR_BASE_URL, "https://mirror.cambonos.org")

    def test_only_keyring_is_globally_mandatory(self):
        self.assertEqual(REQUIRED_PACKAGES, {"cambonos-keyring"})
        # cambonos-pacman is optional and can differ between channels.


if __name__ == "__main__":
    unittest.main()
