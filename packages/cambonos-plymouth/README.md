# cambonos-plymouth

Tema Plymouth de CambonOS e integración con `mkinitcpio` para Arch Linux. El
paquete selecciona el tema en una instalación nueva, incorpora Plymouth al
initramfs y lo reconstruye sin reemplazar la configuración principal del
administrador.

## Diseño

El tema `two-step` usa el azul noche `#061C31`, turquesa `#70E7E6` y una barra
de progreso discreta. El logotipo es el icono canónico de CambonOS. La
transición es inmediata (`TransitionDuration=0.0`) y Plymouth conserva su
`ShowDelay=0`, por lo que el tema no añade una espera al arranque.

GRUB añade `splash quiet` a sus parámetros predeterminados para activar el
splash y ocultar los mensajes de consola. Si se usa otro cargador, hay que
añadir esos parámetros a su configuración. Plymouth depende del framebuffer o
de KMS disponible durante el arranque; sin ellos puede caer al modo texto.

## Dependencias e integración

- `plymouth`, para el daemon, el selector de tema y el hook de initramfs.
- `mkinitcpio>=36`, para los archivos de configuración drop-in.

El paquete instala `/etc/mkinitcpio.conf.d/90-cambonos-plymouth.conf`. El
fragmento agrega el hook `plymouth` sin reemplazar `HOOKS` ni modificar
`/etc/mkinitcpio.conf`; lo sitúa antes de `encrypt`/`sd-encrypt`, o después de
`udev`/`systemd` cuando no hay cifrado. El archivo usa la política `backup` de
pacman para conservar ajustes locales.

Al instalar se selecciona CambonOS y se regeneran los presets existentes. En
actualizaciones se respeta el tema elegido por el administrador y se vuelve a
generar el initramfs. Al desinstalar se restaura el tema predeterminado solo si
CambonOS sigue seleccionado, se retira el hook propiedad del paquete y se
regeneran los presets. Si todavía no hay un kernel/preset instalado, se muestra
un aviso y la configuración se aplicará cuando el paquete se instale con un
kernel presente.

No se modifican los parámetros de otros cargadores, las configuraciones
personales, los presets del kernel ni `/etc/mkinitcpio.conf`. El administrador
debe resolver cualquier `.pacnew` generado por pacman. Las instalaciones con
presets antiguos que definen `ALL_config` deben actualizar dichos presets para
que mkinitcpio cargue los drop-ins.

## Comprobación

```bash
plymouth-set-default-theme
plymouth-set-default-theme --list
grep -E '^(HOOKS|ALL_config)' /etc/mkinitcpio.conf /etc/mkinitcpio.conf.d/*.conf
lsinitcpio /boot/initramfs-linux.img | grep -E 'plymouth|themes/cambonos'
pacman -Qkk cambonos-plymouth
```

La visibilidad y el encuadre dependen del firmware, GPU, KMS, resolución,
cargador y preset local; deben comprobarse en hardware o una VM Arch limpia.