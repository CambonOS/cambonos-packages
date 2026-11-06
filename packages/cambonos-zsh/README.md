# cambonos-zsh

Configuración global de Zsh para CambonOS.

## Responsabilidad

Este paquete instala Zsh y la experiencia interactiva predeterminada de CambonOS. Mantiene el único punto de entrada global de Zsh y proporciona el directorio compartido `conf.d` para que otros paquetes puedan añadir integraciones independientes.

No instala ni configura directamente Fastfetch. Starship se proporciona mediante `cambonos-shell-prompt`, que es una dependencia obligatoria. Instala un `.zshrc` vacío en `/etc/skel` para que los nuevos usuarios reciban un archivo personal inicial sin imponer ajustes adicionales.

## Dependencias

- `zsh`
- `zsh-completions`
- `zsh-autosuggestions`
- `zsh-syntax-highlighting`
- `cambonos-shell-prompt`
- `util-linux` (proporciona `flock` para la gestión segura del punto de entrada)

## Archivos instalados

| Ruta | Función |
|---|---|
| `/etc/zsh/zshrc` | Bloque de entrada global administrado por el paquete; se crea si no existe. |
| `/etc/skel/.zshrc` | Archivo vacío que se copia al crear nuevos usuarios mediante `/etc/skel`. |
| `/usr/share/cambonos/zsh/conf.d/10-completion.zsh` | Inicialización de completions y caché por usuario. |
| `/usr/share/cambonos/zsh/conf.d/20-keybindings.zsh` | Modo Emacs y teclas Home, End, Delete, PageUp y PageDown. |
| `/usr/share/cambonos/zsh/conf.d/30-history.zsh` | Historial, opciones y aliases predeterminados. |
| `/usr/share/cambonos/zsh/conf.d/40-plugins.zsh` | Autosuggestions y syntax highlighting. |
| `/usr/lib/cambonos/zsh/integrate-zsh` | Gestor idempotente del bloque global. |

Los paquetes que necesiten integrar componentes en Zsh instalan sus propios fragmentos en `/usr/share/cambonos/zsh/conf.d/`. No deben modificar `/etc/zsh/zshrc`.

## Configuración

El bloque global se ejecuta antes de `~/.zshrc`. Por tanto, los usuarios pueden personalizar opciones, aliases, funciones, variables y comportamiento del prompt desde su archivo personal. El paquete proporciona un `.zshrc` vacío en `/etc/skel`; no modifica los archivos personales de usuarios existentes.

La configuración incluye:

- `autocd` y corrección interactiva de comandos.
- Historial persistente de 100.000 entradas en `${ZDOTDIR:-$HOME}/.zsh_history`.
- Completions adicionales y menú de selección.
- Modo de edición Emacs.
- Home y End para principio/final de la línea actual.
- Delete para borrar el carácter bajo el cursor.
- PageUp y PageDown para buscar en el historial por el prefijo escrito.
- `zsh-autosuggestions` y `zsh-syntax-highlighting`.

No se fuerza `EDITOR`, no se cambia la shell de ninguna cuenta y no se modifica `/etc/default/useradd`. La shell predeterminada se decide en el instalador ISO.

## Integración de componentes

El cargador procesa los archivos `*.zsh` en orden lexicográfico. Los nombres deben utilizar prefijos numéricos para expresar el orden. Los fragmentos de otros paquetes se instalan y eliminan independientemente.

Ejemplos:

- `cambonos-shell-prompt`: `50-shell-prompt.zsh`.
- `cambonos-fastfetch`: `60-fastfetch.zsh`.

Si se instala uno de esos paquetes sin `cambonos-zsh`, el fragmento queda disponible pero no se carga automáticamente. El usuario puede integrarlo manualmente desde `~/.zshrc`, por ejemplo:

```zsh
source /usr/share/cambonos/zsh/conf.d/50-shell-prompt.zsh
```

## Política de configuración y ciclo de vida

El helper administra un bloque delimitado en `/etc/zsh/zshrc`, con bloqueo compartido `/run/lock/cambonos-shell-integration.lock`, validación conservadora de marcadores y escritura atómica. Preserva el contenido externo al bloque y rechaza enlaces simbólicos, directorios y marcadores ambiguos.

- `post_install`: instala el bloque.
- `post_upgrade`: repara el bloque.
- `pre_remove`: retira exclusivamente el bloque.

Si el helper creó `/etc/zsh/zshrc` y, al retirar el bloque, no queda contenido ajeno, elimina ese archivo. Si el archivo ya existía o contiene configuración externa, lo conserva.

## Comprobación

```bash
sudo /usr/lib/cambonos/zsh/integrate-zsh check
pacman -Qkk cambonos-zsh
```
