import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.validation import (  # noqa: E402
    discover_packages,
    extract_array,
    extract_function,
    extract_scalar,
    validate_package,
)


class BasePackageTests(unittest.TestCase):
    EXPECTED_DEPENDENCIES = (
        "cambonos-keyring",
        "cambonos-pacman",
        "cambonos-release",
        "cambonos-branding",
        "cambonos-fastfetch",
        "cambonos-shell-prompt",
        "cambonos-zsh",
    )

    def setUp(self):
        self.package_dir = ROOT / "packages" / "cambonos-base"
        self.pkgb_path = self.package_dir / "PKGBUILD"
        self.pkgb = self.pkgb_path.read_text(encoding="utf-8")

    def test_package_is_discovered_and_statically_valid(self):
        packages = discover_packages(ROOT)
        package = packages["cambonos-base"]
        self.assertEqual(package.pkgver, "0.1.0")
        self.assertEqual(package.pkgrel, "1")
        self.assertEqual(package.architecture, ("any",))
        self.assertEqual(validate_package(package), [])

    def test_declares_exact_base_dependencies(self):
        self.assertEqual(
            tuple(extract_array(self.pkgb, "depends")),
            self.EXPECTED_DEPENDENCIES,
        )

    def test_is_an_empty_metapackage_without_installation_side_effects(self):
        self.assertEqual(extract_function(self.pkgb, "package").strip(), ":")
        self.assertIsNone(extract_scalar(self.pkgb, "install"))
        self.assertFalse((self.package_dir / "files").exists())
        self.assertFalse(list(self.package_dir.rglob("*.hook")))
        self.assertFalse(list(self.package_dir.rglob("*.install")))

    def test_boot_components_are_not_base_dependencies(self):
        dependencies = extract_array(self.pkgb, "depends")
        self.assertNotIn("cambonos-grub", dependencies)
        self.assertNotIn("cambonos-plymouth", dependencies)

    def test_readme_documents_shell_policy_and_component_boundaries(self):
        readme = (self.package_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("Zsh forma parte obligatoria", readme)
        self.assertIn("no modifica la shell de", readme)
        self.assertIn("`cambonos-grub` y `cambonos-plymouth`", readme)
        for dependency in self.EXPECTED_DEPENDENCIES:
            with self.subTest(dependency=dependency):
                self.assertIn(f"`{dependency}`", readme)
