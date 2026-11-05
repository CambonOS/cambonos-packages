# cambonos-branding

Recursos gráficos comunes de CambonOS. El paquete mantiene todos los archivos originales de identidad visual en una ubicación central y publica enlaces simbólicos en las rutas estándar que necesitan los consumidores del sistema.

## Responsabilidad

- Distribuir los recursos gráficos genéricos de CambonOS.
- Mantener una única ubicación canónica para los archivos de branding.
- Exponer los recursos necesarios mediante enlaces simbólicos en las rutas estándar.
- No instalar temas de escritorio ni modificar configuraciones del administrador.

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

`cambonos-text-black.svg` procede del archivo `cambonos-text-black.png` del paquete fuente recibido. El contenido de ese archivo era SVG (XML), no PNG; se ha corregido su extensión para reflejar su formato real.

## Enlaces simbólicos de compatibilidad

| Ruta publicada | Destino |
|---|---|
| `/usr/share/icons/hicolor/scalable/apps/cambonos.svg` | `/usr/share/cambonos/branding/cambonos-icon.svg` |
| `/usr/share/pixmaps/cambonos-logo.svg` | `/usr/share/cambonos/branding/cambonos-icon.svg` |
| `/usr/share/pixmaps/cambonos-logo-text.svg` | `/usr/share/cambonos/branding/cambonos-text.svg` |

Los nombres y rutas existentes se mantienen para no romper consumidores que ya los utilicen. Los enlaces son relativos para que puedan comprobarse dentro del árbol de empaquetado y sigan resolviendo correctamente bajo `/usr/share`.

Las variantes `black` y `white` permanecen disponibles en el directorio canónico. No se publican aliases adicionales en rutas del sistema porque el paquete fuente no define consumidores ni rutas de compatibilidad para ellas.

## Dependencias

No declara dependencias de ejecución ni opcionales.

## Política de archivos

- Los recursos originales son propiedad del paquete y se gestionan bajo `/usr/share/cambonos/branding/`.
- Los enlaces simbólicos también son propiedad del paquete.
- No se modifican archivos bajo `/etc` ni directorios personales.
- Las personalizaciones locales no deben hacerse modificando los archivos propiedad del paquete; deben utilizar rutas alternativas y configurar el consumidor correspondiente.

## Identidad visual

La paleta oficial de CambonOS utiliza exactamente estos valores:

| Nombre | Valor |
|---|---|
| Verde lima eléctrico | `#AEFA50` |
| Turquesa luminoso | `#70E7E6` |
| Azul noche profundo | `#061C31` |
| Blanco | `#FFFFFF` |
| Verde esmeralda | `#149246` |
| Azul turquesa | `#019FA7` |

Los recursos incluidos se conservan tal como aparecen en el archivo fuente recibido. La tabla anterior es la referencia oficial para futuras exportaciones y revisiones del logotipo.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-branding

pacman -Qkk cambonos-branding

# Recursos canónicos
find /usr/share/cambonos/branding -maxdepth 1 -type f -printf '%f\n'

# Enlaces y destinos
readlink -v /usr/share/icons/hicolor/scalable/apps/cambonos.svg
readlink -v /usr/share/pixmaps/cambonos-logo.svg
readlink -v /usr/share/pixmaps/cambonos-logo-text.svg

# Verificar que los enlaces resuelven
test -r /usr/share/icons/hicolor/scalable/apps/cambonos.svg
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
- [ ] No se instala ningún recurso original duplicado en las rutas de compatibilidad.
- [ ] Los tres enlaces simbólicos se crean con los destinos esperados.
- [ ] Los tres enlaces simbólicos resuelven a archivos legibles.
- [ ] Todos los SVG son XML válido y se renderizan correctamente.
- [ ] `cambonos-text-black.svg` se identifica como SVG, no como PNG.
- [ ] La actualización reemplaza recursos y enlaces por los incluidos en el paquete.
- [ ] La desinstalación elimina los archivos y enlaces propiedad del paquete.
- [ ] No se modifican `/etc`, `$HOME` ni configuraciones de escritorio.

## Notas

Los temas GTK, iconos específicos de escritorio, fondos de pantalla, LightDM y branding específico de cada entorno deben residir en paquetes independientes. Este paquete proporciona exclusivamente recursos gráficos genéricos y sus rutas de integración.
