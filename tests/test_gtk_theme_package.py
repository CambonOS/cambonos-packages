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
        self.assertIn("pkgrel=7", pkgb)
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

    def test_whisker_categories_have_translucent_background(self):
        for stylesheet in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / stylesheet).read_text(encoding="utf-8")
            self.assertIn("window#whiskermenu-window box.categories", css)
            self.assertIn("background-color: rgba(6, 28, 49, 0.72);", css)

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

    def test_whiskermenu_uses_cambonos_dark_palette(self):
        for filename in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / filename).read_text(encoding="utf-8")
            self.assertIn("window#whiskermenu-window > frame > border", css)
            self.assertIn("background-color: #019FA7;", css)
            self.assertIn("border-color: #70E7E6;", css)
            whisker_frame = re.search(
                r"window#whiskermenu-window > frame,\s*"
                r"window#whiskermenu-window > frame > border\s*\{([^}]*)\}",
                css,
            )
            self.assertIsNotNone(whisker_frame, filename)
            self.assertIn("background: transparent;", whisker_frame.group(1))
            self.assertIn("box-shadow: none;", whisker_frame.group(1))

    def test_whiskermenu_surfaces_use_layered_transparency(self):
        for filename in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / filename).read_text(encoding="utf-8")
            self.assertRegex(
                css,
                r"window#whiskermenu-window\s*\{[^}]*background-color:\s*rgba\(6, 28, 49, 0\.58\)",
            )
            self.assertIn("window#whiskermenu-window box.categories", css)
            self.assertRegex(
                css,
                r"window#whiskermenu-window scrolledwindow\.frame\s*\{[^}]*background-color:\s*rgba\(6, 28, 49, 0\.84\)",
            )
            self.assertRegex(
                css,
                r"window#whiskermenu-window entry\.search\s*\{[^}]*background-color:\s*rgba\(6, 28, 49, 0\.90\)",
            )
            self.assertIn("background-color: rgba(6, 28, 49, 0.94);", css)

    def test_xfce_logout_dialog_uses_cambonos_palette_and_translucency(self):
        for filename in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / filename).read_text(encoding="utf-8")
            self.assertRegex(
                css,
                r"\.xfsm-logout-dialog\s*\{[^}]*background-color:\s*rgba\(6, 28, 49, 0\.94\)",
            )
            self.assertIn(".xfsm-logout-dialog button:hover", css)
            self.assertIn(".xfsm-logout-dialog button:active", css)
            self.assertIn(".xfsm-logout-dialog label", css)
            self.assertNotIn("dialog.xfsm-logout-dialog", css)
            self.assertNotIn("background-color: rgba(33, 33, 33, 0.97);", css)

    def test_gtk3_pointer_hover_uses_cambonos_teal_not_orchis_lime(self):
        selectors = (
            "row.activatable:hover",
            "treeview.view:hover",
            "flowbox > flowboxchild:hover",
            "modelbutton.flat:hover",
            ".menuitem:hover",
        )
        for filename in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / filename).read_text(encoding="utf-8")
            for selector in selectors:
                self.assertIn(selector, css, f"{filename}: {selector}")
            self.assertIn("background-color: #006B73;", css)
            self.assertIn("color: #FFFFFF;", css)
            whisker = re.search(
                r"window#whiskermenu-window scrolledwindow\.frame treeview\.view:hover,"
                r"\s*window#whiskermenu-window scrolledwindow\.frame treeview\.view:selected,"
                r"\s*window#whiskermenu-window scrolledwindow\.frame treeview\.view:selected:hover\s*\{([^}]*)\}",
                css,
            )
            self.assertIsNotNone(whisker, filename)
            self.assertIn("background-color: #006B73;", whisker.group(1))

    def test_thunar_iconview_rubberband_avoids_generic_hover_shadow(self):
        for filename in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / filename).read_text(encoding="utf-8")
            hover = re.search(
                r"\.thunar \.standard-view\.frame iconview\.view:hover\s*\{([^}]*)\}",
                css,
            )
            self.assertIsNotNone(hover, filename)
            self.assertIn("box-shadow: none;", hover.group(1))
            rubberband = re.search(
                r"\.thunar \.standard-view\.frame iconview\.view > rubberband\s*\{([^}]*)\}",
                css,
            )
            self.assertIsNotNone(rubberband, filename)
            self.assertIn("background-color: rgba(1, 159, 167, 0.24);", rubberband.group(1))
            self.assertIn("border: 1px solid #70E7E6;", rubberband.group(1))
            self.assertIn("box-shadow: none;", rubberband.group(1))
            self.assertIn("transition: none;", rubberband.group(1))

    def test_xfce_panel_uses_opaque_midnight_background(self):
        for filename in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / filename).read_text(encoding="utf-8")
            match = re.search(
                r"\.xfce4-panel\.background\s*\{([^}]*)\}", css
            )
            self.assertIsNotNone(match, filename)
            self.assertIn("background-color: #061C31;", match.group(1))
            self.assertNotRegex(match.group(1), r"background-color:\s*rgba?\(")

    def test_selection_uses_cambonos_turquoise_across_gtk_versions(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            for filename in ("gtk.css", "gtk-dark.css"):
                css = (THEME / toolkit / filename).read_text(encoding="utf-8")
                self.assertIn("#006B73", css, f"{toolkit}/{filename}")
                self.assertIn(".view:selected", css, f"{toolkit}/{filename}")
                if toolkit == "gtk-3.0":
                    self.assertIn("border: 1px solid #70E7E6;", css, f"{toolkit}/{filename}")
                    self.assertIn("background-color: rgba(1, 159, 167, 0.24);", css, f"{toolkit}/{filename}")
                else:
                    self.assertIn("@define-color accent_bg_color #006B73;", css)
                    self.assertIn("border: 1px solid #70E7E6;", css)
                self.assertNotRegex(
                    css,
                    r"(?is)(?:selected|selection-mode)[^{}]*\\{[^{}]*(?:#AEFA50|#66BB6A|#54B359|#414141)",
                )
        for filename in ("gtk.css", "gtk-dark.css"):
            css = (THEME / "gtk-3.0" / filename).read_text(encoding="utf-8")
            self.assertIn("@define-color theme_selected_bg_color #006B73;", css)
            self.assertIn("@define-color theme_unfocused_selected_bg_color #006B73;", css)

    def test_gtk2_palette_matches_cambonos_dark(self):
        gtkrc = (THEME / "gtk-2.0" / "gtkrc").read_text(encoding="utf-8")
        self.assertIn("selected_bg_color:#006B73", gtkrc)
        self.assertIn("bg_color:#061C31", gtkrc)
        self.assertIn("base_color:#061C31", gtkrc)
        self.assertIn("link_color:#70E7E6", gtkrc)
        self.assertNotRegex(gtkrc, r"#(?:66BB6A|CE93D8|212121|2C2C2C|3C3C3C|616161)")

    def test_visited_links_and_secondary_teal_use_brand_palette(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            for filename in ("gtk.css", "gtk-dark.css"):
                css = (THEME / toolkit / filename).read_text(encoding="utf-8")
                self.assertIn("color: #019FA7;", css, f"{toolkit}/{filename}")
                if toolkit == "gtk-4.0":
                    self.assertIn("--accent-teal: #70E7E6;", css)

    def test_index_theme_does_not_advertise_missing_metacity_theme(self):
        metadata = (THEME / "index.theme").read_text(encoding="utf-8")
        self.assertNotIn("MetacityTheme=", metadata)
        self.assertTrue((THEME / "xfwm4" / "themerc").is_file())

    def test_pkgbuild_has_valid_bash_syntax(self):
        result = subprocess.run(["bash", "-n", str(PACKAGE / "PKGBUILD")],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
