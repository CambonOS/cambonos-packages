#!/usr/bin/env python3
"""Generate CambonOS GTK color-token CSS from the canonical palette.

Palette values may be plain CSS colors (legacy format) or objects:
    {"color": "#RRGGBB", "alpha": 0.88}
The latter are emitted as rgba(r, g, b, alpha).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE = json.loads((ROOT / "src/palette.json").read_text())

GTK3_NAMES = {
    "theme_bg_color":"base", "theme_fg_color":"text",
    "theme_base_color":"surface", "theme_text_color":"text",
    "theme_selected_bg_color":"accent", "theme_selected_fg_color":"selected_fg",
    "theme_unfocused_bg_color":"surface_alt", "theme_unfocused_fg_color":"text_muted",
    "theme_unfocused_base_color":"surface", "theme_unfocused_text_color":"text",
    "borders":"border", "accent":"accent", "accent_fg_color":"accent_fg",
    "accent_emphasis":"highlight", "success_color":"success",
    "warning_color":"warning", "error_color":"error", "link_color":"link",
}
GTK4_NAMES = {
    "window_bg_color":"base", "window_fg_color":"text",
    "view_bg_color":"surface", "view_fg_color":"text",
    "headerbar_bg_color":"header", "headerbar_fg_color":"text",
    "card_bg_color":"surface_raised", "card_fg_color":"text",
    "popover_bg_color":"popover", "popover_fg_color":"text",
    "dialog_bg_color":"base", "dialog_fg_color":"text",
    "accent_bg_color":"accent", "accent_fg_color":"accent_fg",
    "borders":"border", "accent_color":"accent", "accent_emphasis":"highlight",
    "success_color":"success", "warning_color":"warning", "error_color":"error",
}
EXTRA = {
    "gtk-3.0": {
        "headerbar_bg_color":"header", "button_bg_color":"button_bg",
        "button_border_color":"button_border", "button_hover_bg_color":"button_hover",
        "button_hover_border_color":"button_hover_border",
        "button_selected_bg_color":"button_selected",
        "button_selected_border_color":"button_selected_border", "disabled_fg_color":"text_disabled",
        "disabled_bg_color":"disabled_bg", "focus_color":"focus",
        "accent_hover_color":"accent_hover", "accent_pressed_color":"accent_pressed",
        "destructive_color":"destructive", "switch_off_bg_color":"switch_off",
        "switch_slider_color":"switch_slider", "trough_color":"trough",
        "popover_bg_color":"popover", "menu_hover_bg_color":"menu_hover",
        "tooltip_bg_color":"tooltip_bg", "tooltip_fg_color":"tooltip_fg",
        "surface_hover_color":"surface_hover", "scrollbar_color":"scrollbar",
        "scrollbar_hover_color":"scrollbar_hover", "accent_soft_color":"accent_soft",
    },
    "gtk-4.0": {
        "button_fg_color":"text", "button_bg_color":"button_bg",
        "button_border_color":"button_border", "button_hover_bg_color":"button_hover",
        "button_hover_border_color":"button_hover_border",
        "button_selected_bg_color":"button_selected",
        "button_selected_border_color":"button_selected_border", "disabled_fg_color":"text_disabled",
        "disabled_bg_color":"disabled_bg", "focus_color":"focus",
        "accent_hover_color":"accent_hover", "destructive_color":"destructive",
        "input_bg_color":"input", "switch_off_bg_color":"switch_off",
        "switch_slider_color":"switch_slider", "trough_color":"trough",
        "text_muted_color":"text_muted", "surface_hover_color":"surface_hover",
        "menu_hover_bg_color":"menu_hover", "scrollbar_color":"scrollbar",
        "scrollbar_hover_color":"scrollbar_hover", "link_color":"link",
    },
}

HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")

def css_color(value, token_name=""):
    """Return a CSS color string, validating optional per-token alpha."""
    if isinstance(value, str):
        if value == "transparent":
            return value
        if not value.startswith("#"):
            raise ValueError(f"{token_name}: unsupported color value {value!r}")
        return value
    if not isinstance(value, dict) or set(value) != {"color", "alpha"}:
        raise ValueError(f"{token_name}: expected '#RRGGBB' or {{'color','alpha'}}")
    color = value["color"]
    alpha = value["alpha"]
    match = HEX_RE.fullmatch(color) if isinstance(color, str) else None
    if not match:
        raise ValueError(f"{token_name}: color must be #RRGGBB")
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not 0 <= alpha <= 1:
        raise ValueError(f"{token_name}: alpha must be a number between 0.0 and 1.0")
    rgb = tuple(int(match.group(1)[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha:g})"

def token_css(mode, api):
    names = GTK3_NAMES if api == "gtk-3.0" else GTK4_NAMES
    lines = ["/* Generated from src/palette.json; do not edit by hand. */"]
    for name, token in list(names.items()) + list(EXTRA[api].items()):
        lines.append(f"@define-color {name} {css_color(PALETTE[mode][token], token)};")
    return "\n".join(lines) + "\n"

# Validate every palette entry, including tokens not currently exported to GTK.
for mode, tokens in PALETTE.items():
    for token, value in tokens.items():
        css_color(value, f"{mode}.{token}")

for theme, default_mode in (("CambonOS", "light"), ("CambonOS-dark", "dark")):
    for api in ("gtk-3.0", "gtk-4.0"):
        for filename, mode in (("gtk.css", default_mode), ("gtk-dark.css", "dark")):
            if theme == "CambonOS-dark":
                mode = "dark"
            (ROOT / "themes" / theme / api / f"colors-{mode}.css").write_text(token_css(mode, api))
