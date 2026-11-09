# Checklist funcional de paquetes CambonOS

Este documento registra las funciones de los paquetes y si han sido verificadas en un entorno real. No es una guía de instalación ni una lista de tareas de publicación.

Marca una función únicamente cuando se haya comprobado su funcionamiento en un sistema Arch de pruebas. Una función implementada pero no probada debe permanecer pendiente. Antes de fusionar `dev` en `main`, deben estar verificadas todas las funciones que formen parte del alcance soportado de esa versión. Las pruebas que dependan de capacidades todavía no soportadas pueden permanecer pendientes únicamente si la limitación está documentada y su exclusión del alcance ha sido aceptada expresamente; no deben marcarse como verificadas. Toda función nueva debe añadirse aquí y probarse antes de ese merge.

- `[ ]` Pendiente de verificación funcional.
- `[x]` Verificada en un entorno real.

Anota el entorno y la fecha de la comprobación en el registro del paquete. Si una función no existe todavía, no debe marcarse como verificada.

## cambonos-branding

- [x] Los recursos SVG de identidad se muestran correctamente.
- [x] Los recursos PNG de identidad se muestran correctamente.
- [x] La fuente CambonOS Symbols se reconoce y sus glifos se representan correctamente.
- [x] Fontconfig encuentra y aplica la configuración de la fuente.
- [ ] La paleta ANSI de CambonOS se aplica a cada TTY virtual al inicializarse.
- [ ] Los 16 colores de consola corresponden a la paleta publicada.
- [ ] Xfce Terminal aplica la paleta CambonOS como predeterminado global cuando está instalado.
- [ ] La configuración global previa se restaura al retirar `xfce4-terminal` o `cambonos-branding`.
- [ ] Las preferencias de usuario y las opciones globales ajenas a la paleta se conservan.

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

## cambonos-gtk-theme

- [x] La instalación deja el tema `CambonOS-Dark` en `/usr/share/themes/` sin tocar preferencias del usuario ni archivos de configuración global de GTK.
- [x] GTK 2, GTK 3, GTK 4 y XFWM4 reconocen el tema y cargan sus recursos sin errores de lectura ni rutas rotas.
- [x] La paleta oficial de CambonOS se aplica de forma consistente en ventanas, controles y paneles de una sesión XFCE real.
- [x] La selección del tema requiere acción del usuario; el paquete no fuerza un tema ni sustituye la configuración local del escritorio.
- [x] Las aplicaciones GTK y los componentes de escritorio muestran el modo oscuro con la identidad CambonOS sin forzar acentos o esquemas ajenos.
- [x] La retirada del paquete elimina los recursos del tema sin alterar la configuración previa del sistema ni de los usuarios.

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
| `cambonos-gtk-theme` | VM (iso-install) | 08/11/2026 | - |
