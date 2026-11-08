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
