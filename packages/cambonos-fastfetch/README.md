# cambonos-fastfetch

Perfil visual de Fastfetch e integración automática para las shells interactivas de CambonOS.

## Responsabilidad

Este paquete instala la configuración y el logotipo utilizados por Fastfetch, el lanzador `cambonos-fastfetch` y sus integraciones de inicio. No administra la configuración general de Zsh ni de Starship.

## Dependencias

**Obligatorias**
- `fastfetch`
- `cambonos-release`
- `bash`
- `util-linux` (proporciona `flock`)

**Opcionales**
- `fish`: integración automática en sesiones interactivas de Fish.
- `cambonos-zsh`: cargador global para la integración automática en Zsh.

## Archivos instalados

| Ruta | Función |
|---|---|
| `/usr/bin/cambonos-fastfetch` | Ejecuta Fastfetch con el perfil CambonOS. |
| `/usr/share/cambonos/fastfetch/config.jsonc` | Configuración JSONC. |
| `/usr/share/cambonos/fastfetch/logo.txt` | Logotipo textual. |
| `/usr/share/cambonos/fastfetch/shell/bash` | Fragmento para Bash. |
| `/usr/share/cambonos/zsh/conf.d/60-fastfetch.zsh` | Fragmento para el cargador de `cambonos-zsh`. |
| `/etc/profile.d/cambonos-fastfetch.sh` | Integración de shells POSIX de login. |
| `/usr/share/fish/vendor_conf.d/cambonos-fastfetch.fish` | Integración de Fish. |
| `/usr/lib/cambonos/fastfetch/integrate-shells` | Gestor de integración Bash y migración de la antigua integración Zsh. |
| `/usr/share/libalpm/hooks/cambonos-fastfetch.hook` | Reparación tras actualizaciones de Bash. |

## Comportamiento

- Se ejecuta únicamente en sesiones interactivas.
- `CAMBONOS_NO_FASTFETCH` con cualquier valor no vacío desactiva la ejecución automática.
- `_CAMBONOS_FASTFETCH_RAN` evita una segunda ejecución en la misma sesión cuando se atraviesan varios puntos de inicio.
- El comando puede ejecutarse manualmente independientemente de la integración automática:

```bash
cambonos-fastfetch
```

El gestor soporta:

```bash
sudo /usr/lib/cambonos/fastfetch/integrate-shells install
sudo /usr/lib/cambonos/fastfetch/integrate-shells repair
sudo /usr/lib/cambonos/fastfetch/integrate-shells check
sudo /usr/lib/cambonos/fastfetch/integrate-shells remove
```

## Integración Zsh

El paquete instala su fragmento en `/usr/share/cambonos/zsh/conf.d/60-fastfetch.zsh`. Cuando `cambonos-zsh` está instalado, su cargador lo ejecuta automáticamente. Si Zsh está instalado sin `cambonos-zsh`, el fragmento queda disponible pero debe integrarse manualmente desde `~/.zshrc`:

```zsh
source /usr/share/cambonos/zsh/conf.d/60-fastfetch.zsh
```

Al actualizar desde versiones anteriores, `post_upgrade` retira automáticamente el antiguo bloque Fastfetch de `/etc/zsh/zshrc`. La migración conserva el cargador de `cambonos-zsh` y cualquier contenido ajeno al bloque antiguo. Si los marcadores anteriores están incompletos, duplicados o alterados, la operación falla de forma conservadora y no reescribe el archivo.

## Política de configuración

El bloque administrado de `/etc/bash.bashrc` está delimitado por marcadores. El gestor reemplaza el contenido dentro de ese bloque durante `repair`, pero conserva el contenido exterior. No se deben realizar personalizaciones locales dentro del bloque administrado; deben colocarse fuera de él.

El helper utiliza el bloqueo compartido `/run/lock/cambonos-shell-integration.lock`, escrituras atómicas y rechaza enlaces simbólicos, archivos no regulares y marcadores ambiguos. No modifica `/etc/zsh/zshrc`: esa ruta pertenece exclusivamente al cargador de `cambonos-zsh`.

Los archivos de `/etc/profile.d` y `vendor_conf.d` son payload del paquete. Deben tratarse como integración del sistema, no como configuración personal.

## Actualización y eliminación

- `post_install`: instala el bloque Bash y elimina cualquier resto de la antigua integración Zsh.
- `post_upgrade`: repara Bash y realiza la migración de la integración Zsh antigua.
- `pre_remove`: retira el bloque Bash y cualquier resto del bloque Zsh antiguo.
- El hook ALPM repara la integración Bash después de instalar o actualizar Bash.

Si la integración falla, el scriptlet informa del problema y permite continuar la transacción. Después se puede ejecutar `integrate-shells repair` manualmente.

## Comprobación

```bash
sudo /usr/lib/cambonos/fastfetch/integrate-shells check
cambonos-fastfetch
pacman -Qkk cambonos-fastfetch
```
