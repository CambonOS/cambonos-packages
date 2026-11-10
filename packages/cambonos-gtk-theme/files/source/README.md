# CambonOS GTK Theme

Version **0.4.0** — original GTK 3 and GTK 4 theme for CambonOS / XFCE.

## Theme variants

- `CambonOS`: light default variant, with a dark GTK variant available.
- `CambonOS-dark`: dark default variant.

Both theme directories include GTK 3 and GTK 4 stylesheets. The GTK 4 styles target
regular GTK 4 applications. Applications built with libadwaita may supply their own
styles and are not guaranteed to honor third-party GTK themes.

## Project layout

```text
.
├── PKGBUILD
├── LICENSE
├── README.md
├── src/
│   └── palette.json          # canonical palette source
├── tools/
│   └── build-theme.py        # regenerates color token CSS
└── themes/
    ├── CambonOS/
    │   ├── index.theme
    │   ├── gtk-3.0/
    │   └── gtk-4.0/
    └── CambonOS-dark/
        ├── index.theme
        ├── gtk-3.0/
        └── gtk-4.0/
```

Each GTK version has separate `gtk.css` and `gtk-dark.css` entry points. They
import a mode-specific token file and a version-specific widget stylesheet. The
light theme's `gtk-dark.css` supplies its dark appearance; the dark theme uses
the dark token set for both entry points.
The canonical color palette lives in `src/palette.json`.

## Experimental translucent surfaces (0.4.0)

This test release applies `alpha: 0.88` to the main background surfaces
(`base`, `surface`, `surface_alt`, `surface_raised`, `header`, `input` and
`disabled_bg`) in both light and dark palettes. Existing alpha values for
borders, popovers, tooltips and scrollbars are scaled proportionally by 0.88.
Actual translucency depends on GTK support and the desktop compositor; this
does not make the entire application window translucent.

After editing the palette, regenerate token files with:

```bash
python tools/build-theme.py
```

## Install on Arch Linux

Build and install:

```bash
makepkg -si
```

Install a previously built package:

```bash
sudo pacman -U cambonos-gtk-theme-0.3.8-1-any.pkg.tar.zst
```

The package installs both theme directories under `/usr/share/themes/`.

## Select in XFCE

Open **Settings → Appearance → Style** and select `CambonOS` or `CambonOS-dark`.

From the command line:

```bash
xfconf-query -c xsettings -p /Net/ThemeName -s CambonOS
# or
xfconf-query -c xsettings -p /Net/ThemeName -s CambonOS-dark
```

For GTK 4, the theme loader selects `gtk.css` or `gtk-dark.css` according to the
application's dark preference. The exact preference mechanism depends on the
GTK version and desktop integration. This is separate from choosing the theme
name in XFCE.

## Interaction states

Ordinary buttons use a three-state visual language:

- Idle: transparent background and border.
- Hover: a subdued teal surface and border.
- Checked/selected: the primary CambonOS teal (`#019FA7`) for both background and border.

The same interaction language is explicitly applied to XFCE panel buttons, tasklist
buttons, Whisker Menu category radio buttons/commands and the workspace switcher.
Whisker category and command buttons remove their idle border completely. Suggested and
destructive action buttons remain visually distinct.

## Palette

| Token | Light | Dark |
|---|---|---|
| Base | `#F7F5EC` | `#061C31` |
| Primary | `#019FA7` | `#019FA7` |
| Highlight | `#70E7E6` | `#70E7E6` |
| Main text | `#183344` | `#E7F0EF` |
| Secondary text | `#52636B` | `#A9BEC4` |
| Border | `#D5DED9` | `#244457` |

The highlight cyan is intentionally reserved for dark surfaces and small graphic
accents. On the light base it does not provide sufficient contrast for normal
text or essential control boundaries. Light-mode focus and link states therefore
use a darker derived teal (`#007F87`).

## Xfwm4 window decorations

Both theme variants include an initial `xfwm4/` theme with XPM frame assets,
titlebar segments, and active/inactive/prelight/pressed button states. Select
the matching decoration separately in **Settings → Window Manager → Style**.

Command line:

```bash
xfconf-query -c xfwm4 -p /general/theme -s CambonOS-dark
```

This first Xfwm4 implementation is structurally validated but requires visual
testing against the Xfwm4 version shipped by CambonOS.

## Scope and limitations

- GTK 3.24 and GTK 4 CSS; GTK 2 is not included.
- GTK 4 styling targets regular GTK 4 applications. libadwaita applications may
  ignore third-party themes.
- Xfwm4 window decorations are included as an initial separate component. GTK themes style client content; XFCE window decorations are selected separately in **Settings → Window Manager**.
- Icon and cursor themes are not included.
- CSS selectors and properties require runtime validation against the exact GTK
  versions shipped by CambonOS.

## Development validation

The included `tools/build-theme.py` regenerates the derived color-token files
from `src/palette.json`; it does not require a preprocessor at runtime.

Recommended local checks on an Arch/XFCE test system:

```bash
makepkg -f
GTK_DEBUG=interactive gtk3-widget-factory
GTK_DEBUG=interactive gtk4-widget-factory
```

Also test Thunar, Mousepad, XFCE Terminal, Ristretto and XFCE Settings. Inspect
GTK Inspector's CSS errors and verify focus, selected, disabled, backdrop,
hover and pressed states.


### Xfwm4 application menu icon

The `menu-*.xpm` assets use a 16x22 opaque color-matched area. The matching
titlebar color makes the idle button appear transparent while preserving the
application icon compositing performed by Xfwm4. Hover and pressed states use
the CambonOS muted and primary teal colors.


## Palette alpha support (0.3.8)

`src/palette.json` accepts both the original string format and an optional
per-token alpha object:

```json
{
  "popover": {
    "color": "#0B2940",
    "alpha": 0.94
  }
}
```

The theme builder converts this to `rgba(11, 41, 64, 0.94)` in the generated
GTK3/GTK4 color-token CSS. Existing plain values such as `"#061C31"` and
`"transparent"` remain supported. Alpha must be numeric and between `0.0`
and `1.0`.

Regenerate generated color CSS after editing the palette:

```bash
python tools/build-theme.py
```
