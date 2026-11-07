# Checklist funcional de paquetes CambonOS

Este documento registra las funciones de los paquetes y si han sido verificadas en un entorno real. No es una guía de instalación ni una lista de tareas de publicación.

Marca una función únicamente cuando se haya comprobado su funcionamiento en un sistema Arch de pruebas. Una función implementada pero no probada debe permanecer pendiente. Antes de fusionar `dev` en `main`, todas las funciones de esta checklist deben estar verificadas. Toda función nueva debe añadirse aquí y probarse antes de ese merge.

- `[ ]` Pendiente de verificación funcional.
- `[x]` Verificada en un entorno real.

Anota el entorno y la fecha de la comprobación en el registro del paquete. Si una función no existe todavía, no debe marcarse como verificada.

## cambonos-branding

- [ ] Los recursos SVG de identidad se muestran correctamente.
- [ ] Los recursos PNG de identidad se muestran correctamente.
- [ ] La fuente CambonOS Symbols se reconoce y sus glifos se representan correctamente.
- [ ] Fontconfig encuentra y aplica la configuración de la fuente.

## cambonos-fastfetch

- [ ] Fastfetch muestra la identidad y el logotipo de CambonOS.
- [ ] Fastfetch muestra correctamente la información principal del sistema.
- [ ] Fastfetch se ejecuta en las sesiones de login compatibles mediante `/etc/profile.d/`.
- [ ] La integración automática funciona en sesiones interactivas de Bash.
- [ ] La integración automática funciona en sesiones interactivas de Zsh cuando está instalado `cambonos-zsh`.
- [ ] La integración automática funciona en sesiones interactivas de Fish.
- [ ] La integración de shells puede activarse y retirarse sin alterar configuraciones ajenas.

## cambonos-shell-prompt

- [ ] Starship utiliza la configuración visual predeterminada de CambonOS.
- [ ] El prompt funciona en sesiones interactivas de Bash.
- [ ] El prompt funciona en sesiones interactivas de Zsh cuando está instalado `cambonos-zsh`.
- [ ] El prompt funciona en sesiones interactivas de Fish.
- [ ] El directorio actual y sus directorios padre se representan correctamente.
- [ ] Se respeta la configuración personal de Starship del usuario.

## cambonos-zsh

- [ ] Zsh carga la configuración global de CambonOS.
- [ ] El sistema de autocompletado funciona.
- [ ] Los atajos de teclado configurados funcionan.
- [ ] El historial persistente funciona.
- [ ] Autosuggestions y syntax highlighting funcionan.
- [ ] Los fragmentos de integración de otros paquetes se cargan en el orden previsto.
- [ ] La configuración personal del usuario se mantiene independiente de la configuración global.
- [ ] Las operaciones de pacman que modifican el sistema solicitan privilegios cuando corresponde.

## cambonos-release

- [ ] El sistema muestra la identidad CambonOS mediante `/etc/os-release`.
- [ ] Los metadatos LSB de CambonOS están disponibles cuando se instala el componente correspondiente.
- [ ] La identidad CambonOS se mantiene tras las transacciones de paquetes que afectan a los archivos de identidad.
- [ ] La retirada del paquete restaura la identidad anterior cuando corresponde.

## cambonos-pacman

- [ ] El repositorio stable de CambonOS aparece configurado y habilitado.
- [ ] El repositorio testing puede habilitarse mediante su configuración.
- [ ] Pacman aplica las opciones diferenciales de CambonOS.
- [ ] Pacman conserva la verificación obligatoria de firmas de los repositorios CambonOS.
- [ ] La integración con `/etc/pacman.conf` funciona sin eliminar configuraciones manuales del administrador.
- [ ] La transición desde la configuración anterior `cambonos-repo` conserva el funcionamiento esperado.

## cambonos-grub

- [ ] GRUB aplica la configuración predeterminada de CambonOS.
- [ ] El menú de GRUB muestra correctamente el tema CambonOS.
- [ ] Los iconos de los sistemas operativos se muestran correctamente.
- [ ] GRUB detecta otros sistemas operativos cuando `os-prober` está disponible.
- [ ] La configuración del menú se regenera después de los cambios de kernel.
- [ ] El sistema puede arrancar correctamente con la configuración generada.

## cambonos-plymouth

- [ ] Plymouth selecciona y muestra el tema CambonOS.
- [ ] La animación y la barra de progreso se muestran correctamente durante el arranque.
- [ ] Los diálogos de teclado y desbloqueo muestran los recursos gráficos esperados.
- [ ] La integración con mkinitcpio incorpora Plymouth a las imágenes initramfs.
- [ ] La configuración de Plymouth funciona con el orden de hooks previsto, también en sistemas cifrados.
- [ ] La selección de tema del administrador se conserva durante las actualizaciones.

## cambonos-keyring

- [ ] Pacman incorpora la clave pública de CambonOS.
- [ ] Pacman reconoce el material de confianza de CambonOS.
- [ ] Pacman acepta paquetes y bases de datos firmados por la clave autorizada.
- [ ] Pacman rechaza paquetes y bases de datos con firmas inválidas o no confiables.
- [ ] La instalación o actualización ejecuta `pacman-key --populate cambonos` cuando el keyring local está inicializado.
- [ ] La actualización del paquete aplica el material de confianza vigente.

## cambonos-base

- [ ] La instalación de `cambonos-base` resuelve e instala sus siete dependencias CambonOS.
- [ ] El metapaquete no instala archivos, ejecuta scripts ni proporciona hooks ALPM.
- [ ] La instalación o retirada del metapaquete no cambia la shell de inicio de sesión de usuarios existentes.
- [ ] `cambonos-grub` y `cambonos-plymouth` permanecen independientes.

## Registro de verificación

Registrar aquí, por paquete, el entorno real utilizado y la fecha de la última comprobación funcional. No es necesario repetir las pruebas de funciones que no hayan podido verse afectadas por un cambio.

| Paquete | Entorno de prueba | Fecha | Observaciones |
|---|---|---|---|
| `cambonos-branding` | Pendiente | — | — |
| `cambonos-fastfetch` | Pendiente | — | — |
| `cambonos-shell-prompt` | Pendiente | — | — |
| `cambonos-zsh` | Pendiente | — | — |
| `cambonos-release` | Pendiente | — | — |
| `cambonos-pacman` | Pendiente | — | — |
| `cambonos-grub` | Pendiente | — | — |
| `cambonos-plymouth` | Pendiente | — | — |
| `cambonos-base` | Pendiente | — | — |
| `cambonos-keyring` | Pendiente | — | — |
