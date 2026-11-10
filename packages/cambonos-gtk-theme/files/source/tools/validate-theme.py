#!/usr/bin/env python3
"""Dependency-free structural checks for the generated CambonOS GTK theme."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
THEMES = ("CambonOS", "CambonOS-dark")
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

if errors:
    print("CambonOS theme validation: FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("CambonOS theme validation: PASSED")
print("Checked themes: " + ", ".join(THEMES))
print("Checked GTK versions: " + ", ".join(APIS))
print("Checked entry points: gtk.css and gtk-dark.css")
