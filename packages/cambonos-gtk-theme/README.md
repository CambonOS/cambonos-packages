# cambonos-gtk-theme

Paquete de temas visuales de CambonOS para GTK 3, GTK 4 y Xfwm4.

**Versión del paquete Arch:** `0.5.0-1`. **Versión del tema fuente:** `0.4.0`.

## Construcción

El paquete conserva el proyecto CambonOS GTK Theme 0.4.0 completo en
`files/source/`: paleta canónica, builder, validador, recursos base de los
temas, documentación, licencia y metadatos del proyecto original.

Durante `build()`, el `PKGBUILD` copia esas fuentes al directorio de trabajo,
ejecuta `tools/build-theme.py` para generar los CSS de GTK a partir de
`src/palette.json` y ejecuta `tools/validate-theme.py`. `package()` instala
únicamente los directorios resultantes `CambonOS` y `CambonOS-dark` en
`/usr/share/themes/`; no instala el código fuente ni las herramientas de
construcción en el sistema.

## Variantes

- `CambonOS`: variante clara, con soporte de apariencia GTK oscura.
- `CambonOS-dark`: variante oscura.

Ambas incluyen estilos GTK3/GTK4, decoraciones Xfwm4 y sus recursos gráficos.

## Transparencia

La versión 0.4.0 utiliza alpha 0.88 en las superficies principales y reduce
proporcionalmente los demás valores alpha. La transparencia efectiva depende
del soporte GTK y del compositor de ventanas; no convierte por sí misma toda
la ventana en translúcida.

## Activación

Selecciona `CambonOS` o `CambonOS-dark` en Apariencia de XFCE. Para las
decoraciones de ventanas, selecciona el mismo nombre en Gestor de ventanas.
Las aplicaciones GTK4 basadas en libadwaita pueden ignorar temas GTK externos.

La versión anterior del paquete instalaba únicamente `CambonOS-Dark`. Esta
versión instala `CambonOS` y `CambonOS-dark`; tras actualizar, selecciona
`CambonOS-dark` en Apariencia de XFCE y en Gestor de ventanas si tenías
seleccionado el nombre anterior `CambonOS-Dark`.
