# cambonos-gtk-theme

Tema oscuro de CambonOS optimizado y validado para XFCE. Incluye estilos GTK3,
GTK4 y decoraciones XFWM4. Está basado en Orchis Default Dark, revisión
`a4c48a425e63808345e824495964bd9c2f462e04`, con paleta, reglas de superficie e
integraciones XFCE adaptadas por CambonOS.

## Alcance

- GTK3 y GTK4 genéricos.
- Integraciones específicas de Thunar, Xfdesktop, XFCE Panel, Whisker Menu,
  notificaciones y sesión XFCE cuando están disponibles en el toolkit.
- Una única variante XFWM4: `CambonOS-Dark`.
- No incluye GTK2 ni variantes XFWM4 `-hdpi`/`-xhdpi`. Los recursos GTK `@2x`
  necesarios se conservan.
- No incluye personalizaciones específicas para aplicaciones ajenas a XFCE,
  otros escritorios ni greeters. Slick Greeter puede consumir los estilos GTK3
  genéricos, pero no tiene soporte específico ni pruebas dedicadas.
- No incluye selectores específicos de libadwaita. Sus aplicaciones mantienen
  su sistema visual nativo.

## Identidad cromática

| Función | Color |
| --- | --- |
| Fondo principal | `#061C31` |
| Selección | `#019FA7` |
| Acento y foco | `#70E7E6` |
| Texto principal | `#F7F5EC` |
| Éxito | `#149246` |
| Advertencia | `#FBC02D` |
| Error | `#F44336` |

El verde esmeralda se reserva para indicadores de éxito. Sobre fondos turquesa
sólidos se utiliza texto azul noche para conservar el contraste. Los estados de
éxito usan iconos, indicadores y bordes verdes; las superficies pueden emplear
verde translúcido con texto blanco cálido.

## Transparencias

| Superficie | GTK3 | GTK4 |
| --- | ---: | ---: |
| Ventanas | 0.74 | 0.74 |
| Diálogos, incluido cierre de sesión XFCE | 0.78 | 0.78 |
| Menús, popovers y tooltips | 0.80 | 0.80 |
| Contenido y listas | 0.66 | 0.66 |
| Headerbar, titlebar y toolbar | 0.68 | 0.68 |
| Campos editables | 0.76 | 0.76 |
| Panel XFCE | 0.86 | — |
| Whisker exterior | 0.86 | — |

Whisker mantiene categorías `0.65`, lista `0.68`, búsqueda `0.76` y búsqueda
enfocada `0.84`. Thunar mantiene el panel de archivos `0.66`, barra lateral
`0.72` y barra de estado `0.78`.

La transparencia GTK depende de un visual con canal alfa y de la composición
del escritorio. XFWM4 dibuja las decoraciones de ventana; su opacidad depende
de la configuración del compositor y no se modifica desde este paquete.

## GTK4 y libadwaita

Se conservan los tokens de color GTK4 generales y semánticos (acento, éxito,
advertencia y error), pero no se incluyen selectores `Adw*`, inyección CSS,
enlaces en `~/.config/gtk-4.0`, variables de entorno forzadas ni cambios de
preferencias del usuario. La presencia de GTK4 no garantiza tematización
completa de aplicaciones libadwaita.

## Procedencia y licencia

Basado en [Orchis Theme](https://github.com/vinceliuice/Orchis-theme), variante
Default (azul), esquema Dark, revisión
`a4c48a425e63808345e824495964bd9c2f462e04`. Orchis declara estar basado en
Materia Theme de nana-4. Los recursos heredados y la revisión se documentan en
`files/upstream/ORCHIS-NOTICE`.

CambonOS-Dark se distribuye bajo **GPL-3.0-only**. El paquete instala la
licencia y el aviso de procedencia.

## Instalación

Instala `cambonos-gtk-theme` y selecciona `CambonOS-Dark` desde las herramientas
de apariencia de XFCE. El paquete no selecciona automáticamente el tema, no
modifica preferencias del usuario y no incorpora scripts ni hooks ALPM.

La validación final de renderizado debe realizarse en una sesión XFCE real,
con compositor activado y desactivado y en distintas resoluciones y escalados.
