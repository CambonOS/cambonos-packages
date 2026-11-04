import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.validation import (
    discover_packages, extract_array, extract_function, extract_scalar, validate_package,
)


class ValidationTests(unittest.TestCase):
    def test_static_parsers(self):
        text = """pkgname='sample'\npkgver=1.2\npkgrel=3\ndepends=('bash' 'coreutils>=9')\npackage() {\n  echo ok\n}\n"""
        self.assertEqual(extract_scalar(text, "pkgname"), "sample")
        self.assertEqual(extract_array(text, "depends"), ["bash", "coreutils>=9"])
        self.assertIn("echo ok", extract_function(text, "package"))

    def test_existing_packages_are_statically_valid(self):
        packages = discover_packages(ROOT)
        for name in ("cambonos-release", "cambonos-fastfetch", "cambonos-repo"):
            self.assertEqual(validate_package(packages[name]), [], name)

    def test_keyring_material_validation_is_consistent(self):
        packages = discover_packages(ROOT)
        keyring = packages["cambonos-keyring"]
        errors = validate_package(keyring)
        key_file = keyring.directory / "files" / "cambonos.gpg"
        if key_file.stat().st_size == 0:
            self.assertTrue(any("cambonos.gpg" in error for error in errors))
        else:
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
