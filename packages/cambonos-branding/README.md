# cambonos-branding

Recursos gráficos genéricos de CambonOS para aplicaciones y entornos que necesiten identificar la distribución.

## Responsabilidad

Este paquete distribuye los recursos gráficos comunes de CambonOS. No instala un tema de escritorio, no configura un entorno gráfico y no modifica archivos de configuración del administrador.

## Contenido instalado

| Recurso | Ruta |
|---|---|
| Icono SVG | `/usr/share/icons/hicolor/scalable/apps/cambonos.svg` |
| Imagen PNG | `/usr/share/pixmaps/cambonos.png` |
| Licencia del paquete | `/usr/share/licenses/cambonos-branding/LICENSE` |

## Dependencias

No declara dependencias de ejecución ni opcionales.

## Política de configuración y propiedad

Los archivos son recursos estáticos propiedad del paquete y se instalan directamente en `/usr/share`. No se gestionan archivos bajo `/etc` ni directorios personales.

Las personalizaciones locales de estos recursos pueden ser reemplazadas por una actualización del paquete. Para mantener una variante local, debe utilizarse una ruta alternativa y configurar el consumidor correspondiente para apuntar a ella.

## Identidad visual

La paleta oficial de CambonOS debe utilizar exactamente estos valores:

| Nombre | Valor |
|---|---|
| Verde lima eléctrico | `#AEFA50` |
| Turquesa luminoso | `#70E7E6` |
| Azul noche profundo | `#061C31` |
| Blanco | `#FFFFFF` |
| Verde esmeralda | `#149246` |
| Azul turquesa | `#019FA7` |

El paquete incluye el logotipo actual de CambonOS en dos formatos: SVG, como recurso vectorial escalable, y PNG, para consumidores que necesiten una imagen rasterizada. Ambos representan la nueva identidad visual de la distribución y se instalan en las rutas indicadas en la tabla anterior.

La paleta de la tabla es la referencia oficial para los recursos gráficos de CambonOS. Las futuras modificaciones o exportaciones del logotipo deben conservar la identidad visual y utilizar esos valores de color.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-branding

pacman -Qkk cambonos-branding
test -r /usr/share/icons/hicolor/scalable/apps/cambonos.svg
test -r /usr/share/pixmaps/cambonos.png
file /usr/share/icons/hicolor/scalable/apps/cambonos.svg
file /usr/share/pixmaps/cambonos.png
```

Validar SVG:

```bash
xmllint --noout /usr/share/icons/hicolor/scalable/apps/cambonos.svg
```

Si se dispone de un entorno gráfico, comprobar que el icono se muestra correctamente en un consumidor real y que el PNG se escala sin artefactos visibles.

## Pruebas de validación

- [ ] El paquete se construye con `makepkg`.
- [ ] El paquete contiene exactamente los dos recursos y la licencia esperados.
- [ ] Ambos archivos se instalan en las rutas declaradas.
- [ ] El SVG es XML válido y se renderiza correctamente.
- [ ] El PNG tiene formato, dimensiones y transparencia esperados.
- [ ] La paleta de los nuevos recursos coincide exactamente con los seis valores oficiales.
- [ ] La actualización reemplaza los recursos por la versión del paquete.
- [ ] La desinstalación elimina únicamente los archivos propiedad del paquete.
- [ ] No se modifican `/etc`, `$HOME` ni configuraciones de escritorio.
- [ ] `pacman -Qkk cambonos-branding` no informa de archivos ausentes o alterados inesperadamente.

## Notas

Los temas GTK, iconos de escritorio, fondos de pantalla, LightDM y branding específico de cada entorno deben residir en paquetes independientes. Este paquete solo proporciona recursos genéricos.
