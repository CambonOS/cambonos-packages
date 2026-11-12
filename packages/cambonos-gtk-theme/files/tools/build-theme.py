#!/usr/bin/env python3
"""Build the three CambonOS GTK/Xfwm4 themes from one canonical template.

The alpha value in palette.json is a relative transparency weight:
1.0 means that a token follows the variant's window opacity; lower values
make auxiliary surfaces progressively more transparent.

For each token:
    output_alpha = window_opacity - (1 - source_alpha) * multiplier

This keeps the selected window opacity exact while scaling each token's
additional transparency by the configured multiplier.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE = json.loads((ROOT / "src/palette.json").read_text())
TEMPLATE_NAME = "CambonOS-dark"
THEME_ROOT = ROOT / "themes"

VARIANTS = {
    "Conservative": {
        "window_opacity": 0.98,
        "multiplier": 1,
    },
    "Balanced": {
        "window_opacity": 0.88,
        "multiplier": 5,
    },
    "Transparent": {
        "window_opacity": 0.78,
        "multiplier": 10,
    },
}

GTK3_NAMES = {
    "theme_bg_color": "base", "theme_fg_color": "text",
    "theme_base_color": "surface", "theme_text_color": "text",
    "theme_selected_bg_color": "accent", "theme_selected_fg_color": "selected_fg",
    "theme_unfocused_bg_color": "surface_alt", "theme_unfocused_fg_color": "text_muted",
    "theme_unfocused_base_color": "surface", "theme_unfocused_text_color": "text",
    "borders": "border", "accent": "accent", "accent_fg_color": "accent_fg",
    "accent_emphasis": "highlight", "success_color": "success",
    "warning_color": "warning", "error_color": "error", "link_color": "link",
}
GTK4_NAMES = {
    "window_bg_color": "base", "window_fg_color": "text",
    "view_bg_color": "surface", "view_fg_color": "text",
    "headerbar_bg_color": "header", "headerbar_fg_color": "text",
    "card_bg_color": "surface_raised", "card_fg_color": "text",
    "popover_bg_color": "popover", "popover_fg_color": "text",
    "dialog_bg_color": "base", "dialog_fg_color": "text",
    "accent_bg_color": "accent", "accent_fg_color": "accent_fg",
    "borders": "border", "accent_color": "accent", "accent_emphasis": "highlight",
    "success_color": "success", "warning_color": "warning", "error_color": "error",
}
EXTRA = {
    "gtk-3.0": {
        "headerbar_bg_color": "header", "button_bg_color": "button_bg",
        "button_border_color": "button_border", "button_hover_bg_color": "button_hover",
        "button_hover_border_color": "button_hover_border",
        "button_selected_bg_color": "button_selected",
        "button_selected_border_color": "button_selected_border", "disabled_fg_color": "text_disabled",
        "disabled_bg_color": "disabled_bg", "focus_color": "focus",
        "accent_hover_color": "accent_hover", "accent_pressed_color": "accent_pressed",
        "destructive_color": "destructive", "switch_off_bg_color": "switch_off",
        "switch_slider_color": "switch_slider", "trough_color": "trough",
        "popover_bg_color": "popover", "menu_hover_bg_color": "menu_hover",
        "tooltip_bg_color": "tooltip_bg", "tooltip_fg_color": "tooltip_fg",
        "surface_hover_color": "surface_hover", "scrollbar_color": "scrollbar",
        "scrollbar_hover_color": "scrollbar_hover", "accent_soft_color": "accent_soft",
    },
    "gtk-4.0": {
        "button_fg_color": "text", "button_bg_color": "button_bg",
        "button_border_color": "button_border", "button_hover_bg_color": "button_hover",
        "button_hover_border_color": "button_hover_border",
        "button_selected_bg_color": "button_selected",
        "button_selected_border_color": "button_selected_border", "disabled_fg_color": "text_disabled",
        "disabled_bg_color": "disabled_bg", "focus_color": "focus",
        "accent_hover_color": "accent_hover", "accent_pressed_color": "accent_pressed",
        "destructive_color": "destructive", "input_bg_color": "input",
        "switch_off_bg_color": "switch_off", "switch_slider_color": "switch_slider",
        "trough_color": "trough", "text_muted_color": "text_muted",
        "surface_hover_color": "surface_hover", "menu_hover_bg_color": "menu_hover",
        "scrollbar_color": "scrollbar", "scrollbar_hover_color": "scrollbar_hover",
        "link_color": "link", "sidebar_bg_color": "surface_alt",
        "tooltip_bg_color": "tooltip_bg", "tooltip_fg_color": "tooltip_fg",
    },
}
HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def output_alpha(source_alpha: float, variant: dict) -> float:
    """Scale additional token transparency while preserving window opacity."""
    return variant["window_opacity"] - (1.0 - source_alpha) * variant["multiplier"]


def css_color(value, token_name="", variant=None):
    """Validate and render a palette value as a CSS color."""
    if isinstance(value, str):
        if value == "transparent":
            return value
        if not HEX_RE.fullmatch(value):
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
    if variant is not None:
        alpha = output_alpha(float(alpha), variant)
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(
                f"{token_name}: generated alpha {alpha:.4f} is outside 0.0..1.0 "
                f"for {variant['name']}"
            )
    rgb = tuple(int(match.group(1)[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha:g})"


def token_css(mode, api, variant):
    names = GTK3_NAMES if api == "gtk-3.0" else GTK4_NAMES
    lines = [
        "/* Generated from src/palette.json by tools/build-theme.py; do not edit. */",
        f"/* Variant: {variant['name']} ({variant['window_opacity']:.0%} window opacity). */",
    ]
    for name, token in list(names.items()) + list(EXTRA[api].items()):
        lines.append(
            f"@define-color {name} {css_color(PALETTE[mode][token], token, variant)};"
        )
    return "\n".join(lines) + "\n"


def validate_source():
    if set(PALETTE) != {"dark"}:
        raise ValueError("palette.json must define exactly the canonical 'dark' palette")
    for mode, tokens in PALETTE.items():
        for token, value in tokens.items():
            # Validate source syntax before calculating any variant.
            css_color(value, f"{mode}.{token}")
    for name, variant in VARIANTS.items():
        variant["name"] = name
        opacity = variant["window_opacity"]
        multiplier = variant["multiplier"]
        if not isinstance(opacity, (int, float)) or not 0 < opacity <= 1:
            raise ValueError(f"{name}: window_opacity must be between 0 and 1")
        if isinstance(multiplier, bool) or not isinstance(multiplier, int) or multiplier < 1:
            raise ValueError(f"{name}: multiplier must be a positive integer")
        for token, value in PALETTE["dark"].items():
            if isinstance(value, dict):
                alpha = output_alpha(value["alpha"], variant)
                if not 0 <= alpha <= 1:
                    raise ValueError(
                        f"{name}.{token}: generated alpha {alpha:.4f} is outside 0.0..1.0"
                    )


def set_theme_metadata(theme_dir: Path, theme_name: str, comment: str) -> None:
    index_path = theme_dir / "index.theme"
    index = index_path.read_text()
    replacements = {
        r"(?m)^Name=.*$": f"Name={theme_name}",
        r"(?m)^GtkTheme=.*$": f"GtkTheme={theme_name}",
        r"(?m)^MetacityTheme=.*$": f"MetacityTheme={theme_name}",
        r"(?m)^Comment=.*$": f"Comment={comment}",
    }
    for pattern, value in replacements.items():
        if re.search(pattern, index):
            index = re.sub(pattern, value, index)
        elif pattern.startswith(r"(?m)^Comment"):
            index = index.rstrip() + f"\n{value}\n"
        else:
            raise ValueError(f"{theme_name}/index.theme: missing metadata field {pattern}")
    index_path.write_text(index)


def write_theme_colors(theme_dir: Path, variant: dict) -> None:
    for api in ("gtk-3.0", "gtk-4.0"):
        (theme_dir / api / "colors-dark.css").write_text(
            token_css("dark", api, variant)
        )


def write_themes():
    """Generate the default Conservative theme and named alternatives."""
    template = THEME_ROOT / TEMPLATE_NAME
    if not template.is_dir():
        raise FileNotFoundError(f"Missing canonical theme template: {template}")

    conservative = dict(VARIANTS["Conservative"], name="Conservative")
    # Keep the established CambonOS-dark name as the default Conservative theme.
    set_theme_metadata(
        template,
        TEMPLATE_NAME,
        "CambonOS dark theme (conservative transparency)",
    )
    write_theme_colors(template, conservative)

    for name, variant in VARIANTS.items():
        if name == "Conservative":
            continue
        theme_name = f"{TEMPLATE_NAME}-{name}"
        destination = THEME_ROOT / theme_name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(template, destination)
        set_theme_metadata(
            destination,
            theme_name,
            f"CambonOS dark theme ({'high' if name == 'Transparent' else name.lower()} transparency)",
        )
        write_theme_colors(destination, dict(variant, name=name))


def main():
    validate_source()
    write_themes()
    for name, variant in VARIANTS.items():
        theme_name = TEMPLATE_NAME if name == "Conservative" else f"{TEMPLATE_NAME}-{name}"
        print(
            f"Generated {theme_name}: "
            f"window opacity {variant['window_opacity']:.0%}, "
            f"transparency multiplier {variant['multiplier']}"
        )


if __name__ == "__main__":
    main()
