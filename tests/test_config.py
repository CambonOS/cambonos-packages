import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.config import ARCHITECTURE, BRANCH_CHANNELS, DEFAULT_ARCH_IMAGE


class ConfigTests(unittest.TestCase):
    def test_branch_channel_mapping(self):
        self.assertEqual(BRANCH_CHANNELS, {"main": "stable", "dev": "testing"})

    def test_arch_and_image_are_pinned(self):
        self.assertEqual(ARCHITECTURE, "x86_64")
        self.assertIn("@sha256:", DEFAULT_ARCH_IMAGE)


if __name__ == "__main__":
    unittest.main()
