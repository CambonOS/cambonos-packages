# Checklist funcional de paquetes CambonOS

Este documento registra las funciones de los paquetes y si han sido verificadas en un entorno real. No es una guía de instalación ni una lista de tareas de publicación.

Marca una función únicamente cuando se haya comprobado su funcionamiento en un sistema Arch de pruebas. Una función implementada pero no probada debe permanecer pendiente. Antes de fusionar `dev` en `main`, deben estar verificadas todas las funciones que formen parte del alcance soportado de esa versión. Las pruebas que dependan de capacidades todavía no soportadas pueden permanecer pendientes únicamente si la limitación está documentada y su exclusión del alcance ha sido aceptada expresamente; no deben marcarse como verificadas. Toda función nueva debe añadirse aquí y probarse antes de ese merge.

- `[ ]` Pendiente de verificación funcional.
- `[x]` Verificada en un entorno real.

Anota el entorno y la fecha de la comprobación en el registro del paquete. Si una función no existe todavía, no debe marcarse como verificada.

## cambonos-branding

- [x] Los recursos SVG de identidad se muestran correctamente.
- [x] Los recursos PNG de identidad se muestran correctamente.
- [ ] La paleta ANSI de CambonOS se aplica a cada TTY virtual al inicializarse.
- [ ] Los 16 colores de consola corresponden a la paleta publicada.
- [ ] `dialog` aplica el tema CambonOS de `/etc/dialogrc`.
- [ ] Xfce Terminal aplica la paleta CambonOS como predeterminado global cuando está instalado.
- [ ] La configuración global previa se restaura al retirar `xfce4-terminal` o `cambonos-branding`.
- [ ] Las preferencias de usuario y las opciones globales ajenas a la paleta se conservan.

## cambonos-gtk-theme

Alcance del paquete: una única variante (`CambonOS-dark`) con recursos GTK 3,
GTK 4 y Xfwm4. GTK 2 no forma parte del alcance: no se incluye
`gtk-2.0/gtkrc`. La validación estructural ejecutada durante la construcción
no sustituye las comprobaciones visuales en una sesión real.

- [x] La instalación deja únicamente `CambonOS-dark` en `/usr/share/themes/` y la licencia en `/usr/share/licenses/cambonos-gtk-theme/`.
- [x] La instalación no modifica preferencias de usuario ni archivos de configuración global de GTK.
- [x] GTK 3 carga los recursos del tema en aplicaciones compatibles de una sesión XFCE real.
- [x] GTK 4 carga los recursos del tema en aplicaciones compatibles probadas; no implica compatibilidad completa con aplicaciones libadwaita.
- [x] La selección del tema requiere acción del usuario; el paquete no fuerza un tema ni sustituye la configuración local del escritorio.
- [x] La retirada elimina los recursos instalados sin alterar la configuración previa del sistema ni de los usuarios.
- [ ] Xfwm4 representa correctamente las decoraciones y todos los estados de los botones en una sesión real (activa/inactiva, maximizar, minimizar, cerrar, sombrear y fijar).
- [ ] La banda de selección al arrastrar en el escritorio XFCE muestra el relleno translúcido y el borde turquesa del tema.
- [ ] La legibilidad y el contraste de texto, menús, tooltips, entradas y controles se mantienen con las superficies translúcidas definidas en la paleta.
- [ ] La selección del tema en Apariencia y Gestor de ventanas persiste tras cerrar sesión e iniciar de nuevo.

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
- [X] Comprobar que en dev activa el repo testing y que en main activa el repo stable. Se hace mediante el workflow.

## cambonos-grub

- [x] GRUB aplica la configuración predeterminada de CambonOS.
- [x] El menú de GRUB muestra correctamente el tema CambonOS.
- [x] Los iconos de los sistemas operativos se muestran correctamente.
- [x] GRUB detecta otros sistemas operativos cuando `os-prober` está disponible.
- [x] La configuración del menú se regenera después de los cambios de kernel.
- [x] El sistema puede arrancar correctamente con la configuración generada.

## cambonos-plymouth

- [ ] Plymouth muestra correctamente el tema CambonOS durante el arranque.
- [ ] Los recursos gráficos de CambonOS se cargan desde el initramfs.
- [ ] El logo, la barra y el fondo se adaptan correctamente a distintas resoluciones.
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
- [X] La instalación conserva un display manager previamente seleccionado.
- [x] Las actualizaciones y la retirada respetan el estado de activación del servicio.
- [x] Las configuraciones locales se conservan durante las actualizaciones y la retirada.

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

- [ ] La comprobación de red live accede al mirror geo de Arch configurado para `[core]` y `[extra]`.
- [ ] La actualización de `cambonos-installer` muestra la salida de Pacman y maneja correctamente errores.
- [ ] El menú gráfico Syslinux BIOS muestra el fondo y los colores CambonOS legibles en hardware real.
- [ ] Las entradas BIOS, UEFI y UEFI loopback arrancan sin copiar la imagen raíz a RAM y permiten instalar con el medio conectado.
- [ ] La ISO arranca e instala correctamente en una máquina virtual o equipo de prueba, en BIOS y UEFI.

## Registro de verificación

Registrar aquí, por paquete, el entorno real utilizado y la fecha de la última comprobación funcional. No es necesario repetir las pruebas de funciones que no hayan podido verse afectadas por un cambio.

| Paquete | Entorno de prueba | Fecha | Observaciones |
|---|---|---|---|
| `cambonos-branding` | VM (iso-install) | 07/11/2026 | Paletas TTY y Xfce Terminal pendientes de verificación funcional (09/11/2026) |
| `cambonos-fastfetch` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-shell-prompt` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-zsh` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-release` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-pacman` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-grub` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-plymouth` | VM (iso-install) | 07/11/2026 | Cambios recientes pendientes de verificación funcional (09/11/2026) |
| `cambonos-base` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-keyring` | VM (iso-install) | 07/11/2026 | — |
| `cambonos-lightdm` | VM (iso-install) | 08/11/2026 | - |
| `cambonos-gtk-theme` | VM (iso-install) | 08/11/2026 | GTK 3/4 y retirada comprobados; validación visual completa de Xfwm4, selección XFCE y contraste/translucidez pendientes |
| `cambonos-mkiso` | Pendiente de prueba real | — | Verificaciones funcionales pendientes |
