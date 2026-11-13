# cambonos-graphical-base

Base compartida de infraestructura y aplicaciones para los escritorios Xorg de
CambonOS. Es una dependencia de los futuros paquetes `cambonos-qtile` y
`cambonos-xfce`; no instala un gestor de ventanas, compositor, panel ni una sesión
completa.

## Funcionalidad

- Servidor gráfico Xorg y utilidades de entrada y monitores.
- NetworkManager, su applet de sesión, BlueZ y Blueman.
- PipeWire con compatibilidad ALSA, PulseAudio y JACK, WirePlumber y Pavucontrol.
- Avahi y NSS mDNS para descubrimiento y resolución en redes locales.
- Thunar con Thunar Volman, UDisks2, GVFS y sus backends seleccionados.
- Miniaturas de imágenes, vídeo, fuentes, EPUB, ODF, RAW y PDF, además de operaciones de compresión desde Thunar.
- Gestor de discos GNOME, `htop` y `nvtop` como utilidades comunes.
- `gnome-keyring` y `libsecret` para almacenamiento de credenciales; no se modifica PAM ni se promete desbloqueo automático.
- Agente gráfico Polkit común basado en `polkit-gnome`.
- UPower y los portales XDG con backend GTK.
- Autoinicio XDG común para Thunar daemon y el agente Polkit.
- `dex` como ejecutor de entradas XDG Autostart en sesiones ligeras como Qtile.

La selección de GVFS incluye AFC, DNS-SD, GPhoto2, MTP, NFS, SMB y WSDD. Los
backends de GVFS y las aplicaciones gráficas se instalan como dependencias obligatorias
para que las capacidades comunes estén disponibles en ambos escritorios.

## Servicios del sistema

Durante la instalación y actualización, el script del paquete comprueba y habilita si
es necesario:

- `NetworkManager.service`
- `bluetooth.service`
- `avahi-daemon.service`

La habilitación no inicia ni reinicia los servicios. Las unidades enmascaradas no se
desenmascaran automáticamente: se informa del conflicto y se conserva la decisión
administrativa. El paquete no deshabilita servicios al retirarse.

UDisks2, UPower y Polkit utilizan sus mecanismos de activación bajo demanda. PipeWire,
PipeWire Pulse y WirePlumber funcionan en el ámbito de la sesión de usuario; no se
habilitan como servicios globales del sistema.

## Configuración mantenida

### NSS mDNS

`cambonos-configure-nsswitch` garantiza que la línea activa `hosts:` de
`/etc/nsswitch.conf` contenga `mdns_minimal [NOTFOUND=return]` inmediatamente después
de `mymachines`. Si `mdns_minimal` ya aparece como módulo, el archivo no se modifica.

El script se ejecuta durante la instalación y actualización del paquete. Un hook ALPM
de tipo `Path` vuelve a ejecutarlo después de transacciones que instalen o actualicen
`/etc/nsswitch.conf`, para reparar cambios introducidos por otros paquetes. No hay
vigilancia continua: las modificaciones manuales del administrador se respetan hasta
que una transacción posterior vuelva a activar el hook.

Si no existe una línea `hosts:` activa, hay más de una, o no contiene `mymachines`, el
script no inventa una estructura alternativa ni reemplaza el archivo: informa del
problema y termina sin modificarlo.

### Thunar y Thunar Volman

Se instalan las configuraciones Xfconf globales de Thunar y Thunar Volman en
`/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/thunar-volman.xml` que activa el automontaje
de unidades y medios extraíbles. También se instala una entrada XDG Autostart para
`thunar --daemon`.

La configuración global actúa como valor predeterminado; los usuarios pueden mantener
sus preferencias individuales en su configuración Xfconf.

## Contrato de integración de los escritorios

- Los paquetes oficiales `blueman` y `network-manager-applet` proporcionan sus propias
  entradas XDG Autostart (`blueman.desktop` y `nm-applet.desktop`). Este paquete instala
  ambos programas y sus dependencias; no duplica esas entradas.
- Cada sesión debe procesar XDG Autostart. XFCE ya incorpora ese mecanismo; el futuro
  paquete Qtile debe ejecutar `dex -a` una vez por sesión. `dex` se instala como
  dependencia de esta base para que el ejecutor esté disponible.
- Cada escritorio debe proporcionar una zona de notificación/bandeja compatible con
  los applets que mantiene en ejecución.
- `cambonos-graphical-base` instala un autoinicio XDG para el agente `polkit-gnome`. El paquete `xfce4-session` también incluye una entrada de autoinicio de agente Polkit. Por decisión de alcance, `cambonos-xfce-conf` no modifica ni desactiva esa entrada; la posible duplicidad queda como punto de validación funcional y sólo se corregirá si se reproduce un problema real.
- Los paquetes de escritorio configuran los backends XDG Portal y sus preferencias de
  sesión. Este paquete proporciona el portal y el backend GTK, pero no impone una
  selección global.

## Exclusiones

No incluye impresión, navegador, editor, visor de documentos, terminal, gestor de ventanas, compositor, panel, lanzador, bloqueo de pantalla, daemon de notificaciones ni gestor gráfico de energía. Esas funciones pertenecen al paquete de escritorio o al paquete de aplicaciones correspondiente.

No incluye Wayland ni backends de portal específicos de Wayland.
