# cambonos-branding

Recursos de identidad visual aprobados de CambonOS. El paquete distribuye
versiones vectoriales y rasterizadas del icono y del logotipo textual, además
de los recursos tipográficos necesarios para el glifo propio de CambonOS.

## Contenido instalado

```text
/usr/share/cambonos/branding/
├── cambonos-icon.svg
├── cambonos-icon.png
├── cambonos-text.svg
└── cambonos-text.png

/usr/share/fonts/TTF/
└── CambonOS-Symbols.ttf

/usr/share/fontconfig/conf.avail/
└── 65-cambonos-symbols.conf

/usr/share/fontconfig/conf.default/
└── 65-cambonos-symbols.conf -> ../conf.avail/65-cambonos-symbols.conf

/usr/share/licenses/cambonos-branding/
└── LICENSE
```

Los SVG son los recursos vectoriales canónicos. Los PNG son exportaciones
rasterizadas para consumidores que necesiten imágenes de mapa de bits:
`cambonos-icon.png` tiene 1024 × 1024 píxeles y `cambonos-text.png` tiene
3792 × 1024 píxeles. Los cuatro recursos gráficos se instalan en la misma
ubicación canónica.

`files/ttf/` contiene la fuente TrueType preconstruida
`CambonOS-Symbols.ttf` y la regla Fontconfig `65-cambonos-symbols.conf`.
El paquete no genera fuentes durante `makepkg` ni depende de FontForge o
FontTools.

La regla Fontconfig antepone la familia `CambonOS Symbols` cuando el patrón
solicitado contiene el carácter privado `U+10FFFD` (decimal `1114109`),
permitiendo que Fontconfig seleccione esta fuente como fallback para el icono.

## Rutas canónicas e integración

Los consumidores de CambonOS deben utilizar directamente los recursos
necesarios desde:

- `/usr/share/cambonos/branding/cambonos-icon.svg`
- `/usr/share/cambonos/branding/cambonos-icon.png`
- `/usr/share/cambonos/branding/cambonos-text.svg`
- `/usr/share/cambonos/branding/cambonos-text.png`

No se mantienen las variantes `black`/`white`, el logotipo ASCII
`cambonos-logo.txt` ni enlaces simbólicos en `/usr/share/icons/` o
`/usr/share/pixmaps/`. No se ofrece compatibilidad con las rutas anteriores:
los componentes consumidores deben adaptarse a la estructura canónica antes
de su integración. La única ruta simbólica publicada por el paquete es el
enlace Fontconfig que habilita la regla de la fuente.

## Dependencias

Declara `fontconfig` como dependencia de ejecución para proporcionar el
mecanismo de selección de la fuente y cargar la regla de fallback.

## Política de archivos

- Los cuatro recursos gráficos se instalan exclusivamente bajo
  `/usr/share/cambonos/branding/`.
- La fuente se instala en `/usr/share/fonts/TTF/`.
- La regla se instala en `conf.avail` y se habilita mediante el enlace en
  `conf.default`.
- La licencia se instala en `/usr/share/licenses/cambonos-branding/LICENSE`.
- No se modifican archivos bajo `/etc` ni directorios personales.
- Los recursos no deben modificarse manualmente después de la instalación;
  los consumidores deben utilizar las rutas canónicas.

## Validación de los recursos

La aprobación del diseño y la comprobación visual corresponden al equipo de
diseño. Este repositorio comprueba que los recursos aprobados se empaquetan
sin alteraciones, que los SVG mantienen una estructura XML válida, que los
PNG tienen cabecera y dimensiones esperadas, que la fuente TrueType tiene una
cabecera válida y que el enlace Fontconfig resuelve correctamente.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-branding
pacman -Qkk cambonos-branding

test -r /usr/share/cambonos/branding/cambonos-icon.svg
test -r /usr/share/cambonos/branding/cambonos-icon.png
test -r /usr/share/cambonos/branding/cambonos-text.svg
test -r /usr/share/cambonos/branding/cambonos-text.png
test -r /usr/share/fonts/TTF/CambonOS-Symbols.ttf
test -r /usr/share/fontconfig/conf.default/65-cambonos-symbols.conf

xmllint --noout /usr/share/cambonos/branding/cambonos-icon.svg
xmllint --noout /usr/share/cambonos/branding/cambonos-text.svg
fc-match 'CambonOS Symbols'
```

Para disponer de `xmllint`, instalar `libxml2`.

## Pruebas de validación

- [ ] El paquete se construye con `makepkg`.
- [ ] Se instalan los cuatro recursos gráficos en `/usr/share/cambonos/branding/`.
- [ ] Los SVG se validan como XML y se renderizan correctamente.
- [ ] Los PNG tienen las dimensiones documentadas y se visualizan correctamente.
- [ ] `CambonOS-Symbols.ttf` se instala sin modificaciones en `/usr/share/fonts/TTF/`.
- [ ] La regla Fontconfig se instala y su enlace relativo resuelve correctamente.
- [ ] Fontconfig antepone `CambonOS Symbols` para solicitudes que incluyan `U+10FFFD`.
- [ ] No se incluyen variantes black/white ni `cambonos-logo.txt`.
- [ ] No se crean enlaces simbólicos en `/usr/share/icons/` ni `/usr/share/pixmaps/`.
- [ ] La actualización elimina los recursos obsoletos que pertenecían a la versión anterior.
- [ ] La desinstalación elimina los archivos y enlaces propiedad del paquete.
- [ ] No se modifican `/etc`, `$HOME` ni configuraciones de escritorio.

## Notas

Los temas GTK, iconos específicos de escritorio, fondos de pantalla, LightDM y
branding específico de cada entorno deben residir en paquetes independientes.
Este paquete proporciona recursos gráficos genéricos y la integración
tipográfica de CambonOS.
