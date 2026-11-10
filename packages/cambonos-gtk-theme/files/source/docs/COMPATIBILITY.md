# CambonOS theme completeness and compatibility

## Included in the 0.3.0 package

- GTK 3 theme CSS and light/dark color variants.
- GTK 4 theme CSS and light/dark color variants for regular GTK 4 applications.
- XFCE panel and Whisker Menu interaction styling through GTK 3 CSS.
- Initial Xfwm4 window-decoration theme for both light and dark variants.

## Not included yet

- GTK 2: legacy applications require a separate `gtk-2.0/gtkrc` implementation.
- libadwaita: applications can enforce their own appearance and are not guaranteed to follow third-party GTK themes.
- Xfwm4 runtime validation: XPM assets and `themerc` are structurally checked, but still need visual testing on the target XFCE/Xfwm4 release.
- Icon theme and cursor theme: separate packages/components.
- Qt application theme: requires a separate Qt/Kvantum or platform-theme solution.
- XFCE sound theme, wallpapers, greeter, lock screen and login/session artwork: separate desktop integration work.
- High-DPI/4K Xfwm4 assets: first pass uses standard XPM assets and does not yet provide Xfwm 4.20 `-stretch` variants.

## Recommended next validation

1. Select `CambonOS-dark` in Appearance > Style.
2. Select `CambonOS-dark` in Window Manager > Style.
3. Test normal, focused and unfocused windows; maximize/restore; minimize; close; shade; stick; resizing and tiled windows.
4. Test panel, Whisker Menu and GTK 3 apps at the desktop's normal scale.
5. Inspect GTK 4 apps separately; test libadwaita apps as a documented exception.
6. Repeat with `CambonOS` light.

A complete *GTK theme* does not need to include icon, cursor, Qt or sound themes. Those are separate components of a coherent desktop theme bundle.
