# cambonos-zsh

Configuración global de Zsh para ofrecer una experiencia interactiva coherente en
CambonOS.

## Funcionalidad

- Configura autocompletado, historial persistente y atajos de teclado.
- Integra autosuggestions y resaltado de sintaxis.
- Carga fragmentos de integración instalados por otros paquetes CambonOS.
- Añade elevación de privilegios para las operaciones de Pacman que modifican el
  sistema.
- Mantiene la configuración global separada de las preferencias personales del usuario.

La configuración predeterminada para cuentas nuevas se instala en `/etc/skel/.zshrc`. El
paquete no cambia la shell de inicio de sesión de usuarios existentes.

## Dependencias

`zsh`, `zsh-completions`, `zsh-autosuggestions`, `zsh-syntax-highlighting`,
`cambonos-shell-prompt`, `util-linux` y `sudo`.
