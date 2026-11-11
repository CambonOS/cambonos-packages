# cambonos-gtk-theme

Paquete del único tema oscuro de CambonOS para GTK 3, GTK 4 y Xfwm4.

**Versión del paquete Arch:** `0.6.2-1`. **Versión unificada:** `0.6.2`.

## Construcción

El paquete conserva el código fuente, la paleta oscura canónica, el constructor,
el validador, los recursos y la documentación en `files/source/`. El único
PKGBUILD está en la raíz de `packages/cambonos-gtk-theme/`. Durante `build()`, el PKGBUILD copia las fuentes al directorio de trabajo, genera los
CSS desde `src/palette.json` y valida GTK3, GTK4 y Xfwm4.

`package()` instala únicamente `CambonOS-dark` en `/usr/share/themes/`, junto
con la documentación y la licencia. No instala herramientas de construcción.

## Tema único

`CambonOS-dark` es la única variante disponible. Sus dos puntos de entrada GTK
(`gtk.css` y `gtk-dark.css`) utilizan la misma paleta oscura. Incluye estilos
GTK3/GTK4 y decoraciones Xfwm4. Las aplicaciones GTK4 basadas en libadwaita
pueden ignorar temas GTK externos.

## Activación

Selecciona `CambonOS-dark` en Apariencia de XFCE y en Gestor de ventanas. Se
conserva este nombre para mantener la compatibilidad con LightDM y con las
configuraciones existentes.
