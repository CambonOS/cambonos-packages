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

GTK 3 and GTK 4 use a deliberately assertive transparency hierarchy: top-level
windows (`0.78` alpha), dialogs (`0.82`), floating menus/popovers (`0.84`),
content views (`0.72`), window chrome (`0.68`) and editable fields (`0.78`).
Lower alpha means more of the desktop or parent surface remains visible. These
values are intended to make transparency perceptible rather than merely
nominal, while retaining a dark midnight-blue tint.

The policy paints only independent functional surfaces. Generic buttons at
rest, labels, icons, separators and nested layout containers do not receive a
background of their own. They inherit the already-painted parent. Hover,
active and selected states may add a turquoise interaction background.
The XFCE panel and Whisker Menu outer frame share the same midnight-blue
material (`#061C31`, `0.86` alpha), making the menu visually extend from its
launcher panel. Whisker's inner surfaces step down subtly: categories use
`0.80`, the application list `0.84`, and the search field `0.90` (`0.92`
while focused). Panel and menu surface rules are defined once in the GTK 3
transparency policy to avoid competing declarations. XFdesktop icon labels
remain explicitly transparent.

GTK 2 uses the legacy GtkRcStyle/GdkColor model and this package's GTK 2
resource format exposes opaque named colors rather than GTK 3/4 CSS alpha
colors. It therefore retains a solid midnight-blue fallback. GTK window alpha
also depends on GTK selecting an alpha-capable visual and on a functioning
compositor; CSS alone cannot force transparency if the display/compositor does
not provide it. XFWM4 decorations are image assets whose opacity is controlled
by the window manager/compositor, not GTK CSS.

The policy applies to GTK 3/4 applications that use the selected theme and
honor GTK CSS. It does not override libadwaita's independent styling system,
applications with custom-rendered surfaces, or non-GTK toolkits such as Qt.
The package's automated checks validate CSS syntax and policy invariants, but
the final rendering still requires validation in a real XFCE session.
