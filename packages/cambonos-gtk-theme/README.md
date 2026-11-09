# cambonos-gtk-theme

Tema oscuro para GTK 3, GTK 4 y XFWM4, basado en Orchis Default Dark (azul),
revisión `a4c48a425e63808345e824495964bd9c2f462e04`.

## Contenido y alcance

- Incluye hojas GTK 3 y GTK 4, decoraciones XFWM4 y ajustes para el escritorio
  XFCE: Thunar, Xfdesktop, panel, Whisker Menu, notificaciones y diálogo de
  sesión.
- No incluye GTK 2, greeters, variantes de escala XFWM4 ni reglas para
  aplicaciones de otros escritorios. Las aplicaciones libadwaita pueden
  conservar partes de su estilo nativo.
- No cambia preferencias del usuario ni instala scripts o hooks.

## Paleta

| Elemento | Color |
| --- | --- |
| Fondo de ventana | Azul noche `#061C31`, alpha `0.88` |
| Texto principal | Blanco cálido `#F7F5EC` |
| Selección de elementos | Turquesa `#019FA7` |
| Foco y borde de arrastre | Turquesa claro `#70E7E6` |
| Banda de selección al arrastrar | `#70E7E6` al 32 %, borde sólido de 1 px |
| Barras de menú | Azul noche, alpha `0.60` |
| Menús emergentes y tooltips | Azul noche, alpha `0.88` |

Las ventanas mantienen la misma superficie al perder el foco. Los contenedores
internos dejan ver el fondo de la ventana; controles editables y barras usan
capas propias de menor opacidad. Los colores semánticos de error, advertencia
y éxito conservan sus valores.

La transparencia requiere un compositor. GTK 3 también depende de que cada
aplicación solicite un visual RGBA; el tema no puede forzarlo ni quitar fondos
opacos que una aplicación dibuje por su cuenta.

## Instalación

Instala `cambonos-gtk-theme` y selecciona `CambonOS-Dark` en Apariencia de
XFCE. Para aplicar también los marcos de ventana, selecciona `CambonOS-Dark`
por separado en Gestor de ventanas > Estilo. La selección del tema de iconos y
del cursor sigue siendo independiente.

El paquete incluye la licencia GPL-3.0-only y el aviso de atribución de Orchis
en `files/upstream/ORCHIS-NOTICE`.
