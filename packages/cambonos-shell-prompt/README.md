# cambonos-shell-prompt

Configuración de Starship que proporciona el prompt visual de CambonOS.

## Funciones

- Prompt de dos líneas con contexto Git, estado de comandos y datos del entorno.
- Los colores usan nombres ANSI y siguen la paleta activa del terminal.
- Las consolas virtuales Linux (`/dev/ttyN`) usan un perfil con símbolos ASCII; los emuladores (`/dev/pts/*`) conservan el perfil visual actual.
- Integración con Bash, Zsh y Fish.
- Respeta la configuración personal del usuario.

## Dependencias

`ttf-nerd-fonts-symbols-mono` proporciona los glifos de Nerd Fonts utilizados por los símbolos del prompt en terminales monoespaciadas.

`starship`, `bash`, `util-linux`, `ttf-nerd-fonts-symbols-mono`.
