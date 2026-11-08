import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-gtk-theme"
FILES = PACKAGE / "files"
PKGBUILD = PACKAGE / "PKGBUILD"
VARIANTS = {
    "Light": {
        "background": "#f7f5ec",
        "foreground": "#102537",
        "surface": "#eef3f2",
    },
    "Dark": {
        "background": "#0a1d2b",
        "foreground": "#e4edf2",
        "surface": "#102b3d",
    },
}


class GtkThemePackageTests(unittest.TestCase):
    def test_metadata_and_license(self):
        pkgb = PKGBUILD.read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-gtk-theme", pkgb)
        self.assertIn("pkgver=0.1.0", pkgb)
        self.assertIn("pkgrel=2", pkgb)
        self.assertIn("license=('GPL-3.0-only')", pkgb)
        license_text = (FILES / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("GNU GENERAL PUBLIC LICENSE", license_text)
        self.assertIn('"$pkgdir/usr/share/licenses/$pkgname/LICENSE"', pkgb)

    def test_both_gtk3_variants_have_metadata_and_stylesheets(self):
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                theme = FILES / "themes" / f"CambonOS-{variant}"
                metadata = (theme / "index.theme").read_text(encoding="utf-8")
                css = (theme / "gtk-3.0" / "gtk.css").read_text(encoding="utf-8")
                self.assertIn(f"GtkTheme=CambonOS-{variant}", metadata)
                self.assertIn("GTK 3", metadata)
                self.assertIn("window, .background", css)
                self.assertIn("button.suggested-action", css)
                self.assertIn("entry", css)
                self.assertIn("notebook > header", css)
                self.assertIn("border-radius: 6px", css)
                self.assertIn("box-shadow:", css)
                self.assertIn(".sidebar row:hover", css)
                self.assertIn("button:focus", css)
                self.assertEqual(css.count("{"), css.count("}"))

    def test_variants_use_web_palette_and_shared_accents(self):
        accent_colors = {"#aefa50", "#70e7e6"}
        for variant, colors in VARIANTS.items():
            with self.subTest(variant=variant):
                css = (FILES / "themes" / f"CambonOS-{variant}" / "gtk-3.0" / "gtk.css").read_text(
                    encoding="utf-8"
                )
                for value in (colors["background"], colors["foreground"], colors["surface"]):
                    self.assertIn(value, css)
                self.assertTrue(accent_colors.issubset(set(re.findall(r"#[0-9a-f]{6}", css))))

    def test_every_payload_file_is_installed(self):
        pkgb = PKGBUILD.read_text(encoding="utf-8")
        actual = {
            path.relative_to(FILES).as_posix()
            for path in FILES.rglob("*")
            if path.is_file()
        }
        expected = {"LICENSE"}
        for variant in VARIANTS:
            theme_dir = f"themes/CambonOS-{variant}"
            expected.update({f"{theme_dir}/index.theme", f"{theme_dir}/gtk-3.0/gtk.css"})
        self.assertEqual(expected, actual)
        for variant in VARIANTS:
            theme_dir = f"themes/CambonOS-{variant}"
            self.assertIn(f'"$startdir/files/{theme_dir}/index.theme"', pkgb)
            self.assertIn(f'"$startdir/files/{theme_dir}/gtk-3.0/gtk.css"', pkgb)

    def test_package_does_not_force_gtk_settings(self):
        pkgb = PKGBUILD.read_text(encoding="utf-8")
        self.assertNotIn("/etc/gtk-3.0", pkgb)
        self.assertNotIn("gtk-theme-name", pkgb)
        self.assertFalse((FILES / "etc").exists())

    def test_pkgbuild_has_valid_bash_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(PKGBUILD)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()