# cambonos-xfce-conf

Configuración y sesión XFCE de CambonOS. Este paquete depende de la infraestructura
común `cambonos-graphical-base`, de la identidad visual, del tema GTK y de la
configuración de LightDM; no instala ni habilita LightDM por su cuenta.

## Sesión

Instala la sesión `CambonOS XFCE` en `/usr/share/xsessions/cambonos-xfce.desktop` y
el wrapper `/usr/bin/cambonos-startxfce`. El wrapper antepone `/etc/cambonos/xdg` a
`XDG_CONFIG_DIRS`, conserva `/etc/xdg` y los directorios preexistentes y ejecuta
`/usr/bin/startxfce4`. La configuración de usuario en `~/.config` conserva prioridad
sobre los valores globales.

## Configuración global

Los valores predeterminados se distribuyen bajo `/etc/cambonos/xdg`:

- Menú XFCE y asociaciones MIME específicas de la sesión.
- Helpers Exo para terminal, Thunar y Chromium.
- Panel inferior de 35 px con Whisker, tres lanzadores, lista de ventanas, notificaciones,
  bandeja, audio, energía y reloj.
- Whisker con favoritos Chromium/Thunar/Terminal, accesos de configuración, bloqueo,
  cambio a greeter, perfil y cierre de sesión.
- Configuración Xfconf de teclado, escritorio, atajos, notificaciones, panel, energía,
  salvapantallas, Xfwm4 y XSettings.
- Configuración nativa de XFCE Terminal generada durante el build con los 16 colores de
  `/usr/share/cambonos/branding/console-colors`; la paleta no se duplica en el repositorio.

Thunar y Thunar Volman no se configuran aquí: sus canales Xfconf comunes pertenecen a
`cambonos-graphical-base`. Tampoco se copian archivos de `skel` a usuarios existentes ni
se realizan migraciones automáticas de perfiles. Los 13 lanzadores `.desktop` personales
que el repositorio heredado ocultaba o reemplazaba no se migran.

## Apariencia y wallpaper

Usa `CambonOS-dark`, `Papirus-Dark`, cursor `elementary`, Cantarell 14 y Monospace 14.
Xfwm4 mantiene compositor y sombras, título centrado y un espacio de trabajo; los valores
de opacidad de ventana definidos por el perfil son 95 %. El wallpaper se instala
provisionalmente en `/usr/share/backgrounds/cambonos/wallpaper.jpeg` hasta que exista el
paquete común de fondos.

## Polkit

No modifica la entrada de autoinicio Polkit que proporciona XFCE. La posible coexistencia
con el agente común de `cambonos-graphical-base` queda pendiente de validación en una
sesión real y no se altera preventivamente.

## Exclusiones

No instala MenuLibre, Orca, Blueberry, VLC, Firefox ni aplicaciones de impresión. No
instala el antiguo `archie.sh`, no modifica `/etc/xdg/xfce4/xinitrc`, no habilita servicios
ni reconfigura LightDM. LibreOffice y Hunspell son dependencias opcionales de
`cambonos-xfce`, no obligatorias para la sesión.
