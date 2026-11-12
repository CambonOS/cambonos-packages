# cambonos-shell-prompt

Configuración de Starship que proporciona el prompt visual de CambonOS.

## Funcionalidad

- Prompt de dos líneas con contexto Git, estado de comandos e información del entorno.
- Colores basados en nombres ANSI para seguir la paleta activa del terminal.
- Integración con Bash, Zsh y Fish.
- Perfil compatible con consolas virtuales Linux (`/dev/ttyN`); los emuladores
  (`/dev/pts/*`) mantienen el perfil visual habitual.
- Respeta la configuración personal de Starship del usuario.

El paquete proporciona los fragmentos de integración comunes. La integración de Zsh se
completa con `cambonos-zsh`.

## Dependencias

Obligatorias: `starship`, `bash`, `util-linux` y `ttf-nerd-fonts-symbols-mono`.

Opcional: `fish` para su integración automática.
