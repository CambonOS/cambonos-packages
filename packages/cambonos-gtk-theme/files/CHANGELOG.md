## 0.9.7

- Expanded drag-selection rubberband selectors to cover XFCE desktop icon views, Thunar content views and GTK tree/flow/grid/column views while retaining the CambonOS teal at 22% fill alpha and a solid teal outline.
- Removed the Thunar-specific rubberband selector and standardized GTK 3/GTK 4 drag-selection styling on the generic `rubberband` CSS node, using the primary teal accent at 22% fill alpha with a solid teal outline.
- Added the same state-aware `GtkSpinner` styling to GTK 4 as GTK 3: hidden while idle and visible with continuous rotation only while `:checked`, using GTK 4's equivalent `@accent_color` token.
- Aligned GTK 4 grid-item selection and drag-selection rubberband with GTK 3's icon-view treatment: light teal (`#70E7E6`) fill, dark readable text and a primary-teal (`#019FA7`) outline.
- Extended theme validation to require matching spinner lifecycle and animation behavior in both GTK stylesheets.

## 0.9.6

- Restored GTK 3 `GtkSpinner` state handling: the indicator is hidden while idle and appears with a continuous rotation only while the widget is active (`:checked`).
- Styled the active spinner with the theme highlight color without changing Thunar behavior or GTK 4 styling.

## 0.9.5

- Improved GTK 3 Thunar icon selection visibility with the light teal highlight (`#70E7E6`) and dark foreground (`#061C31`), matching the desktop rubberband appearance while preserving legibility.
- Scoped the drag-selection rectangle styling to the `iconview.view rubberband` CSS node so it remains distinct from selected icon tiles.

# Changelog

## 0.9.4

- Increased GTK 3 drag-selection rubberband visibility over dark Thunar surfaces by using the lighter highlight teal (`#70E7E6`) at 45% opacity, while retaining the primary teal outline (`#019FA7`).
- Kept GTK 4, individual item selection, popup-menu hover and the global palette unchanged.

## 0.9.3

- Corrected the GTK 3 drag-selection rubberband to use the CambonOS teal accent (`#019FA7`) instead of the dark general selected-background token.
- Kept the existing 22% translucent fill and 1 px teal border; GTK 4 already uses the accent and remains unchanged.

## 0.9.2

- Improved GTK 3/GTK 4 drag-selection rubberband visibility in icon views with a translucent CambonOS teal fill and a clear teal border.
- Kept individual item selection, menu hover, primary accent and other palette states unchanged.

## 0.9.1

- Darkened the GTK 3/GTK 4 popup-menu hover and selected-item background to `#176F78` for readable white labels.
- Kept the primary accent, focus, link and scrollbar colors unchanged; the menu-specific color is controlled by the canonical palette token.

## 0.8.1

- Retuned inactive Xfwm4 title accents to use muted CambonOS teal `#397B82`, while preserving the active teal `#019FA7`, navy surfaces, title geometry and accent thickness.
- Applied the inactive title accent consistently to all five title segments (`title-1` through `title-5`) in the canonical theme template; generated variants inherit the same assets.
- Corrected theme variant identifiers and package-version references in the package documentation.
- Updated the functional checklist to cover all three installed variants and the active/inactive Xfwm4 title accent; visual verification remains pending on a real XFCE session.

## 0.8.0

- Replaced the single installed dark theme with Conservative (98%), Balanced (88%) and Transparent (78%) profiles generated from one canonical palette and theme template.
- Added a shared opacity policy with per-variant multipliers 1, 5 and 10; auxiliary surfaces retain additional transparency relative to the window background.
- Kept RGB colors, typography, widget styling and Xfwm4 assets identical across variants; Xfwm4 shadow opacity remains independent from GTK alpha.
- Extended the builder to generate complete GTK 3, GTK 4 and Xfwm4 theme directories and unique theme metadata.
- Extended validation to check all generated variants, window opacity targets, RGBA ranges, RGB consistency and absence of inline alpha colors in widget stylesheets.
- Updated the Arch package to install all three generated themes.


## 0.6.2

- Added explicit symbolic glyphs for checked, radio-selected and indeterminate GTK 3 indicators; removed hover/selected indicator fills that forced unchecked menu indicators to white.

- Removed the unnecessary GTK 3 `menu` ancestor from menu check/radio selectors so indicators are styled across different GtkCheckMenuItem menu-shell hierarchies, including Thunar and Xfwm4.

- Strengthened GTK 3 popup-menu indicator selectors for left/right check and radio nodes, including Xfwm4 draw-as-radio check menu items; increased GTK 4 menu model-button selector coverage.

- Applied the accessible checkbox/radio contrast and state styling to GTK 3 menu items and GTK 4 model buttons, including checked, hover/selected, disabled and indeterminate states.

- Added direction-aware spacing between check/radio indicators and menu labels in GTK 3 and GTK 4.

- Redesigned all Xfwm4 titlebar button XPMs in the CambonOS navy/teal palette and made every button-state pixel opaque so the full icon canvas remains an input target.

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
