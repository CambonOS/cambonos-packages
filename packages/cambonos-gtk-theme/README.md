# cambonos-gtk-theme

Tema oscuro para XFCE basado en Orchis Default Dark (azul), revisión
`a4c48a425e63808345e824495964bd9c2f462e04`. Incluye estilos GTK3, GTK4 y
decoraciones XFWM4. Los estilos de widgets genéricos proceden de Orchis; las
adaptaciones propias se limitan a la paleta y a integraciones XFCE.

## Alcance

- Compatible con GTK3, GTK4 y XFWM4. Integra Thunar, Xfdesktop, panel,
  Whisker Menu, notificaciones y diálogo de sesión XFCE.
- No incluye GTK2, greeters, variantes de escala XFWM4 ni reglas específicas
  para aplicaciones de otros escritorios. Las aplicaciones libadwaita pueden
  conservar partes de su estilo nativo.
- No cambia preferencias del usuario, no fuerza la selección del tema y no
  instala scripts ni hooks.

## Paleta y superficies

| Uso | Valor |
| --- | --- |
| Fondo principal | `#061C31` al 88 % |
| Selección | `#019FA7` |
| Foco | `#70E7E6` |
| Rectángulo de arrastre | Turquesa al 28 %, borde al 92 % |
| Texto, también sobre selección | `#F7F5EC` |
| Barra y desplegables de menú | Azul medianoche al 88 % |

Las ventanas GTK usan una superficie azul medianoche con alpha `0.88`. Los
`GtkBox` hijos directos de la ventana usan esa misma superficie; otros
contenedores internos son transparentes. Barras y campos usan capas de baja
opacidad. La barra y los menús desplegables usan azul medianoche al 88 % para
que el texto del menú conserve contraste. Selección y foco permanecen turquesa para
conservar contraste. Las superficies conservan el mismo alpha al perder el
foco. Los estados semánticos de error, advertencia y éxito
mantienen sus colores propios.

La transparencia requiere un compositor. GTK3 también depende de que la
aplicación solicite un visual RGBA; el tema no puede forzarlo ni quitar fondos
opacos que una aplicación dibuje por su cuenta.

## Instalación y procedencia

Instala `cambonos-gtk-theme` y selecciona `CambonOS-Dark` en Apariencia de
XFCE. Para aplicar también los marcos de ventana, selecciona `CambonOS-Dark`
por separado en Gestor de ventanas > Estilo; XFCE mantiene esa elección fuera
de la configuración del tema GTK. El tema de iconos y el cursor siguen siendo
independientes. La licencia GPL-3.0-only y el aviso de atribución de Orchis se
instalan con el paquete; consulta `files/upstream/ORCHIS-NOTICE`.
