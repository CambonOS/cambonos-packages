import re
import unittest
from pathlib import Path

import tinycss2

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-gtk-theme"
FILES = PACKAGE / "files"
THEME = FILES / "themes" / "CambonOS-Dark"


class GtkThemePackageTests(unittest.TestCase):
    def test_package_metadata_and_version(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-gtk-theme", pkgb)
        self.assertIn("pkgver=0.3.0", pkgb)
        self.assertIn("pkgrel=1", pkgb)
        self.assertIn("license=('GPL-3.0-only')", pkgb)
        self.assertIn('"$pkgdir/usr/share/licenses/$pkgname/LICENSE"', pkgb)
        self.assertIn('"$pkgdir/usr/share/doc/$pkgname/ORCHIS-NOTICE"', pkgb)

    def test_theme_contains_only_approved_toolkits(self):
        self.assertFalse((THEME / "gtk-2.0").exists())
        for directory in ("gtk-3.0", "gtk-4.0", "xfwm4"):
            self.assertTrue((THEME / directory).is_dir(), directory)
        for path in ("gtk-3.0/gtk.css", "gtk-3.0/gtk-dark.css",
                     "gtk-4.0/gtk.css", "gtk-4.0/gtk-dark.css", "xfwm4/themerc"):
            self.assertTrue((THEME / path).is_file(), path)

    def test_theme_metadata_and_provenance(self):
        metadata = (THEME / "index.theme").read_text(encoding="utf-8")
        notice = (FILES / "upstream/ORCHIS-NOTICE").read_text(encoding="utf-8")
        self.assertIn("Name=CambonOS-Dark", metadata)
        self.assertIn("GtkTheme=CambonOS-Dark", metadata)
        self.assertIn("based on Orchis Theme", metadata)
        self.assertIn("a4c48a425e63808345e824495964bd9c2f462e04", notice)
        self.assertIn("release/Orchis.tar.xz", notice)
        self.assertIn("Default (blue) variant and Dark", notice)
        self.assertNotIn("Orchis-Green", notice)

    def test_palette_and_semantic_colors(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            for filename in ("gtk.css", "gtk-dark.css"):
                css = (THEME / toolkit / filename).read_text(encoding="utf-8")
                self.assertIn("#061C31", css)
                self.assertIn("#019FA7", css)
                self.assertIn("#70E7E6", css)
                self.assertNotIn("#AEFA50", css)
                self.assertNotIn("#006B73", css)
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        self.assertIn("@define-color accent_color #70E7E6;", gtk4)
        self.assertIn("@define-color accent_bg_color #019FA7;", gtk4)
        self.assertIn("@define-color accent_fg_color #061C31;", gtk4)
        self.assertIn("@define-color success_color #149246;", gtk4)

    def test_no_unresolved_scss_variables(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            for filename in ("gtk.css", "gtk-dark.css"):
                css = (THEME / toolkit / filename).read_text(encoding="utf-8")
                self.assertNotRegex(css, r"\$[A-Za-z_][A-Za-z0-9_-]*")

    def test_stylesheets_parse(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            for filename in ("gtk.css", "gtk-dark.css"):
                css = (THEME / toolkit / filename).read_text(encoding="utf-8")
                rules = tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True)
                errors = [rule for rule in rules if rule.type == "error"]
                self.assertEqual(errors, [], f"{toolkit}/{filename}: {errors}")

    def test_dark_stylesheets_are_synchronized(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            css = (THEME / toolkit / "gtk.css").read_bytes()
            dark = (THEME / toolkit / "gtk-dark.css").read_bytes()
            self.assertEqual(css, dark, toolkit)

    def test_translucency_policy(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        self.assertRegex(gtk3, re.compile(r"headerbar,\s*\.titlebar,.*?background-color: rgba\(6, 28, 49, 0\.68\)", re.S))
        self.assertRegex(gtk3, r"\.xfce4-panel\.background\s*\{[^}]*background-color: rgba\(6, 28, 49, 0\.86\)", re.S)
        self.assertRegex(gtk3, r"\.xfsm-logout-dialog\s*\{[^}]*background-color: rgba\(6, 28, 49, 0\.78\)", re.S)
        self.assertIn("background-color: rgba(6, 28, 49, 0.68);", gtk4)
        self.assertIn("background-color: rgba(6, 28, 49, 0.78);", gtk4)

    def test_whisker_and_thunar_integrations_remain(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        self.assertIn("window#whiskermenu-window", gtk3)
        self.assertIn(".thunar .standard-view.frame", gtk3)
        self.assertIn("XfdesktopIconView.view", gtk3)
        self.assertIn(".xfce4-panel.background", gtk3)

    def test_no_invasive_libadwaita_or_user_configuration(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(".config/gtk-4.0", pkgb)
        self.assertNotIn("gtk-theme-name", pkgb)
        self.assertNotIn("/etc/gtk-3.0", pkgb)
        self.assertIn("no\nmodifica preferencias", readme)
        self.assertFalse((FILES / "etc").exists())

    def test_payload_has_no_extra_theme_variants(self):
        payload = {p.relative_to(FILES).as_posix() for p in FILES.rglob("*") if p.is_file()}
        self.assertIn("LICENSE", payload)
        self.assertIn("upstream/ORCHIS-NOTICE", payload)
        self.assertFalse(any("CambonOS-Light" in p for p in payload))
        self.assertFalse(any("gtk-2.0" in p for p in payload))
        self.assertFalse(any("CambonOS-Dark-hdpi" in p or "CambonOS-Dark-xhdpi" in p for p in payload))

    def test_no_application_specific_selectors_outside_xfce(self):
        import re
        forbidden = (
            "nautilus", "nemo", "caja", "budgie", "raven", "mate", "geary",
            "gedit", "pluma", "atril", "lightdm", "greeter", "firefox",
            "chromium", "inkscape", "eclipse", "meld", "tilix",
            "terminator", "pamac", "gnome", "adw", "stopwatch",
        )
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            css = (THEME / toolkit / "gtk.css").read_text(encoding="utf-8")
            rules = tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True)
            def selectors(items):
                for rule in items:
                    if rule.type == "qualified-rule":
                        yield tinycss2.serialize(rule.prelude).lower()
                    elif rule.type == "at-rule" and rule.content is not None:
                        nested = tinycss2.parse_rule_list(rule.content, skip_whitespace=True, skip_comments=True)
                        yield from selectors(nested)
            for selector in selectors(rules):
                for marker in forbidden:
                    self.assertNotRegex(selector, rf"(?<![a-z0-9]){re.escape(marker)}")

    def test_css_asset_references_resolve(self):
        import re
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            directory = THEME / toolkit
            css = (directory / "gtk.css").read_text(encoding="utf-8")
            refs = set(re.findall(r"url\([\"']?([^\)\"']+)", css))
            for ref in refs:
                if ref.startswith(("data:", "http:", "https:")):
                    continue
                self.assertTrue((directory / ref).resolve().exists(), f"{toolkit}: {ref}")

    def test_xfwm4_symlinks_resolve(self):
        for path in (THEME / "xfwm4").rglob("*"):
            if path.is_symlink():
                self.assertTrue(path.exists(), f"Broken symlink: {path}")


if __name__ == "__main__":
    unittest.main()
