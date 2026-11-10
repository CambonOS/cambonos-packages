# CambonOS GTK Theme

Version **0.6.0** — single dark GTK 3, GTK 4 and Xfwm4 theme for CambonOS / XFCE.

## Theme

The project provides exactly one selectable theme: `CambonOS-dark`. Both GTK 3
and GTK 4 entry points (`gtk.css` and `gtk-dark.css`) use the same dark palette.
The theme includes Xfwm4 window decorations under the same theme name.

GTK 4 styling targets regular GTK 4 applications. Applications built with
libadwaita may supply their own styles and are not guaranteed to honor
third-party GTK themes.

## Project layout

```text
.
├── LICENSE
├── README.md
├── src/
│   └── palette.json          # canonical dark palette
├── tools/
│   ├── build-theme.py        # regenerates dark color token CSS
│   └── validate-theme.py     # validates GTK and Xfwm4 resources
└── themes/
    └── CambonOS-dark/
        ├── index.theme
        ├── gtk-3.0/
        ├── gtk-4.0/
        └── xfwm4/
```

The canonical dark color palette lives in `src/palette.json`. Both GTK entry
points import the same dark token file and their version-specific widget CSS.

## Integration in CambonOS

This directory contains the theme source payload consumed by the CambonOS package.
It is not a standalone Arch package and intentionally has no `PKGBUILD` or
`.SRCINFO`. Build and installation are managed exclusively by the package's
root-level `packages/cambonos-gtk-theme/PKGBUILD`.

The package installs only `/usr/share/themes/CambonOS-dark`.

## Select in XFCE

Select `CambonOS-dark` in **Settings → Appearance → Style** and in
**Settings → Window Manager → Style**. The existing theme name is preserved
for compatibility with CambonOS LightDM and XFCE configurations.

```bash
xfconf-query -c xsettings -p /Net/ThemeName -s CambonOS-dark
xfconf-query -c xfwm4 -p /general/theme -s CambonOS-dark
```

GTK 4 applications may choose either entry point according to their dark
appearance preference; both now resolve to the same dark styling.

## Scope and limitations

- GTK 3.24 and GTK 4 CSS; GTK 2 is not included.
- libadwaita applications may ignore third-party themes.
- Xfwm4 decorations are selected separately from the GTK application theme.
- Icon and cursor themes are provided by separate packages.

## Development validation

```bash
python tools/build-theme.py
python tools/validate-theme.py
```

Test Thunar, Mousepad, XFCE Terminal, Ristretto and XFCE Settings. Inspect
GTK Inspector's CSS errors and verify focus, selected, disabled, backdrop,
hover and pressed states.
