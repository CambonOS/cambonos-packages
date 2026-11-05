# cambonos-branding

Recursos gráficos aprobados de CambonOS. El paquete mantiene los recursos en una ubicación canónica y publica los enlaces de integración que consumen el escritorio y otras aplicaciones.

## Responsabilidad

- Distribuir los recursos gráficos aprobados por el equipo responsable de diseño.
- Mantener una única ubicación canónica para los archivos de branding.
- Publicar los enlaces de integración declarados por el paquete.
- No diseñar, modificar ni aprobar visualmente los recursos.
- No instalar temas de escritorio ni modificar configuraciones del administrador.

El diseño, la paleta, la exportación y la validación visual corresponden al equipo de diseño. Este repositorio verifica el empaquetado, las rutas, los enlaces, los permisos y el ciclo de vida de los archivos distribuidos.

## Ubicación canónica

Todos los recursos visuales se instalan en:

```text
/usr/share/cambonos/branding/
├── cambonos-icon.svg
├── cambonos-icon-black.svg
├── cambonos-icon-white.svg
├── cambonos-text.svg
├── cambonos-text-black.svg
└── cambonos-text-white.svg
```

`cambonos-text-black.svg` se distribuye como SVG. La extensión y el formato del recurso coinciden.

## Rutas de integración publicadas

| Ruta publicada | Destino |
|---|---|
| `/usr/share/icons/hicolor/scalable/apps/cambonos-logo.svg` | `/usr/share/cambonos/branding/cambonos-icon.svg` |
| `/usr/share/pixmaps/cambonos-logo.svg` | `/usr/share/cambonos/branding/cambonos-icon.svg` |
| `/usr/share/pixmaps/cambonos-logo-text.svg` | `/usr/share/cambonos/branding/cambonos-text.svg` |

Estas son las rutas publicadas por la versión actual del paquete. Las rutas históricas que utilizaban nombres anteriores, como `cambonos.svg`, están obsoletas y no se mantienen como aliases de compatibilidad. Los enlaces son relativos para que puedan comprobarse dentro del árbol de empaquetado y sigan resolviendo correctamente bajo `/usr/share`.

Las variantes `black` y `white` permanecen disponibles únicamente en el directorio canónico; no se crean enlaces adicionales para ellas.

## Dependencias

No declara dependencias de ejecución ni opcionales.

## Política de archivos

- Los recursos originales son propiedad del paquete y se gestionan bajo `/usr/share/cambonos/branding/`.
- Los enlaces simbólicos también son propiedad del paquete.
- No se modifican archivos bajo `/etc` ni directorios personales.
- Las personalizaciones locales no deben hacerse modificando los archivos propiedad del paquete; deben utilizar rutas alternativas y configurar el consumidor correspondiente.

## Validación de los recursos

La aprobación del diseño y la comprobación visual de los SVG corresponden al equipo de diseño. En este paquete se comprueba que los recursos aprobados se instalan sin alteraciones en las rutas declaradas, que los SVG mantienen una estructura XML válida y que los enlaces simbólicos resuelven a sus destinos.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-branding

pacman -Qkk cambonos-branding

# Recursos canónicos
find /usr/share/cambonos/branding -maxdepth 1 -type f -printf '%f\n'

# Enlaces y destinos
readlink -v /usr/share/icons/hicolor/scalable/apps/cambonos-logo.svg
readlink -v /usr/share/pixmaps/cambonos-logo.svg
readlink -v /usr/share/pixmaps/cambonos-logo-text.svg

# Verificar que los enlaces resuelven
test -r /usr/share/icons/hicolor/scalable/apps/cambonos-logo.svg
test -r /usr/share/pixmaps/cambonos-logo.svg
test -r /usr/share/pixmaps/cambonos-logo-text.svg

# Validar todos los SVG canónicos
for svg in /usr/share/cambonos/branding/*.svg; do
  xmllint --noout "$svg" || exit 1
done
```

Para disponer de `xmllint`, instalar `libxml2`.

## Pruebas de validación

- [ ] El paquete se construye con `makepkg`.
- [ ] Todos los recursos visuales se instalan bajo `/usr/share/cambonos/branding/`.
- [ ] No se instala ningún recurso original duplicado fuera de su ubicación canónica.
- [ ] Los tres enlaces simbólicos se crean con los destinos esperados.
- [ ] Los tres enlaces simbólicos resuelven a archivos legibles.
- [ ] No se crean aliases para rutas históricas obsoletas, como `cambonos.svg`.
- [ ] Todos los SVG son XML válido.
- [ ] `cambonos-text-black.svg` se identifica como SVG, no como PNG.
- [ ] La actualización reemplaza recursos y enlaces por los incluidos en el paquete.
- [ ] La desinstalación elimina los archivos y enlaces propiedad del paquete.
- [ ] No se modifican `/etc`, `$HOME` ni configuraciones de escritorio.

## Notas

Los temas GTK, iconos específicos de escritorio, fondos de pantalla, LightDM y branding específico de cada entorno deben residir en paquetes independientes. Este paquete proporciona exclusivamente recursos gráficos genéricos y sus rutas de integración.
