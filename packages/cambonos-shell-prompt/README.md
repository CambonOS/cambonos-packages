# cambonos-shell-prompt

Instala Starship y proporciona el prompt predeterminado de CambonOS para Zsh, Bash y Fish.

## Responsabilidad

Este paquete es propietario de la configuración visual de Starship y de sus integraciones. No instala ni configura Zsh, Bash o Fish. La integración de cada shell se realiza de forma independiente cuando su punto de entrada está disponible.

## Dependencias

**Obligatorias**
- `starship`
- `bash`
- `util-linux` (proporciona `flock`)

**Opcionales**
- `fish`: integración automática en sesiones interactivas de Fish.

`cambonos-shell-prompt` no depende de `cambonos-zsh`. Sin embargo, `cambonos-zsh` depende de este paquete para garantizar el prompt esperado al instalar la experiencia Zsh de CambonOS.

## Archivos instalados

| Ruta | Función |
|---|---|
| `/usr/share/cambonos/shell-prompt/starship.toml` | Configuración visual predeterminada de CambonOS. |
| `/usr/bin/cambonos-starship-directory` | Módulo personalizado para colorear y truncar la ruta actual. |
| `/usr/share/cambonos/shell-prompt/shell/bash` | Fragmento de inicialización Bash. |
| `/usr/share/cambonos/zsh/conf.d/50-shell-prompt.zsh` | Fragmento para el cargador de `cambonos-zsh`. |
| `/usr/share/fish/vendor_conf.d/cambonos-shell-prompt.fish` | Integración nativa de Fish. |
| `/usr/lib/cambonos/shell-prompt/integrate-bash` | Gestor del bloque Bash. |
| `/usr/share/libalpm/hooks/cambonos-shell-prompt.hook` | Reparación tras actualizaciones de Bash. |

## Configuración predeterminada

La configuración mantiene la paleta `cambonos` y un prompt de dos líneas. La primera línea coloca el directorio y el contexto Git a la izquierda; Python, metadatos de PKGBUILD/paquetes, usuario y host SSH se alinean a la derecha mediante `$fill`. La segunda línea conserva el carácter de entrada a la izquierda y el estado de salida, trabajos y duración a la derecha.

El directorio se representa mediante `cambonos-starship-directory`: muestra hasta cuatro carpetas, con las tres anteriores en `deep_blue` y la carpeta actual en `accent`. El directorio HOME utiliza un icono de casa. El script sanitiza caracteres de control en nombres de carpeta antes de emitir sus secuencias ANSI. No requiere una Nerd Font: los glifos pueden sustituirse visualmente si la fuente de terminal no los incluye.

La configuración personal tiene prioridad:

1. Se respeta `STARSHIP_CONFIG` si ya está definido.
2. Si existe `$XDG_CONFIG_HOME/starship.toml` (o `~/.config/starship.toml`), se utiliza esa configuración.
3. En caso contrario, se establece `/usr/share/cambonos/shell-prompt/starship.toml` como fallback.

La variable se establece durante el inicio de la shell y puede redefinirse posteriormente desde la configuración personal.

## Integración por shell

- **Bash:** bloque delimitado en `/etc/bash.bashrc`, que carga el fragmento del paquete.
- **Zsh:** fragmento en `/usr/share/cambonos/zsh/conf.d/50-shell-prompt.zsh`, cargado por `cambonos-zsh`.
- **Fish:** archivo en `vendor_conf.d`, cargado por Fish en sesiones interactivas.

Si Zsh está instalado sin `cambonos-zsh`, el fragmento queda disponible pero no se carga automáticamente. Para integrarlo manualmente, añade lo siguiente a `~/.zshrc`:

```zsh
source /usr/share/cambonos/zsh/conf.d/50-shell-prompt.zsh
```

La instalación de este paquete no fuerza la instalación de Zsh ni Fish. Bash forma parte de las dependencias del paquete porque se proporciona una integración administrada para esa shell.

## Política de configuración y ciclo de vida

El bloque Bash utiliza marcadores propios y el bloqueo compartido `/run/lock/cambonos-shell-integration.lock`. Las operaciones son idempotentes, atómicas y preservan el contenido externo. El helper rechaza enlaces simbólicos, archivos no regulares y marcadores incompletos o duplicados.

- `post_install`: instala la integración Bash.
- `post_upgrade`: repara la integración Bash.
- `pre_remove`: retira exclusivamente el bloque del paquete.
- Hook ALPM: repara el bloque después de instalar o actualizar Bash.

Los fragmentos Zsh y Fish son archivos propiedad del paquete y se retiran mediante pacman. No se modifican archivos personales.

## Comprobación

```bash
sudo /usr/lib/cambonos/shell-prompt/integrate-bash check
pacman -Qkk cambonos-shell-prompt
```
