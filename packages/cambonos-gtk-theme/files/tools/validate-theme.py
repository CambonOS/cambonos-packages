#!/usr/bin/env python3
"""Dependency-free structural checks for the generated CambonOS GTK theme."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "CambonOS-dark": {"window_opacity": 0.98, "multiplier": 1},
    "CambonOS-dark-Balanced": {"window_opacity": 0.88, "multiplier": 5},
    "CambonOS-dark-Transparent": {"window_opacity": 0.78, "multiplier": 10},
}
THEMES = tuple(VARIANTS)
PALETTE = json.loads((ROOT / "src/palette.json").read_text())
APIS = ("gtk-3.0", "gtk-4.0")
errors = []

for theme in THEMES:
    theme_root = ROOT / "themes" / theme
    if not (theme_root / "index.theme").is_file():
        errors.append(f"{theme}: missing index.theme")
    for api in APIS:
        api_root = theme_root / api
        for entry in ("gtk.css", "gtk-dark.css"):
            entry_path = api_root / entry
            if not entry_path.is_file():
                errors.append(f"{theme}/{api}: missing {entry}")
                continue
            entry_css = entry_path.read_text()
            imports = re.findall(r'@import\s+url\("([^"]+)"\)\s*;', entry_css)
            if len(imports) != 2:
                errors.append(f"{theme}/{api}/{entry}: expected palette and widgets imports")
                continue
            combined = "\n".join((api_root / item).read_text() for item in imports if (api_root / item).is_file())
            for item in imports:
                if not (api_root / item).is_file():
                    errors.append(f"{theme}/{api}/{entry}: missing import {item}")
            defined = set(re.findall(r"@define-color\s+([\w-]+)", combined))
            widget_path = api_root / "widgets.css"
            if not widget_path.is_file():
                errors.append(f"{theme}/{api}: missing widgets.css")
                continue
            widgets = widget_path.read_text()
            used = set(re.findall(r"@([\w-]+)", widgets))
            missing = sorted(used - defined)
            if missing:
                errors.append(f"{theme}/{api}/{entry}: undefined colors: {', '.join(missing)}")
        for css_path in api_root.glob("*.css"):
            css = re.sub(r"/\*.*?\*/", "", css_path.read_text(), flags=re.S)
            if css.count("{") != css.count("}"):
                errors.append(f"{css_path.relative_to(ROOT)}: unbalanced braces")
            if css.count("(") != css.count(")"):
                errors.append(f"{css_path.relative_to(ROOT)}: unbalanced parentheses")


# Xfwm4 compatibility assets: required frame parts and action-button states.
FRAME_PARTS = (
    "top-left", "top-right", "title-1", "title-2", "title-3", "title-4", "title-5",
    "left", "right", "bottom-left", "bottom", "bottom-right",
)
BUTTON_PARTS = {
    "menu": ("active", "inactive", "prelight", "pressed"),
    "hide": ("active", "inactive", "prelight", "pressed"),
    "maximize": ("active", "inactive", "prelight", "pressed",
                 "toggled-active", "toggled-inactive", "toggled-prelight", "toggled-pressed"),
    "close": ("active", "inactive", "prelight", "pressed"),
    "shade": ("active", "inactive", "prelight", "pressed",
              "toggled-active", "toggled-inactive", "toggled-prelight", "toggled-pressed"),
    "stick": ("active", "inactive", "prelight", "pressed",
              "toggled-active", "toggled-inactive", "toggled-prelight", "toggled-pressed"),
}
for theme in THEMES:
    xfwm = ROOT / "themes" / theme / "xfwm4"
    if not (xfwm / "themerc").is_file():
        errors.append(f"{theme}/xfwm4: missing themerc")
    required = [f"{part}-{state}.xpm" for part in FRAME_PARTS for state in ("active", "inactive")]
    required += [f"{button}-{state}.xpm" for button, states in BUTTON_PARTS.items() for state in states]
    for filename in required:
        path = xfwm / filename
        if not path.is_file():
            errors.append(f"{theme}/xfwm4: missing {filename}")
            continue
        lines = path.read_text(errors="replace").splitlines()
        if not lines or "XPM" not in lines[0]:
            errors.append(f"{theme}/xfwm4/{filename}: invalid XPM header")
        if len(lines) < 3:
            errors.append(f"{theme}/xfwm4/{filename}: missing XPM dimensions header")
            continue
        header = lines[2].strip().strip('",')
        fields = header.split()
        if len(fields) != 4 or not all(field.isdigit() for field in fields):
            errors.append(f"{theme}/xfwm4/{filename}: invalid XPM dimensions header")
            continue
        width, height, ncolors, cpp = map(int, fields)
        color_start = 3
        pixel_start = color_start + ncolors
        pixel_rows = lines[pixel_start:pixel_start + height]
        if len(lines) < pixel_start + height:
            errors.append(f"{theme}/xfwm4/{filename}: truncated XPM pixel data")
            continue
        if any(len(row.strip().strip('",')) != width * cpp for row in pixel_rows):
            errors.append(f"{theme}/xfwm4/{filename}: XPM pixel row has incorrect width")


# The top corners must span the full titlebar height; short 8x8 tiles leave
# unpainted/black gaps at the upper window edges. Parse dimensions from XPM
# headers directly so the validator has no Pillow dependency.
for theme in THEMES:
    xfwm = ROOT / "themes" / theme / "xfwm4"
    def xpm_height(path):
        lines = path.read_text(errors="replace").splitlines()
        if len(lines) < 3:
            return None
        fields = lines[2].strip().strip('",').split()
        if len(fields) != 4 or not all(field.isdigit() for field in fields):
            return None
        return int(fields[1])
    expected_height = xpm_height(xfwm / "title-1-active.xpm")
    for corner in ("top-left-active", "top-left-inactive",
                   "top-right-active", "top-right-inactive"):
        path = xfwm / f"{corner}.xpm"
        actual_height = xpm_height(path)
        if actual_height != expected_height:
            errors.append(
                f"{theme}/xfwm4/{corner}.xpm: height {actual_height}px "
                f"does not match titlebar height {expected_height}px"
            )


# With show_app_icon=true, menu button pixmaps need an opaque background so
# Xfwm4 can composite the application icon into the menu-button area.
for theme in THEMES:
    xfwm = ROOT / "themes" / theme / "xfwm4"
    themerc = (xfwm / "themerc").read_text(errors="replace")
    if "show_app_icon=true" in themerc:
        for state in ("active", "inactive", "prelight", "pressed"):
            path = xfwm / f"menu-{state}.xpm"
            lines = path.read_text(errors="replace").splitlines()
            color_lines = lines[3:3 + int(lines[2].strip().strip('",').split()[2])]
            if any(" c None" in line for line in color_lines):
                errors.append(f"{theme}/xfwm4/menu-{state}.xpm: transparent color is not allowed with show_app_icon=true")


# Keep application-menu icon geometry intentional and consistent across states.
# Xfwm4 uses the menu XPM dimensions as the available app-icon area.
for theme in THEMES:
    xfwm = ROOT / "themes" / theme / "xfwm4"
    for state in ("active", "inactive", "prelight", "pressed"):
        path = xfwm / f"menu-{state}.xpm"
        lines = path.read_text(errors="replace").splitlines()
        fields = lines[2].strip().strip('",').split() if len(lines) > 2 else []
        if len(fields) != 4 or fields[:2] != ["16", "22"]:
            errors.append(f"{theme}/xfwm4/menu-{state}.xpm: expected 16x22 menu icon area")

# Verify the generated opacity policy, metadata, and RGB consistency.
def rgba_definitions(path):
    content = path.read_text()
    return {
        name: (tuple(map(int, rgb.split(","))), float(alpha))
        for name, rgb, alpha in re.findall(
            r"@define-color\s+([\w-]+)\s+rgba\(\s*(\d+\s*,\s*\d+\s*,\s*\d+)\s*,\s*([0-9.]+)\s*\)",
            content,
        )
    }

reference_rgb = {}
for theme, policy in VARIANTS.items():
    theme_root = ROOT / "themes" / theme
    index = (theme_root / "index.theme").read_text(errors="replace") if (theme_root / "index.theme").is_file() else ""
    for field in (f"Name={theme}", f"GtkTheme={theme}", f"MetacityTheme={theme}"):
        if field not in index:
            errors.append(f"{theme}/index.theme: missing {field!r}")

    for api, window_token in (("gtk-3.0", "theme_bg_color"), ("gtk-4.0", "window_bg_color")):
        colors_path = theme_root / api / "colors-dark.css"
        if not colors_path.is_file():
            continue
        definitions = rgba_definitions(colors_path)
        if window_token not in definitions:
            errors.append(f"{theme}/{api}/colors-dark.css: missing RGBA token {window_token}")
            continue
        window_alpha = definitions[window_token][1]
        if abs(window_alpha - policy["window_opacity"]) > 1e-6:
            errors.append(
                f"{theme}/{api}: {window_token} alpha {window_alpha} does not match "
                f"{policy['window_opacity']}"
            )

        rgb_map = {name: value[0] for name, value in definitions.items()}
        key = api
        if key in reference_rgb and rgb_map != reference_rgb[key]:
            errors.append(f"{theme}/{api}: RGB palette differs from other variants")
        else:
            reference_rgb.setdefault(key, rgb_map)

        for token, (_, alpha) in definitions.items():
            if not 0.0 <= alpha <= 1.0:
                errors.append(f"{theme}/{api}: {token} alpha {alpha} is outside 0.0..1.0")

        source_tokens = {
            "theme_bg_color": "base", "window_bg_color": "base",
            "theme_base_color": "surface", "view_bg_color": "surface",
            "headerbar_bg_color": "header", "popover_bg_color": "popover",
            "tooltip_bg_color": "tooltip_bg", "scrollbar_color": "scrollbar",
            "borders": "border", "disabled_bg_color": "disabled_bg",
            "input_bg_color": "input", "card_bg_color": "surface_raised",
            "dialog_bg_color": "base", "sidebar_bg_color": "surface_alt",
        }
        for css_token, source_token in source_tokens.items():
            if css_token not in definitions:
                continue
            source_value = PALETTE["dark"].get(source_token)
            if not isinstance(source_value, dict):
                errors.append(f"palette.dark.{source_token}: expected an alpha-bearing color")
                continue
            expected_alpha = policy["window_opacity"] - (
                1.0 - source_value["alpha"]
            ) * policy["multiplier"]
            actual_alpha = definitions[css_token][1]
            if abs(actual_alpha - expected_alpha) > 1e-6:
                errors.append(
                    f"{theme}/{api}: {css_token} alpha {actual_alpha} does not match "
                    f"palette policy ({expected_alpha:.4f})"
                )

        widgets_path = theme_root / api / "widgets.css"
        if widgets_path.is_file():
            widgets = re.sub(r"/\*.*?\*/", "", widgets_path.read_text(), flags=re.S)
            if re.search(r"rgba\s*\(|#[0-9a-fA-F]{8}\b", widgets):
                errors.append(
                    f"{theme}/{api}/widgets.css: inline alpha color bypasses the canonical palette"
                )

# Verify GTK4 semantic surfaces are wired to their dedicated tokens.
for theme in VARIANTS:
    gtk4 = (ROOT / "themes" / theme / "gtk-4.0" / "widgets.css").read_text()
    required_rules = {
        "dropdown input surface": (r"dropdown,\s*combobox\s*\{[^}]*background-color:\s*@input_bg_color",),
        "popover floating surface": (r"popover,\s*\.popover\s*\{[^}]*background-color:\s*@popover_bg_color",),
        "tooltip floating surface": (r"tooltip\s*\{[^}]*background-color:\s*@tooltip_bg_color",),
        "sidebar secondary surface": (r"sidebar,\s*\.sidebar,\s*\.navigation-sidebar,\s*placessidebar\s*\{[^}]*background-color:\s*@sidebar_bg_color",),
        "spinbutton input surface": (r"spinbutton\s*\{[^}]*background-color:\s*@input_bg_color",),
    }
    for label, patterns in required_rules.items():
        if not any(re.search(pattern, gtk4, re.S) for pattern in patterns):
            errors.append(f"{theme}/gtk-4.0/widgets.css: missing {label} rule")

    gtk3 = (ROOT / "themes" / theme / "gtk-3.0" / "widgets.css").read_text()
    if not re.search(r"spinbutton\s*\{[^}]*background-color:\s*@theme_base_color", gtk3, re.S):
        errors.append(f"{theme}/gtk-3.0/widgets.css: spinbutton outer surface is not defined")

# Explicitly protect intentional transparent controls and structural containers.
if PALETTE["dark"].get("button_bg") != "transparent" or PALETTE["dark"].get("button_border") != "transparent":
    errors.append("palette.dark: idle button background and border must remain transparent")

for theme in VARIANTS:
    for api in APIS:
        widgets_path = ROOT / "themes" / theme / api / "widgets.css"
        widgets = re.sub(r"/\*.*?\*/", "", widgets_path.read_text(), flags=re.S)
        button_selector = (
            r"(?m)^button,\s*\.button,\s*modelbutton\s*\{[^}]*background-color:\s*@button_bg_color"
            if api == "gtk-3.0"
            else r"(?m)^button\s*\{[^}]*background-color:\s*@button_bg_color"
        )
        if not re.search(button_selector, widgets, re.S):
            errors.append(f"{theme}/{api}/widgets.css: idle buttons must use the transparent button token")
        if re.search(r"(?m)^box\s*\{[^}]*background-color:", widgets, re.S):
            errors.append(f"{theme}/{api}/widgets.css: global GtkBox surface rule is forbidden")

    gtk3 = (ROOT / "themes" / theme / "gtk-3.0" / "widgets.css").read_text()
    if not re.search(r"spinbutton entry\s*\{[^}]*background-color:\s*transparent", gtk3, re.S):
        errors.append(f"{theme}/gtk-3.0/widgets.css: SpinButton internal entry must remain transparent")
    if not re.search(r"spinbutton button,\s*spinbutton button\.up,\s*spinbutton button\.down\s*\{[^}]*background-color:\s*transparent", gtk3, re.S):
        errors.append(f"{theme}/gtk-3.0/widgets.css: SpinButton stepper buttons must remain transparent")

    gtk4 = (ROOT / "themes" / theme / "gtk-4.0" / "widgets.css").read_text()
    if not re.search(r"spinbutton text\s*\{[^}]*background-color:\s*transparent", gtk4, re.S):
        errors.append(f"{theme}/gtk-4.0/widgets.css: SpinButton internal text must remain transparent")
    if not re.search(r"spinbutton button,\s*spinbutton button\.up,\s*spinbutton button\.down\s*\{[^}]*background-color:\s*transparent", gtk4, re.S):
        errors.append(f"{theme}/gtk-4.0/widgets.css: SpinButton stepper buttons must remain transparent")

# Check the same semantic popover token is generated consistently in both GTK APIs.
for theme in VARIANTS:
    for api in APIS:
        definitions = rgba_definitions(ROOT / "themes" / theme / api / "colors-dark.css")
        token = "popover_bg_color"
        if token not in definitions:
            errors.append(f"{theme}/{api}/colors-dark.css: missing {token}")

if errors:
    print("CambonOS theme validation: FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("CambonOS theme validation: PASSED")
print("Checked themes: " + ", ".join(THEMES))
print("Checked GTK versions: " + ", ".join(APIS))
print("Checked entry points: gtk.css and gtk-dark.css")
