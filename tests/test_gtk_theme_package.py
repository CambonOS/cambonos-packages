import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-gtk-theme"
FILES = PACKAGE / "files"
THEME = FILES / "themes" / "CambonOS-Dark"


class GtkThemePackageTests(unittest.TestCase):
    def test_package_metadata_and_version(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-gtk-theme", pkgb)
        self.assertIn("pkgver=0.2.0", pkgb)
        self.assertIn("pkgrel=1", pkgb)
        self.assertIn("license=('GPL-3.0-or-later')", pkgb)
        self.assertIn('"$pkgdir/usr/share/licenses/$pkgname/LICENSE"', pkgb)
        self.assertIn('"$pkgdir/usr/share/doc/$pkgname/ORCHIS-NOTICE"', pkgb)

    def test_single_dark_theme_contains_all_approved_toolkits(self):
        metadata = (THEME / "index.theme").read_text(encoding="utf-8")
        self.assertIn("Name=CambonOS-Dark", metadata)
        self.assertIn("GtkTheme=CambonOS-Dark", metadata)
        for directory in ("gtk-2.0", "gtk-3.0", "gtk-4.0", "xfwm4"):
            self.assertTrue((THEME / directory).is_dir(), directory)
        for path in ("gtk-2.0/gtkrc", "gtk-3.0/gtk.css", "gtk-3.0/gtk-dark.css",
                     "gtk-4.0/gtk.css", "gtk-4.0/gtk-dark.css", "xfwm4/themerc"):
            self.assertTrue((THEME / path).is_file(), path)

    def test_brand_palette_is_present_in_gtk_stylesheets(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            css = (THEME / toolkit / "gtk.css").read_text(encoding="utf-8")
            self.assertIn("#AEFA50", css)
            self.assertIn("#70E7E6", css)
            self.assertEqual(css.count("{"), css.count("}"))

    def test_upstream_provenance_is_recorded(self):
        notice = (FILES / "upstream" / "ORCHIS-NOTICE").read_text(encoding="utf-8")
        self.assertIn("a4c48a425e63808345e824495964bd9c2f462e04", notice)
        self.assertIn("vinceliuice/Orchis-theme", notice)
        self.assertIn("Orchis-Green.tar.xz", notice)

    def test_no_invasive_libadwaita_or_user_configuration(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(".config/gtk-4.0", pkgb)
        self.assertNotIn("gtk-theme-name", pkgb)
        self.assertNotIn("/etc/gtk-3.0", pkgb)
        self.assertNotIn("gtk-4.0/gtk.css", pkgb)
        self.assertIn("no modifica preferencias", readme)
        self.assertFalse((FILES / "etc").exists())

    def test_payload_is_exactly_the_single_theme_and_licenses(self):
        payload = {p.relative_to(FILES).as_posix() for p in FILES.rglob("*") if p.is_file()}
        self.assertIn("LICENSE", payload)
        self.assertIn("upstream/ORCHIS-NOTICE", payload)
        self.assertIn("themes/CambonOS-Dark/index.theme", payload)
        self.assertFalse(any("CambonOS-Light" in p for p in payload))
        self.assertFalse(any("CambonOS-" in p and "CambonOS-Dark" not in p for p in payload))

    def test_pkgbuild_has_valid_bash_syntax(self):
        result = subprocess.run(["bash", "-n", str(PACKAGE / "PKGBUILD")],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
