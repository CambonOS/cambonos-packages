# Changelog

## 0.6.2

- Improved GTK 3 TreeView checkbox contrast on selected rows and added clearer checked, unchecked, disabled and indeterminate states; strengthened GTK 3/4 checkbox borders and disabled styling.

- Explicitly assign the pan-down symbolic icon to GTK 3/4 ComboBox and GTK 4 DropDown arrow nodes so the chevron is rendered instead of relying on the node's implicit built-in image.

- Added persistent, muted chevron indicators to GTK 3 ComboBox and GTK 4 ComboBox/DropDown controls, with teal hover/focus feedback and subdued disabled states.

- Added a subtle outer border around the complete numeric stepper while keeping the individual increment/decrement button borders hidden until hover.

- Added an integrated, compact numeric stepper style for GTK 3 and GTK 4.
- Unified the spin button field and increment/decrement controls with a shared surface, subtle borders and rounded interactive buttons.
- Added restrained hover, pressed and disabled states using the CambonOS navy/teal palette.

## 0.6.1

- Fixed selected-text contrast in GTK 3 and GTK 4 by setting the canonical selected and accent foreground colors to white.
- Kept the teal selection/accent backgrounds unchanged.

## 0.6.0

- Removed the embedded PKGBUILD and .SRCINFO so the repository package has one authoritative PKGBUILD.
- Unified the Arch package and theme source release at version 0.6.0.
- Kept package construction, source generation and validation under the repository-level PKGBUILD.

## 0.5.0

- Consolidated the project to one selectable theme: `CambonOS-dark`.
- Removed the light theme directory and light palette from the build source.
- Made both GTK 3 and GTK 4 entry points use the dark palette.
- Kept the existing `CambonOS-dark` name for XFCE and LightDM compatibility.
- Updated build validation and package metadata for the single-theme layout.


## 0.4.0 (experimental)

- Applied alpha 0.88 to the main background surfaces in both light and dark palettes: base, surface, surface_alt, surface_raised, header, input and disabled_bg.
- Scaled every pre-existing alpha value proportionally by 0.88 to preserve relative opacity hierarchy.
- Kept the per-token alpha format and RGBA CSS generation introduced in 0.3.8.
- Preserved GTK3/GTK4 widget styling, spacing and Xfwm4 assets from 0.3.8-1.
- Experimental release intended for visual testing with an active XFCE compositor.

## 0.3.8

- Added optional per-token alpha support to `src/palette.json`.
- Palette colors now accept legacy strings (`#RRGGBB`, `transparent`) or `{ "color": "#RRGGBB", "alpha": 0.88 }`.
- Updated `tools/build-theme.py` to emit `rgba(r, g, b, alpha)` CSS color definitions and validate alpha values.
- Added restrained initial alpha values for popovers, tooltips, borders and scrollbars in light/dark palettes.
- Kept existing palette entries and CSS generation backward-compatible.
- Preserved GTK3/GTK4 widget styling, form spacing and Xfwm4 assets from 0.3.7-1.

# Changelog

## 0.3.7

- Added external margins (3px vertical, 4px horizontal) to GTK3/GTK4 text inputs to separate fields from adjacent controls and parent layout edges.
- Added matching outer spacing to spin buttons and combo/dropdown controls.
- Added search-entry container spacing while resetting margins on embedded entry children to prevent double gaps.
- Preserved 0.3.6 inner text padding (6px vertical, 9px horizontal).
- Preserved 0.3.5 slider/switch spacing and the functional Xfwm4 assets from 0.3.3-1.
- Applied consistently to CambonOS light/dark variants.

# Changelog

## 0.3.6

- Increased horizontal and vertical inner padding for GTK3 text entries to 9px and 6px respectively.
- Applied matching 6px vertical / 9px horizontal padding to GTK4 entries, search/password entries and spin buttons.
- Improved text inset in GTK4 text views.
- Applied the input-spacing adjustments to light and dark variants.
- Preserved all 0.3.5-1 slider, switch, checkbox and radio spacing improvements.
- Preserved the functional Xfwm4 assets from 0.3.3-1.

# Changelog

## 0.3.5

- Added 10px end margins to horizontal GtkScale troughs to keep the handle clear of endpoint labels at minimum and maximum values.
- Added 10px end margins to vertical GtkScale troughs for consistent endpoint clearance.
- Added 8px trailing margin and 2px vertical margins to boolean switches so they no longer touch container borders.
- Applied the adjustments to GTK3/GTK4 and both light/dark variants.
- Preserved checkbox/radio sizing and spacing from 0.3.4.
- Preserved all Xfwm4 assets and application-menu icon behavior from 0.3.3-1.

# Changelog

## 0.3.4

- Improved GTK3/GTK4 checkbox and radio indicator spacing with a 7px label gap.
- Reduced scale slider handles from 14px to 12px and slimmed their border from 2px to 1px.
- Normalized switch dimensions and reduced the internal slider footprint.
- Compactified spinbutton sub-controls and expander arrows where supported.
- Applied the same interaction sizing to CambonOS light and dark variants.
- Preserved the 0.3.3-1 Xfwm4 assets and application-menu icon behavior.

# Changelog

## 0.3.3

- Refined Xfwm4 application-menu button assets to 16x22 pixels to reduce the application icon footprint.
- Kept menu pixmaps opaque and matched their idle colors to the active/inactive titlebar surfaces for a transparent visual appearance.
- Preserved muted teal hover and primary teal pressed states without decorative glyphs.
- Applied the updated assets to both light and dark variants.
- Added a validator check for the expected menu pixmap dimensions.


## 0.3.2

- Fixed Xfwm4 application menu icon rendering when `show_app_icon=true`.
- Replaced transparent idle menu XPMs with opaque titlebar-colored assets.
- Removed the three-dot glyph from all menu button states so the application icon can occupy the menu button area.
- Kept muted teal hover and primary teal pressed backgrounds.
- Applied the correction to light and dark variants.


## 0.3.1

- Fixed upper Xfwm4 window corners: top-left/top-right XPM assets now span the full 30px titlebar height.
- Made top-corner tiles fully opaque to prevent unpainted/black gaps in the frame compositor.
- Added a validator invariant requiring top-corner height to match the titlebar tile height.
- Applied the fix to CambonOS and CambonOS-dark, active and inactive states.


## 0.3.0

- Added initial Xfwm4 window-decoration themes for CambonOS light and dark.
- Added XPM titlebar segments, frame edges/corners and action-button states.
- Added `themerc` configuration with matching title colors, spacing and frame shadows.
- Added a compatibility/completeness document.
- Expanded structural validation to cover Xfwm4 assets.
- Fixed malformed GTK4 focus selectors discovered during the compatibility audit.
- Tuned Xfwm4 active title surfaces to align with GTK headerbar colors.


## 0.2.2

- Fixed the XFCE/Whisker Menu interaction styling in both light and dark theme variants.
- Removed idle borders completely from Whisker category radio buttons and command buttons.
- Added explicit selectors for Whisker Menu's `box.categories > button.radio` widget structure.
- Kept muted teal hover borders and the primary teal selected state.
- Synchronized GTK widget styles between light and dark variants; palette tokens remain separate.


## 0.2.1

- Changed ordinary button styling to transparent idle, muted teal hover and teal selected states.
- Applied matching interaction states to XFCE panel buttons, tasklist buttons, Whisker Menu categories/commands and workspace switcher.
- Kept suggested and destructive actions visually distinct.
- Added dedicated palette tokens for button idle, hover and selected backgrounds/borders.


## 0.2.0

- Reorganized the theme into independently selectable light and dark variants.
- Added `gtk.css` and `gtk-dark.css` entry points for GTK 3 and GTK 4.
- Centralized the canonical palette in `src/palette.json`.
- Added `tools/build-theme.py` to regenerate color-token stylesheets.
- Expanded GTK 3 and GTK 4 widget coverage.
- Replaced broad selection styling with more specific widget selectors.
- Added derived surface, text, border, focus, disabled and hover colors.
- Improved theme metadata and Arch package documentation.
- Clarified GTK 4/libadwaita and XFCE/Xfwm4 scope limitations.

## 0.1.0

- Initial GTK 3 and GTK 4 light/dark theme skeleton.
