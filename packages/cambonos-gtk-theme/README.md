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

## Sistema de superficies translúcidas (0.4.2)

La base visual de cada ventana GTK3/GTK4 es una única superficie de azul
medianoche `#061C31` al `0.88` (88 %). Los contenedores de composición y las
vistas de contenido anidadas permanecen transparentes: no vuelven a pintar el
mismo azul sobre la superficie de la ventana. Solo las superficies funcionales
independientes (barras adyacentes, controles editables, menús y popovers)
pintan un fondo propio. Los estados interactivos, iconos y etiquetas conservan
sus estilos específicos. Botones, etiquetas, iconos,
selecciones y estados semánticos conservan sus estilos propios cuando cumplen
una función visual o interactiva específica.

| Superficie | Opacidad objetivo |
| --- | ---: |
| Ventana base (GtkWindow) | 0.88 |
| GtkFrame | Transparente |
| GtkNotebook | 0.50 |
| GtkStatusbar | Transparente |
| GtkMenubar | 0.84 |
| Vistas y contenedores internos | Transparente |
| Campos editables | 0.88 |
| Barras y cabeceras adyacentes | 0.84 |
| Diálogos, menús, popovers y tooltips | 0.72 |
| Panel XFCE | 0.86 |
| Whisker exterior | 0.72 |
| Whisker categorías | 0.52 |
| Whisker búsqueda | 0.76–0.82 |

Las vistas GTK3/GTK4 y las áreas de contenido de Thunar se fuerzan a transparentes también mediante selectores específicos de mayor prioridad, para evitar que las reglas heredadas de Orchis vuelvan a pintar el contenido. Los menús y Whisker reducen su opacidad; la del panel XFCE se mantiene sin cambios. Las superficies transparentes no añaden una segunda capa. Los valores son opacidades CSS, no porcentajes de transparencia: `0.88`
significa 88 % de azul medianoche y 12 % de contenido subyacente. Los estados
interactivos mantienen el turquesa `#019FA7`; los colores de éxito, advertencia
y error mantienen su semántica. Los iconos y etiquetas no reciben fondos
indiscriminados.

La transparencia GTK depende de que la ventana GTK3 solicite un visual RGBA y
de que exista composición en el escritorio. GTK4 utiliza visuales RGBA, pero
sigue necesitando un compositor para mostrar el escritorio a través de la
ventana. Un tema no puede obligar a una aplicación GTK3 a solicitar un visual
con canal alfa ni neutralizar fondos que la propia aplicación dibuje de forma
opaca. Las decoraciones XFWM4 las dibuja el gestor de ventanas; su opacidad
inactiva corresponde al compositor, no a las reglas CSS del tema.

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


### 0.4.3 — GTK3 surface roles

- GtkWindow: midnight-blue base surface at 0.88 opacity.
- GtkFrame: transparent, without an independent background image.
- GtkNotebook: tinted midnight-blue content surface at 0.40 opacity.
- GtkStatusbar: transparent.
- GtkMenubar: midnight-blue surface at 0.55 opacity; inactive windows use 0.45 opacity.


### 0.4.4 — Consolidated GTK3 surface cascade

- Reconciles the inherited Orchis base declarations with the CambonOS surface policy instead of relying on competing duplicate rules.
- GtkWindow remains the 0.88 midnight-blue base surface.
- GtkFrame remains transparent without removing its borders or functional states.
- GtkNotebook uses the 0.40 tinted surface in both framed and unframed forms; its stack remains transparent.
- GtkStatusbar and its frame containers are transparent, including the Thunar-specific statusbar.
- GtkMenubar uses the 0.55 midnight-blue surface, including when embedded in a headerbar; inactive menubars use 0.45.
- GTK4 styling, XFCE panel, Whisker Menu, window decorations, and functional interaction states are otherwise unchanged.


### 0.4.5 — Normalized GTK3 surface policy

- Consolidates GTK3 surface declarations into one authoritative policy with selectors scoped to window backgrounds.
- GtkWindow uses the 0.88 midnight-blue base surface.
- GtkFrame backgrounds are transparent while frame borders remain styled.
- GtkNotebook uses a 0.50 midnight-blue tint; its content stack is transparent.
- GtkStatusbar is transparent, including the Thunar statusbar, while retaining spacing and separator styling.
- GtkMenubar uses a 0.84 midnight-blue surface; inactive menubars retain the 0.45 backdrop treatment.
- GTK4, XFCE panel, Whisker Menu, XFWM4 decorations and functional interaction states are unchanged.


## 0.4.6 — GTK3 surface and selection corrections

- Consolidates GTK3 frame, notebook, statusbar and menubar surface treatments after upstream Orchis rules.
- Keeps the Whisker outer frame transparent without changing its category, application-list or search treatments.
- Targets the XFCE Terminal root content box using its GTK `background` style class rather than an invented application CSS class.
- Restores explicit GTK3 checkbox/radio indicator icon sources and their checked/indeterminate/disabled states.
- Defines a shared turquoise rubberband treatment for GTK3 icon/tree views, Thunar and Xfdesktop, while retaining a separate selected-item state.
- GTK4 styling is unchanged; GTK3-specific widget selectors are not copied into GTK4.
