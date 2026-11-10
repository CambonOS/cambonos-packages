# CambonOS theme completeness and compatibility

## Included

- One selectable dark theme: `CambonOS-dark`.
- GTK 3 and GTK 4 dark CSS entry points for regular GTK applications.
- XFCE panel and Whisker Menu interaction styling through GTK 3 CSS.
- Xfwm4 window-decoration assets under the same theme name.

## Not included / limitations

- GTK 2: legacy applications require a separate `gtk-2.0/gtkrc` implementation.
- libadwaita: applications can enforce their own appearance and are not guaranteed to follow third-party themes.
- Xfwm4 runtime validation: XPM assets and `themerc` are structurally checked, but still need visual testing on the target XFCE/Xfwm4 release.
- Icon theme and cursor theme: separate packages/components.
- Qt application theme: requires a separate Qt/Kvantum or platform-theme solution.
- XFCE sound theme, wallpapers, greeter, lock screen and login/session artwork: separate desktop integration work.

## Recommended validation

1. Select `CambonOS-dark` in Appearance > Style.
2. Select `CambonOS-dark` in Window Manager > Style.
3. Test normal, focused and unfocused windows; maximize/restore; minimize; close; shade; stick; resizing and tiled windows.
4. Test panel, Whisker Menu and GTK 3 apps at the desktop's normal scale.
5. Inspect GTK 4 apps separately; test libadwaita apps as a documented exception.

A complete GTK theme does not need to include icon, cursor, Qt or sound themes.
Those are separate components of a coherent desktop theme bundle.
