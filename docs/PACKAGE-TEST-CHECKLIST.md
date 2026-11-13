# Checklist funcional de paquetes CambonOS

Esta checklist registra las funciones de cada paquete que se han comprobado en un sistema Arch real. Complementa la suite automatizada descrita en [TESTING.md](TESTING.md); no es una guía de instalación ni una lista de tareas de publicación.

- `[ ]` Pendiente de verificación funcional.
- `[x]` Verificada en un entorno real.

Marca una función únicamente después de comprobarla. Antes de fusionar `dev` en `main`, deben estar verificadas las funciones incluidas en el alcance soportado de esa versión. Una limitación puede quedar pendiente si está documentada y su exclusión del alcance se ha aceptado expresamente. Toda función nueva que requiera validación real debe añadirse a esta checklist.

Registra el entorno, la fecha y las observaciones de cada comprobación. La existencia de archivos o una prueba estática no demuestra por sí sola el funcionamiento real.

## cambonos-branding

- [x] Los recursos SVG de identidad se muestran correctamente.
- [x] Los recursos PNG de identidad se muestran correctamente.
- [x] La paleta ANSI de CambonOS se aplica a cada TTY virtual al inicializarse.
- [x] Los 16 colores de consola corresponden a la paleta publicada.
- [x] `dialog` aplica el tema CambonOS de `/etc/dialogrc`.

## cambonos-gtk-theme

Alcance del paquete: tres variantes (`CambonOS-dark`,
`CambonOS-dark-balanced` y `CambonOS-dark-transparent`) con recursos GTK 3,
GTK 4 y Xfwm4, generadas desde una plantilla y una paleta canónicas. GTK 2 no
forma parte del alcance: no se incluye `gtk-2.0/gtkrc`. La validación
estructural ejecutada durante la construcción no sustituye las comprobaciones
visuales en una sesión real.

- [x] La instalación deja las tres variantes en `/usr/share/themes/` y la licencia en `/usr/share/licenses/cambonos-gtk-theme/`.
- [x] La instalación no modifica preferencias de usuario ni archivos de configuración global de GTK.
- [x] GTK 3 carga los recursos del tema en aplicaciones compatibles de una sesión XFCE real.
- [x] GTK 4 carga los recursos del tema en aplicaciones compatibles probadas; no implica compatibilidad completa con aplicaciones libadwaita.
- [x] La selección del tema requiere acción del usuario; el paquete no fuerza un tema ni sustituye la configuración local del escritorio.
- [x] La retirada elimina los recursos instalados sin alterar la configuración previa del sistema ni de los usuarios.
- [x] Xfwm4 representa correctamente las decoraciones y todos los estados de los botones en una sesión real (activa/inactiva, maximizar, minimizar, cerrar, sombrear y fijar).
- [x] Xfwm4 mantiene el turquesa original `#019FA7` en ventanas activas y muestra el turquesa atenuado `#397B82` en ventanas inactivas, en los cinco segmentos del título y en las tres variantes.
- [x] La banda de selección al arrastrar en el escritorio XFCE muestra el relleno translúcido y el borde turquesa del tema.
- [x] La legibilidad y el contraste de texto, menús, tooltips, entradas y controles se mantienen con las superficies translúcidas definidas en la paleta.
- [x] La selección del tema en Apariencia y Gestor de ventanas persiste tras cerrar sesión e iniciar de nuevo.

## cambonos-fastfetch

- [x] Fastfetch muestra la identidad y el logotipo de CambonOS.
- [x] Fastfetch muestra correctamente la información principal del sistema.
- [x] Fastfetch se ejecuta en las sesiones de login compatibles mediante `/etc/profile.d/`.
- [x] La integración automática funciona en sesiones interactivas de Bash.
- [x] La integración automática funciona en sesiones interactivas de Zsh cuando está instalado `cambonos-zsh`.
- [x] La integración automática funciona en sesiones interactivas de Fish.
- [x] La integración de shells puede activarse y retirarse sin alterar configuraciones ajenas.

## cambonos-shell-prompt

- [x] Starship utiliza la configuración visual predeterminada de CambonOS.
- [x] El prompt funciona en sesiones interactivas de Bash.
- [x] El prompt funciona en sesiones interactivas de Zsh cuando está instalado `cambonos-zsh`.
- [x] El prompt funciona en sesiones interactivas de Fish.
- [x] El directorio actual y sus directorios padre se representan correctamente.
- [x] Se respeta la configuración personal de Starship del usuario.
- [x] Las consolas virtuales Linux usan el perfil compatible con TTY y los emuladores conservan el perfil visual actual.
- [x] Bash, Zsh y Fish seleccionan el perfil TTY correctamente en una consola virtual real.

## cambonos-zsh

- [x] Zsh carga la configuración global de CambonOS.
- [x] El sistema de autocompletado funciona.
- [x] Los atajos de teclado configurados funcionan.
- [x] El historial persistente funciona.
- [x] Autosuggestions y syntax highlighting funcionan.
- [x] Los fragmentos de integración de otros paquetes se cargan.
- [x] La configuración personal del usuario se mantiene independiente de la configuración global.
- [x] Las operaciones de pacman que modifican el sistema solicitan privilegios cuando corresponde.

## cambonos-release

- [x] El sistema muestra la identidad CambonOS mediante `/etc/os-release`.
- [x] Los metadatos LSB de CambonOS están disponibles cuando se instala el componente correspondiente.
- [x] La identidad CambonOS se mantiene tras las transacciones de paquetes que afectan a los archivos de identidad.
- [x] La retirada del paquete restaura la identidad anterior cuando corresponde.

## cambonos-pacman

- [x] El repositorio stable de CambonOS aparece configurado y habilitado.
- [x] El repositorio testing puede habilitarse mediante su configuración.
- [x] Pacman aplica las opciones diferenciales de CambonOS.
- [x] Pacman conserva la verificación obligatoria de firmas de los repositorios CambonOS.
- [x] La integración con `/etc/pacman.conf` funciona sin eliminar configuraciones manuales del administrador.
- [x] La transición desde la configuración anterior `cambonos-repo` conserva el funcionamiento esperado.
- [x] El snapshot `dev` genera la configuración del canal `testing` y el snapshot `main` genera la del canal `stable`.

## cambonos-grub

- [x] GRUB aplica la configuración predeterminada de CambonOS.
- [x] El menú de GRUB muestra correctamente el tema CambonOS.
- [x] Los iconos de los sistemas operativos se muestran correctamente.
- [x] GRUB detecta otros sistemas operativos cuando `os-prober` está disponible.
- [x] La configuración del menú se regenera después de los cambios de kernel.
- [x] El sistema puede arrancar correctamente con la configuración generada.

## cambonos-plymouth

- [x] Plymouth muestra correctamente el tema CambonOS durante el arranque.
- [x] Los recursos gráficos de CambonOS se cargan desde el initramfs.
- [x] El logo, la barra y el fondo se adaptan correctamente a distintas resoluciones.
- [x] La integración con mkinitcpio incorpora Plymouth a las imágenes initramfs.
- [x] La selección de tema del administrador se conserva durante las actualizaciones.

## cambonos-lightdm

- [x] LightDM selecciona Slick Greeter como interfaz de autenticación.
- [x] El greeter muestra la lista de usuarios y no ofrece login manual ni sesión de invitado.
- [x] El fondo de CambonOS se muestra correctamente.
- [x] NumLock se activa en el greeter.
- [x] HiDPI se detecta y aplica correctamente.
- [x] La selección de sesión permite iniciar los escritorios instalados sin imponer una sesión predeterminada.
- [x] La instalación habilita LightDM cuando no existe otro display manager seleccionado.
- [x] La instalación conserva un display manager previamente seleccionado.
- [x] Las actualizaciones y la retirada respetan el estado de activación del servicio.
- [x] Las configuraciones locales se conservan durante las actualizaciones y la retirada.

## cambonos-graphical-base

- [ ] La instalación habilita `NetworkManager.service`, `bluetooth.service` y `avahi-daemon.service` cuando no están habilitados, sin iniciarlos ni reiniciarlos.
- [ ] Las unidades enmascaradas se conservan y generan un aviso.
- [ ] `mdns_minimal [NOTFOUND=return]` se añade después de `mymachines` en la línea `hosts:`.
- [ ] La configuración NSS es idempotente y se repara tras una transacción Pacman que actualiza `/etc/nsswitch.conf`.
- [ ] Las modificaciones administrativas de `/etc/nsswitch.conf` no se revierten sin una transacción que active el hook.
- [ ] Thunar conserva sus preferencias globales de vista, zoom, ubicación y navegación mediante `thunar.xml`.
- [ ] Thunar Volman activa el automontaje de unidades y medios extraíbles con los valores Xfconf globales.
- [ ] Las miniaturas de vídeo, fuentes, EPUB, ODF, RAW y PDF se generan en Thunar.
- [ ] GNOME Disk Utility, `htop` y `nvtop` están disponibles en el entorno gráfico.
- [ ] GNOME Keyring y libsecret están disponibles sin modificar PAM ni prometer desbloqueo automático.
- [ ] `thunar --daemon` se inicia en las sesiones gráficas compatibles con XDG Autostart.
- [ ] El agente `polkit-gnome` se inicia en las sesiones compatibles; comprobar la posible coexistencia con el autoinicio que proporciona `xfce4-session` sin desactivarlo preventivamente.
- [ ] Blueman Applet y NetworkManager Applet se inician en Qtile y XFCE.
- [ ] Los iconos de ambos applets se muestran en las zonas de notificación de Qtile y XFCE.
- [ ] PipeWire, PipeWire Pulse y WirePlumber funcionan en la sesión de usuario con audio ALSA, PulseAudio y JACK.
- [ ] GVFS permite acceder a recursos SMB, NFS, MTP, AFC, GPhoto2, DNS-SD y WSDD.
- [ ] Los portales XDG funcionan con la selección de backend definida por cada sesión.


## cambonos-xfce-conf

- [ ] LightDM ofrece la sesión `CambonOS XFCE` y la inicia mediante `cambonos-startxfce`.
- [ ] El wrapper prioriza `/etc/cambonos/xdg`, conserva `/etc/xdg` y los directorios XDG preexistentes.
- [ ] Las preferencias personales en `~/.config` prevalecen sobre los valores globales.
- [ ] Una cuenta nueva recibe el panel inferior de 35 px con los 13 elementos en el orden aprobado.
- [ ] Whisker muestra los favoritos Chromium, Thunar y XFCE Terminal y las acciones de configuración, bloqueo, greeter, perfil y cierre de sesión.
- [ ] La paleta del terminal coincide con los 16 colores canónicos de `cambonos-branding`; el fondo es transparente con oscurecimiento 0.95.
- [ ] Xfwm4 mantiene compositor, sombras, título centrado, un espacio de trabajo y las opacidades configuradas al 95 %.
- [ ] El wallpaper se aplica en la pantalla principal y el modo Zoom conserva proporciones y recorta el excedente.
- [ ] Los atajos de teclado conservados funcionan; Orca y MenuLibre no se instalan ni se invocan.
- [ ] Chromium se utiliza como navegador predeterminado de Exo y para HTTP/HTTPS; Thunar se utiliza para directorios y trash.
- [ ] Las configuraciones globales se actualizan sin migrar ni sobrescribir automáticamente perfiles personales existentes.
- [ ] La retirada del paquete no elimina perfiles personales ni recursos de usuario.

## cambonos-xfce

- [ ] El metapaquete instala `cambonos-base`, `cambonos-xfce-conf` y las aplicaciones generales seleccionadas.
- [ ] LibreOffice Fresh y Hunspell aparecen como dependencias opcionales, no obligatorias.
- [ ] Una instalación limpia del instalador selecciona `CambonOS XFCE` como sesión cuando se elige XFCE.
- [ ] La ISO instala el metapaquete XFCE sin clonar ni ejecutar el repositorio heredado `Cambon18/xfce`.
- [ ] Una actualización desde una instalación XFCE existente conserva los datos y preferencias del usuario.

## cambonos-keyring

- [x] Pacman incorpora la clave pública de CambonOS.
- [x] Pacman reconoce el material de confianza de CambonOS.
- [x] Pacman acepta paquetes y bases de datos firmados por la clave autorizada.
- [x] Pacman rechaza paquetes y bases de datos con firmas inválidas o no confiables.
- [x] La instalación o actualización ejecuta `pacman-key --populate cambonos` cuando el keyring local está inicializado.
- [x] La actualización del paquete aplica el material de confianza vigente.

## cambonos-base

- [x] La instalación de `cambonos-base` resuelve e instala sus siete dependencias CambonOS.
- [x] El metapaquete no instala archivos, ejecuta scripts ni proporciona hooks ALPM.
- [x] La instalación o retirada del metapaquete no cambia la shell de inicio de sesión de usuarios existentes.
- [x] `cambonos-grub` y `cambonos-plymouth` permanecen independientes.

## cambonos-mkiso

- [x] La comprobación de red live accede al mirror geo de Arch configurado para `[core]` y `[extra]`.
- [x] La actualización de `cambonos-installer` muestra la salida de Pacman y maneja correctamente errores.
- [x] El menú gráfico Syslinux BIOS muestra el fondo y los colores CambonOS legibles en hardware real.
- [x] Las entradas BIOS, UEFI y UEFI loopback arrancan sin copiar la imagen raíz a RAM y permiten instalar con el medio conectado.
- [x] La ISO arranca e instala correctamente en una máquina virtual o equipo de prueba, en BIOS y UEFI.

## Registro de verificación

Registrar aquí, por paquete, el entorno real utilizado y la fecha de la última comprobación funcional. No es necesario repetir las pruebas de funciones que no hayan podido verse afectadas por un cambio.

| Paquete | Entorno de prueba | Fecha | Observaciones |
|---|---|---|---|
| `cambonos-branding` | VM (iso-install) | 12/11/2026 | - |
| `cambonos-fastfetch` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-shell-prompt` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-zsh` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-release` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-pacman` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-grub` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-plymouth` | VM (iso-install) | 12/11/2026 | - |
| `cambonos-base` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-keyring` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-lightdm` | VM (iso-install) | 12/11/2026 | — |
| `cambonos-gtk-theme` | VM (iso-install) | 12/11/2026 | - |
| `cambonos-mkiso` | VM (iso-install) | 12/11/2026 | - |
