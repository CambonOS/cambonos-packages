# cambonos-gtk-theme

Tema oscuro de CambonOS para GTK 2, GTK 3, GTK 4 y decoraciones XFWM4.

## Variante incluida

- `CambonOS-Dark`: tema oscuro basado en Orchis, refinado con la paleta oficial de CambonOS.

El paquete instala el tema en `/usr/share/themes/CambonOS-Dark`. No selecciona
el tema automáticamente, no modifica preferencias del usuario, no instala
configuración global de GTK y no incorpora scripts de instalación ni hooks
ALPM.

## Integración con XFCE

La hoja GTK 3 incluye ajustes visuales para Whisker Menu y el diálogo de cierre
de sesión de XFCE. Whisker utiliza superficies con distintos niveles de
transparencia: las categorías son más transparentes que la lista de
aplicaciones y el campo de búsqueda. El diálogo de cierre de sesión utiliza la
paleta CambonOS y un fondo ligeramente translúcido. La transparencia efectiva
depende de la composición habilitada en XFCE y del soporte del compositor.

## GTK y libadwaita

GTK 2/3/4 consumen los recursos de sus respectivos directorios. La presencia de `gtk-4.0` no implica que las aplicaciones libadwaita
respeten el tema GTK: libadwaita mantiene su propio sistema visual. La
compatibilidad `supported` significa que el paquete no interfiere con sus
preferencias oficiales de esquema/acento; las aplicaciones pueden adoptar el
modo oscuro y los acentos que ofrezcan el escritorio y el portal. No se
garantiza una tematización completa ni un acento HEX personalizado. El paquete
no enlaza archivos en `~/.config/gtk-4.0`, no modifica preferencias y no
inyecta CSS en libadwaita.

## Procedencia

Recursos derivados de Orchis upstream, revisión
`a4c48a425e63808345e824495964bd9c2f462e04`, a partir del payload
`release/Orchis-Green.tar.xz` (`Orchis-Green-Dark`). Los cambios de paleta
CambonOS están aplicados sobre los recursos generados. Se conserva el texto
de licencia upstream en `LICENSE`.

## Instalación y activación

Instala el paquete y selecciona `CambonOS-Dark` desde la herramienta de
apariencia del escritorio. La selección no se realiza automáticamente.

## Limitaciones

- Qt no está incluido; se tratará en un paquete independiente.
- La integración libadwaita es `supported`, no una tematización completa ni
  una garantía de que todas las aplicaciones libadwaita adopten los colores.
- La validación visual debe realizarse en una sesión XFCE real.

### GTK3 interaction and XFCE logout styling

The GTK3 stylesheets use CambonOS teal (`#006B73`) for pointer-hover and
selection states on selectable rows, including Whisker Menu entries. The XFCE
session logout dialog is styled through the `xfsm-logout-dialog` GTK style class.
Its translucent background is subject to GTK window visuals and the XFCE compositor.


### Thunar icon-view selection

The GTK3 theme scopes the rubberband overlay to Thunar's `GtkIconView` CSS
node and disables the generic hover shadow on that view. This avoids applying
a large inset hover effect while the icon view is continuously repainted
during pointer-drag selection.


## Translucent surface policy

Translucency is a defining visual characteristic of CambonOS-Dark. GTK 3 and
GTK 4 use a layered midnight-blue material (`#061C31`) so the wallpaper remains
visible through functional surfaces without sacrificing contrast:

| Surface | GTK alpha |
| --- | ---: |
| Main GTK windows | `0.74` |
| Dialogs | `0.78` |
| Menus, popovers and tooltips | `0.80` |
| Document/list surfaces | `0.66` |
| Headerbars and toolbars | `0.68` |
| Editable fields | `0.76` |

Lower alpha reveals more of the desktop. The values are intentionally assertive,
but labels, icons, separators, desktop icon captions, resting-state buttons and
nested layout containers remain transparent and inherit their parent surface.
Hover, active and selected states may add a turquoise interaction tint.

The XFCE panel and Whisker Menu outer shell share the same midnight-blue material
(`#061C31`, `0.86` alpha). Whisker's inner surfaces are more transparent:
categories `0.65`, application list `0.68`, search field `0.76` and focused
search `0.84`. Thunar's file pane uses a scoped `0.66` surface, while its sidebar
and status area use denser supporting surfaces. The file-view labels and
selection/hover feedback remain independent of the pane background.

GTK CSS alpha is only effective when the application window has an
alpha-capable visual and the X11 compositor is active. A theme cannot force an
application to request an ARGB visual, so some GTK applications may continue
to render an opaque top-level background even when child surfaces are
translucent. GTK 4/libadwaita applications may also use their own styling and
rendering paths.

XFWM4 window decorations (titlebar and resize frame) are drawn by the window
manager, not GTK. Their overall opacity is controlled by XFWM4's compositor
settings rather than GTK CSS or the theme's SVG/XPM button artwork. In
**Window Manager Tweaks → Compositor**, enable compositing and adjust
**Opacity of window decorations** to a value below 100 if a translucent
titlebar/frame is desired. The XFWM4 `frame_opacity` Xfconf setting controls
this value. The theme package deliberately does not overwrite per-user Xfconf
settings. Window content opacity and decoration opacity are separate controls.

GTK 2 retains a solid midnight-blue fallback because its legacy GtkRcStyle
resources do not provide the same CSS alpha model. The package's automated
checks validate stylesheet syntax and policy invariants; final rendering must
still be verified in a real XFCE session.
