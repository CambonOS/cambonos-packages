# cambonos-grub

Configuración global de GRUB y tema CambonOS basado en Vimix para sistemas Arch Linux rolling-release.

## Dependencias

- `grub>=2:2.16`, la versión mínima actual que proporciona el soporte de `/etc/default/grub.d/*.cfg` usado por el paquete.
- `os-prober`, para detectar otros sistemas operativos y habilitar menús multiboot.
- `bash`, para el helper de regeneración.

## Archivos

| Ruta | Función |
|---|---|
| `/etc/default/grub.d/60-cambonos.cfg` | Valores predeterminados CambonOS, gestionados por pacman con política `backup`. |
| `/usr/share/grub/themes/CambonOS/theme.txt` | Tema GRUB y paleta CambonOS. |
| `/usr/share/grub/themes/CambonOS/` | Fondo, fuente, marcos, selección e iconos de sistemas operativos. |
| `/usr/lib/cambonos-grub/regenerate-grub-config` | Regenera una configuración GRUB ya existente. |
| `/usr/share/libalpm/hooks/cambonos-grub-kernel.hook` | Actualiza el menú después de cambios de kernel. |

El tema deriva de Vimix de Vinceliuice y conserva GPL-3.0 y su atribución. La fuente Unifont incluida se redistribuye bajo GPL-2.0-or-later con la excepción GNU de incrustación. El paquete incluye ambos textos de licencia y las atribuciones en `NOTICE`.

La paleta del tema usa azul noche (`#061C31`) como fondo, blanco (`#F7F5EC`) para las entradas normales, turquesa (`#70E7E6`) para la selección y verde lima (`#AEFA50`) para la cuenta atrás. La comprobación visual en GRUB sobre UEFI o BIOS sigue pendiente.

## Configuración predeterminada

- Menú visible durante 5 segundos, con CambonOS como distribuidor.
- `GRUB_GFXMODE=auto`; no se fuerza una resolución ni se conserva el modo gráfico del kernel.
- IPv6 permanece habilitado. Los parámetros de kernel predeterminados son `splash loglevel=3`.
- `os-prober` está habilitado para sistemas multiboot.
- Las opciones avanzadas se muestran en el menú principal, sin submenú, y las entradas de recuperación están habilitadas; `BootNext` permanece deshabilitado.
- Se precargan módulos GPT y MBR.

El archivo de configuración principal `/etc/default/grub` pertenece a `grub` y no se reemplaza. Los administradores pueden modificar el drop-in; pacman preserva cambios locales y puede generar `.pacnew`.

## Regeneración del menú

Los scriptlets regeneran `/boot/grub/grub.cfg` al instalar, actualizar o retirar este paquete. El hook ALPM hace lo mismo después de instalar, actualizar o retirar un kernel en `usr/lib/modules/*/vmlinuz`. Si el archivo de salida aún no existe, la regeneración se omite. Si no puede regenerarse, se informa del fallo y puede ejecutarse manualmente:

```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

Las ediciones directas en `grub.cfg` se reemplazan en la siguiente regeneración; los cambios persistentes deben hacerse en `/etc/default/grub.d/` o en los scripts de `/etc/grub.d/`. Asegúrate de que `/boot` está montado antes de actualizar el kernel.

El paquete no ejecuta `grub-install`, no selecciona disco o modo UEFI/BIOS y no instala el cargador en el disco. Esas acciones dependen de la máquina y siguen siendo responsabilidad del administrador o del instalador.

## Comprobación

```bash
grub-mkconfig -o /boot/grub/grub.cfg
grub-script-check /boot/grub/grub.cfg
pacman -Qkk cambonos-grub
```