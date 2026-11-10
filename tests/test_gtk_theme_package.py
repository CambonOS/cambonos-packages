import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.validation import discover_packages, validate_package  # noqa: E402


class GtkThemePackageTests(unittest.TestCase):
    def setUp(self):
        self.package_dir = ROOT / "packages" / "cambonos-gtk-theme"
        self.source_dir = self.package_dir / "files"
        self.pkgb = (self.package_dir / "PKGBUILD").read_text(encoding="utf-8")

    def test_package_is_discovered_and_statically_valid(self):
        packages = discover_packages(ROOT)
        package = packages["cambonos-gtk-theme"]
        self.assertEqual(package.pkgver, "0.6.0")
        self.assertEqual(package.pkgrel, "1")
        self.assertEqual(package.architecture, ("any",))
        self.assertEqual(package.makedepends, ("python",))
        self.assertEqual(validate_package(package), [])
        readme = (self.package_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("Versión unificada:", readme)
        self.assertIn("`0.6.0`", readme)

    def test_complete_upstream_source_and_builder_are_preserved(self):
        required = (
            "LICENSE", "src/palette.json", "tools/build-theme.py", "tools/validate-theme.py",
            "themes/CambonOS-dark/index.theme",
        )
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((self.source_dir / relative).is_file())
        self.assertTrue((self.package_dir / "PKGBUILD").is_file())
        self.assertEqual(
            [path.relative_to(self.package_dir).as_posix()
             for path in self.package_dir.rglob("PKGBUILD")],
            ["PKGBUILD"],
        )
        self.assertFalse(any(self.source_dir.rglob("__pycache__")))
        self.assertFalse(any(self.source_dir.rglob("*.pyc")))

    def test_pkbuild_generates_and_validates_themes_from_canonical_sources(self):
        self.assertIn("python \"$builddir/tools/build-theme.py\"", self.pkgb)
        self.assertIn("python \"$builddir/tools/validate-theme.py\"", self.pkgb)
        self.assertIn("cp -a \"$startdir/files/.\" \"$builddir/\"", self.pkgb)
        with tempfile.TemporaryDirectory() as temporary:
            builddir = Path(temporary) / "cambonos-gtk-theme-0.6.0"
            shutil.copytree(self.source_dir, builddir)
            subprocess.run(
                [sys.executable, str(builddir / "tools/build-theme.py")],
                check=True, capture_output=True, text=True,
            )
            result = subprocess.run(
                [sys.executable, str(builddir / "tools/validate-theme.py")],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("PASSED", result.stdout)
            theme = builddir / "themes" / "CambonOS-dark"
            self.assertTrue((theme / "gtk-3.0/gtk.css").is_file())
            self.assertTrue((theme / "gtk-4.0/gtk.css").is_file())
            self.assertTrue((theme / "xfwm4/themerc").is_file())
            self.assertFalse((builddir / "themes" / "CambonOS").exists())

    def test_package_installs_only_generated_runtime_and_documentation(self):
        package_body = self.pkgb.split("package() {", 1)[1]
        self.assertIn('"$pkgdir/usr/share/themes"', package_body)
        self.assertIn('"$builddir/themes/CambonOS-dark"', package_body)
        self.assertNotIn('"$builddir/themes/CambonOS"', package_body)
        self.assertIn('"$pkgdir/usr/share/licenses/$pkgname/LICENSE"', package_body)
        self.assertNotIn('"$pkgdir/usr/share/themes/source"', package_body)
        self.assertNotIn('"$pkgdir/usr/share/tools"', package_body)


if __name__ == "__main__":
    unittest.main()
