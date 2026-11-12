# CambonOS GTK Theme — Opacity Policy

This package generates three GTK theme profiles from one canonical palette.

## Profiles

| Theme | Window opacity | Transparency multiplier |
|---|---:|---:|
| `CambonOS-dark` | 98% | 1 |
| `CambonOS-dark-balanced` | 88% | 5 |
| `CambonOS-dark-transparent` | 78% | 10 |

The base `CambonOS-dark` theme is the Conservative profile and preserves the
historical default theme name. The other profiles are generated alternatives.

## Surface policy

- Main windows and primary content/input surfaces use the profile's window
  opacity.
- Secondary and floating surfaces use their semantic palette tokens and are
  transformed by the profile multiplier.
- Text, icons, accents, and functional indicators remain opaque unless a
  specific design token states otherwise.
- Flat buttons and structural GTK containers remain transparent where their
  parent provides the visible surface.
- Internal nodes such as `GtkBox` children must not receive a global background
  merely because GTK Inspector reports a transparent computed background.
- Popovers, menus, and tooltips are independent floating surfaces.
- XFWM4 shadow opacity is independent from GTK widget background alpha.

## Implementation rules

All generated alpha values originate in `files/src/palette.json` and are
transformed by `files/tools/build-theme.py`. GTK stylesheets must consume
generated palette tokens rather than introducing ad-hoc RGBA values.

The validator checks generated theme structure, profile output, and the
documented transparency exceptions. GTK's runtime widget tree remains
context-dependent: a transparent structural node is valid when it inherits
the intended visible surface from its parent.
