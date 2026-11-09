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
        self.assertIn("pkgver=0.4.9", pkgb)
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
                self.assertNotIn("budgie_tasklist_indicator", css)
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        self.assertIn("@define-color accent_color #70E7E6;", gtk4)
        self.assertIn("@define-color accent_bg_color #019FA7;", gtk4)
        self.assertIn("@define-color accent_fg_color #F7F5EC;", gtk4)
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

    def test_dark_stylesheets_link_to_canonical_stylesheet(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            css_path = THEME / toolkit / "gtk.css"
            dark_path = THEME / toolkit / "gtk-dark.css"
            self.assertTrue(dark_path.is_symlink(), toolkit)
            self.assertEqual(dark_path.readlink().as_posix(), "gtk.css", toolkit)
            self.assertEqual(css_path.read_bytes(), dark_path.read_bytes(), toolkit)

    def test_translucency_policy(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        self.assertIn("@define-color theme_bg_color rgba(6, 28, 49, 0.88);", gtk3)
        self.assertIn("@define-color theme_unfocused_base_color rgba(6, 28, 49, 0.12);", gtk3)
        self.assertIn("@define-color window_bg_color rgba(6, 28, 49, 0.88);", gtk4)
        self.assertIn("@define-color theme_unfocused_base_color rgba(6, 28, 49, 0.12);", gtk4)
        self.assertNotRegex(gtk3, re.compile(r"(?m)^\.background\s*\{\s*background-color: rgba\(6, 28, 49, 0\.88\)"))
        self.assertNotRegex(gtk4, re.compile(r"(?m)^\.background\s*\{\s*background-color: rgba\(6, 28, 49, 0\.88\)"))
        self.assertRegex(gtk3, re.compile(r"window,\s*window\.background,.*?background-color: rgba\(6, 28, 49, 0\.88\)", re.S))
        self.assertRegex(gtk3, re.compile(r"\.xfce4-panel\.background\s*\{[^}]*background-color: rgba\(6, 28, 49, 0\.88\)", re.S))
        self.assertIn("background-color: rgba(6, 28, 49, 0.88);", gtk4)
        self.assertIn("button:not(.suggested-action):not(.destructive-action)", gtk3)
        self.assertIn("XfdesktopIconView.view label", gtk3)
        self.assertIn("success_color #149246", gtk4)

    def test_gtk3_gtk4_visual_policy_correlates(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        shared_colors = {
            "theme_fg_color": "#F7F5EC",
            "theme_text_color": "#F7F5EC",
            "theme_bg_color": "rgba(6, 28, 49, 0.88)",
            "theme_selected_bg_color": "#019FA7",
            "theme_selected_fg_color": "#F7F5EC",
            "warning_color": "#FBC02D",
            "error_color": "#F44336",
            "success_color": "#149246",
        }
        for name, value in shared_colors.items():
            for toolkit, css in (("GTK3", gtk3), ("GTK4", gtk4)):
                self.assertRegex(
                    css,
                    rf"(?m)^@define-color {name} {re.escape(value)};",
                    f"{toolkit} {name} diverges from the shared theme palette",
                )
        for gtk_css in (gtk3, gtk4):
            self.assertIn("background-color: rgba(112, 231, 230, 0.32);", gtk_css)
            self.assertIn("border: 1px solid #70E7E6;", gtk_css)
            self.assertIn("outline-color: #70E7E6;", gtk_css)
            self.assertIn("background-color: rgba(6, 28, 49, 0.88);", gtk_css)

    def test_xfce_desktop_integrations_remain(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        self.assertIn("window#whiskermenu-window", gtk3)
        self.assertIn("XfdesktopIconView.view", gtk3)
        self.assertIn(".xfce4-panel.background", gtk3)
        self.assertIn("window.background .view:selected", gtk3)
        self.assertNotIn(".thunar headerbar.titlebar toolbar", gtk3)

    def test_no_invasive_libadwaita_or_user_configuration(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(".config/gtk-4.0", pkgb)
        self.assertNotIn("gtk-theme-name", pkgb)
        self.assertNotIn("/etc/gtk-3.0", pkgb)
        self.assertIn("No cambia preferencias del usuario", readme)
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
            "terminator", "pamac", "gnome", "adw", "stopwatch", "mozilla",
            "#panel_window", "#login_window", "weatherthermometer", "forecast-card",
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

    def test_gtk3_surface_policy(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        self.assertIn("window.background frame,", gtk3)
        self.assertIn("notebook.frame,", gtk3)
        self.assertIn("window.background notebook", gtk3)
        self.assertIn("background-color: rgba(6, 28, 49, 0.08);", gtk3)
        self.assertIn("statusbar,", gtk3)
        self.assertIn("menubar,", gtk3)
        self.assertIn(".menubar,", gtk3)
        self.assertIn("background-color: rgba(6, 28, 49, 0.88);", gtk3)
        self.assertNotIn("terminal-window.background.csd", gtk3)
        self.assertNotIn("#MozillaGtkWidget", gtk3)

    def test_direct_window_boxes_use_window_surface(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            css = (THEME / toolkit / "gtk.css").read_text(encoding="utf-8")
            start = css.rfind("window > box {")
            self.assertGreaterEqual(start, 0, toolkit)
            block_start = css.find("{", start)
            block_end = css.find("}", block_start)
            block = css[block_start:block_end]
            self.assertIn("background-color: rgba(6, 28, 49, 0.88);", block)
            self.assertIn("background-image: none;", block)

    def test_gtk3_selection_indicators_and_general_rubberband(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        for selector in ("check:checked", "check:indeterminate", "radio:checked",
                         "radio:indeterminate", "rubberband"):
            self.assertIn(selector, gtk3)
        for asset in ("unchecked-symbolic.svg", "checkbox-checked-symbolic.svg",
                      "radio-checked-symbolic.svg", "mixed-symbolic.svg"):
            self.assertIn(f'url("assets/scalable/{asset}")', gtk3)
        self.assertIn("background-color: rgba(112, 231, 230, 0.32);", gtk3)
        self.assertIn("border: 1px solid #70E7E6;", gtk3)
        mouse_selection = gtk3[gtk3.rfind("/* GTK 3 rubberband selection"):]
        desktop_rubberband = gtk3[gtk3.rfind("XfdesktopIconView.view.rubberband"):]
        self.assertIn("XfdesktopIconView.view.rubberband", mouse_selection)
        self.assertIn("background-color: rgba(112, 231, 230, 0.32);", desktop_rubberband)
        self.assertIn("border: 1px solid #70E7E6;", desktop_rubberband)
        self.assertIn("background-image: none;", desktop_rubberband)
        self.assertNotIn(".thunar", mouse_selection)
        self.assertIn("treeview.view rubberband", mouse_selection)
        for css in (gtk3, gtk4):
            self.assertIn("background-color: rgba(112, 231, 230, 0.32);", css)
            self.assertIn("border: 1px solid #70E7E6;", css)
            self.assertNotIn("border-radius: 3px;", css[css.lower().rfind("rubberband selection"):])


    def test_selection_and_focus_follow_cambonos_palette(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        for css in (gtk3, gtk4):
            self.assertIn("@define-color theme_selected_bg_color #019FA7;", css)
            self.assertIn("@define-color theme_selected_fg_color #F7F5EC;", css)
            self.assertIn("outline-color: #70E7E6;", css)
        self.assertIn("window#whiskermenu-window box.categories > button.radio:checked", gtk3)
        self.assertIn("window#whiskermenu-window scrolledwindow.frame treeview.view:selected", gtk3)
        self.assertIn("window.background treeview.view:selected", gtk3)
        self.assertIn("window.background listview > row:selected", gtk4)
        self.assertIn("window .view:not(:selected)", gtk3)
        self.assertIn("window treeview.view:not(:selected)", gtk3)
        self.assertIn("tabbar tab:selected", gtk4)
        self.assertIn("tabbar tab:checked", gtk4)

    def test_window_surface_alpha_is_unchanged_in_backdrop_state(self):
        gtk3 = (THEME / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        gtk4 = (THEME / "gtk-4.0/gtk.css").read_text(encoding="utf-8")
        for css, selectors, alpha in (
            (gtk3, ".titlebar,\n.titlebar:backdrop", "0.12"),
            (gtk3, "window.solid-csd,", "0.88"),
            (gtk3, ".solid-csd decoration,", "0.88"),
            (gtk3, "menubar,\n.menubar,\nmenubar:backdrop", "0.6"),
            (gtk4, "menubar,\nmenubar:backdrop", "0.6"),
            (gtk4, "headerbar,\nheaderbar:backdrop", "0.12"),
            (gtk4, "window.solid-csd,", "0.88"),
            (gtk4, "popover.background,\npopover.background:backdrop", "0.16"),
        ):
            start = css.rfind(selectors)
            self.assertGreaterEqual(start, 0, selectors)
            block_start = css.find("{", start)
            block_end = css.find("}", block_start)
            block = css[block_start:block_end]
            self.assertIn(f"background-color: rgba(6, 28, 49, {alpha});", block)

    def test_tooltips_use_midnight_surface(self):
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            for filename in ("gtk.css", "gtk-dark.css"):
                css = (THEME / toolkit / filename).read_text(encoding="utf-8")
                start = css.rfind("tooltip.background,")
                self.assertGreaterEqual(start, 0, f"{toolkit}/{filename}")
                block_start = css.find("{", start)
                block_end = css.find("}", block_start)
                block = css[block_start:block_end]
                self.assertIn("background-color: rgba(6, 28, 49, 0.88);", block)
                self.assertIn("color: #F7F5EC;", block)

    def test_xfwm4_symlinks_resolve(self):
        for path in (THEME / "xfwm4").rglob("*"):
            if path.is_symlink():
                self.assertTrue(path.exists(), f"Broken symlink: {path}")

    def test_xfwm4_uses_cambonos_surface_and_control_palette(self):
        xfwm4 = THEME / "xfwm4"
        wm_colors = {
            "wm_title": "#F7F5EC",
            "wm_bg": "#061C31",
            "wm_unfocused_bg": "#0A2942",
            "wm_button_icon": "#F7F5EC",
            "wm_button_max_hover_bg": "#70E7E6",
            "wm_button_max_active_bg": "#019FA7",
        }
        for toolkit in ("gtk-3.0", "gtk-4.0"):
            css = (THEME / toolkit / "gtk.css").read_text(encoding="utf-8")
            for name, value in wm_colors.items():
                self.assertRegex(
                    css,
                    rf"(?m)^@define-color {name} {re.escape(value)};",
                    f"{toolkit} {name} diverges from XFWM4",
                )
        for name in ("bottom-active.xpm", "bottom-left-active.xpm",
                     "bottom-right-active.xpm", "left-active.xpm",
                     "title-active.xpm", "top-left-active.xpm",
                     "top-right-active.xpm"):
            self.assertIn("#061C31", (xfwm4 / name).read_text(encoding="utf-8"), name)
        for name in ("bottom-inactive.xpm", "bottom-left-inactive.xpm",
                     "bottom-right-inactive.xpm", "left-inactive.xpm",
                     "title-inactive.xpm", "top-left-inactive.xpm",
                     "top-right-inactive.xpm"):
            self.assertIn("#0A2942", (xfwm4 / name).read_text(encoding="utf-8"), name)
        for name in ("button-active.xpm", "button-inactive.xpm",
                     "button-mac-active.xpm", "button-mac-inactive.xpm"):
            self.assertIn("#F7F5EC", (xfwm4 / name).read_text(encoding="utf-8"), name)
        for path in xfwm4.glob("*-prelight.svg"):
            svg = path.read_text(encoding="utf-8")
            self.assertIn("fill:#019FA7", svg, path.name)
            self.assertIn("fill:#F7F5EC", svg, path.name)

    def test_xfwm4_theme_is_selectable_and_matches_gtk_palette(self):
        xfwm4 = THEME / "xfwm4"
        metadata = (THEME / "index.theme").read_text(encoding="utf-8")
        themerc = (THEME / "xfwm4/themerc").read_text(encoding="utf-8")
        self.assertIn("Name=CambonOS-Dark", metadata)
        self.assertIn("full_width_title=true", themerc)
        self.assertIn("active_text_color=active_text_color_2", themerc)
        self.assertIn("inactive_text_color=inactive_text_color_2", themerc)
        self.assertIn("#061C31", (THEME / "xfwm4/title-active.xpm").read_text(encoding="utf-8"))
        self.assertIn("#0A2942", (THEME / "xfwm4/title-inactive.xpm").read_text(encoding="utf-8"))
        for path in xfwm4.glob("*-prelight.svg"):
            self.assertIn("fill:#019FA7", path.read_text(encoding="utf-8"), path.name)


if __name__ == "__main__":
    unittest.main()
