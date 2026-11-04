# cambonos-release

Identidad de distribución y metadatos de release de CambonOS sobre una base Arch Linux.

## Responsabilidad

Este paquete proporciona metadatos propios de CambonOS y un helper que mantiene la identidad del sistema tras determinadas transacciones de paquetes. No reemplaza la base Arch ni pretende ocultar la procedencia técnica de la distribución.

## Dependencias

**Obligatorias**
- `bash`
- `coreutils`

**Opcionales**
- `lsb-release`: permite proporcionar metadatos mediante `lsb_release`.
- `cambonos-fastfetch`: añade la presentación de identidad mediante el perfil Fastfetch.

## Archivos instalados

| Ruta | Función |
|---|---|
| `/usr/lib/cambonos/os-release` | Metadatos de CambonOS. |
| `/usr/lib/cambonos/lsb-release` | Valores LSB de CambonOS. |
| `/usr/lib/cambonos/restore-release-files` | Helper de mantenimiento/restauración. |
| `/usr/share/libalpm/hooks/zzzz-cambonos-release.hook` | Hook de reparación tras transacciones relevantes. |

El helper puede mantener `/etc/os-release` como enlace a `../usr/lib/cambonos/os-release`. Para LSB, personaliza `/etc/lsb-release` cuando el paquete opcional `lsb-release` está instalado.

## Política de configuración

La política es **managed**: CambonOS aplica su identidad predeterminada sin apropiarse de personalizaciones del administrador.

### `/etc/os-release`

- Si apunta al archivo estándar de Arch (`../usr/lib/os-release`), el helper lo cambia al archivo de CambonOS.
- Si falta, crea el enlace de CambonOS.
- Si es un enlace personalizado o un archivo regular, lo conserva.
- Durante la desinstalación, restaura el enlace estándar de Arch solo si el enlace CambonOS sigue activo.

### `/etc/lsb-release`

- Si `lsb-release` no está instalado, no se gestiona el archivo.
- Antes de aplicar los valores CambonOS, guarda una copia del estado original o registra que no existía.
- Conserva enlaces simbólicos y directorios.
- Escribe el archivo mediante un temporal y sustitución atómica.
- Guarda una copia exacta del contenido administrado para detectar modificaciones posteriores.
- Al desinstalar, restaura el original únicamente si el archivo sigue coincidiendo con el contenido administrado. Si existe `.pacnew`, tiene preferencia sobre la copia anterior.

## Hook ALPM

El hook se ejecuta después de instalar, actualizar o eliminar `filesystem`, `systemd` o `lsb-release`, y ante cambios de determinadas rutas relacionadas con `os-release` y `lsb-release`.

El helper se ejecuta también desde `post_install` y `post_upgrade`.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-release

cat /etc/os-release
readlink /etc/os-release
```

Si `lsb-release` está instalado:

```bash
lsb_release -a
cat /etc/lsb-release
```

Inspeccionar el estado de restauración:

```bash
sudo find /var/lib/cambonos-release -maxdepth 1 -type f -ls
```

## Pruebas de validación

- [ ] Construcción correcta con `makepkg`.
- [ ] Los metadatos instalados identifican `CambonOS`, `ID=cambonos`, `ID_LIKE=arch` y `BUILD_ID=rolling`.
- [ ] En una instalación Arch estándar, `/etc/os-release` pasa a apuntar a `../usr/lib/cambonos/os-release`.
- [ ] Si `/etc/os-release` ya apunta a CambonOS, repetir el helper no produce cambios innecesarios.
- [ ] Si `/etc/os-release` es un archivo regular personalizado, el helper lo conserva.
- [ ] Si `/etc/os-release` es un enlace simbólico personalizado, el helper lo conserva.
- [ ] Si `/etc/os-release` falta, se crea el enlace esperado.
- [ ] Con `lsb-release` ausente, el helper no crea ni modifica `/etc/lsb-release`.
- [ ] Con `lsb-release` instalado, se aplica el contenido LSB CambonOS.
- [ ] La primera aplicación conserva una copia del estado original.
- [ ] Las actualizaciones sucesivas no sobrescriben la copia original.
- [ ] Un `/etc/lsb-release` simbólico se conserva.
- [ ] Un `/etc/lsb-release` que sea directorio se conserva y se informa.
- [ ] El archivo LSB se escribe atómicamente y con permisos esperados.
- [ ] Una edición manual posterior de `/etc/lsb-release` se conserva al desinstalar.
- [ ] Si el contenido sigue siendo el gestionado, la desinstalación restaura el original.
- [ ] Si existe `/etc/lsb-release.pacnew`, se comprueba la prioridad de restauración documentada.
- [ ] La ausencia original de `/etc/lsb-release` se maneja correctamente al desinstalar.
- [ ] El hook ALPM repara la identidad después de actualizar `filesystem`.
- [ ] El hook ALPM repara la identidad después de actualizar `systemd`.
- [ ] El hook ALPM responde a la instalación/actualización/eliminación de `lsb-release`.
- [ ] La desinstalación restaura el enlace Arch solo si el enlace CambonOS sigue activo.
- [ ] Las modificaciones administrativas de identidad no se sobrescriben silenciosamente.
- [ ] `pacman -Qkk cambonos-release` no detecta daños inesperados.

## Punto de atención conocido

El script `post_remove` elimina `/var/lib/cambonos-release` al final incluso cuando el archivo LSB ya no coincide con el contenido gestionado y, por tanto, no puede restaurarse automáticamente. Antes de cerrar la validación, probar el escenario de edición manual y decidir si el backup debe conservarse para recuperación manual en lugar de eliminarse.
