# cambonos-fastfetch

Perfil de Fastfetch con la identidad visual de CambonOS e integración en shells.

## Funcionalidad

- Logotipo y configuración de Fastfetch.
- Colores basados en nombres ANSI, para respetar la paleta activa del terminal.
- Ejecución automática en los contextos de shell compatibles.
- Integración con Bash y, de forma opcional, con Zsh y Fish.

La integración de Zsh requiere `cambonos-zsh`; la de Fish requiere Fish instalado. El
paquete no sustituye la configuración personal de esas shells.

## Dependencias

Obligatorias: `fastfetch`, `cambonos-release`, `bash` y `util-linux`.

Opcionales: `fish` y `cambonos-zsh` para habilitar sus integraciones respectivas.
