# cambonos-fastfetch

Perfil visual de Fastfetch e integración automática para shells interactivos de CambonOS.

## Responsabilidad

Este paquete instala la configuración y el logotipo utilizados por Fastfetch, un lanzador `cambonos-fastfetch` y mecanismos para integrar su ejecución en sesiones interactivas de Bash, Zsh, Fish y shells POSIX de login.

## Dependencias

**Obligatorias**
- `fastfetch`
- `cambonos-release`
- `bash`
- `util-linux` (proporciona `flock`)

**Opcionales**
- `fish`: integración automática en sesiones interactivas de Fish.
- `zsh`: integración automática en sesiones interactivas de Zsh.

## Archivos instalados

| Ruta | Función |
|---|---|
| `/usr/bin/cambonos-fastfetch` | Ejecuta Fastfetch con el perfil CambonOS. |
| `/usr/share/cambonos/fastfetch/config.jsonc` | Configuración JSONC. |
| `/usr/share/cambonos/fastfetch/logo.txt` | Logotipo textual. |
| `/usr/share/cambonos/fastfetch/shell/bash` | Fragmento para Bash. |
| `/usr/share/cambonos/fastfetch/shell/zsh` | Fragmento para Zsh. |
| `/etc/profile.d/cambonos-fastfetch.sh` | Integración de shells POSIX de login. |
| `/usr/share/fish/vendor_conf.d/cambonos-fastfetch.fish` | Integración de Fish. |
| `/usr/lib/cambonos/fastfetch/integrate-shells` | Gestor de bloques globales. |
| `/usr/share/libalpm/hooks/cambonos-fastfetch.hook` | Reparación tras actualizaciones de Bash/Zsh. |

El gestor administra bloques marcados en `/etc/bash.bashrc` y `/etc/zsh/zshrc`.

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

`check` devuelve error si falta alguna integración aplicable a los shells instalados. Los shells opcionales ausentes se omiten.

## Política de configuración

La configuración JSONC y el logotipo son recursos propiedad del paquete en `/usr/share`; las actualizaciones pueden reemplazarlos.

Los bloques administrados de `/etc/bash.bashrc` y `/etc/zsh/zshrc` están delimitados por marcadores. El gestor reemplaza el contenido dentro de esos bloques durante `repair`, pero conserva el contenido exterior. No se deben realizar personalizaciones locales dentro del bloque administrado; deben colocarse fuera de él.

El gestor rechaza enlaces simbólicos y archivos que no sean regulares en los puntos globales que modifica. También rechaza marcadores incompletos o duplicados en lugar de intentar reparar contenido ambiguo.

Los archivos de `/etc/profile.d` y `vendor_conf.d` son payload del paquete. Deben tratarse como integración del sistema, no como configuración personal.

## Actualización y eliminación

- `post_install`: ejecuta `install`.
- `post_upgrade`: ejecuta `repair`.
- `pre_remove`: ejecuta `remove`.
- El hook ALPM se ejecuta después de transacciones que instalan o actualizan Bash o Zsh y repara los bloques administrados.

Si la integración falla, el scriptlet informa del problema y permite continuar la transacción. Después se puede ejecutar `integrate-shells repair` manualmente.

## Incidencia conocida de la configuración

La configuración JSONC de la instantánea auditada contiene una coma final en el objeto `display`. Está prevista su corrección en la próxima versión y no se considera un fallo bloqueante conocido de esta versión. La validación debe realizarse con Fastfetch y no con un parser JSON estricto. La configuración también referencia el esquema remoto `dev` de Fastfetch, por lo que conviene validar compatibilidad con la versión instalada.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-fastfetch

cambonos-fastfetch
sudo /usr/lib/cambonos/fastfetch/integrate-shells check
pacman -Qkk cambonos-fastfetch
```

Para desactivar el inicio automático en una sesión:

```bash
export CAMBONOS_NO_FASTFETCH=1
```

## Pruebas de validación

- [ ] Construcción correcta con `makepkg`.
- [ ] Dependencias obligatorias resueltas y opcionales identificadas.
- [ ] `cambonos-fastfetch` ejecuta Fastfetch con el archivo de configuración esperado.
- [ ] Fastfetch acepta la configuración JSONC y carga `logo.txt`.
- [ ] Se verifica la salida visual en terminales con distintos tamaños y capacidades de color.
- [ ] Bash interactivo ejecuta Fastfetch una sola vez.
- [ ] Bash no interactivo no lo ejecuta.
- [ ] Zsh interactivo ejecuta Fastfetch una sola vez.
- [ ] Zsh no interactivo no lo ejecuta.
- [ ] Fish interactivo ejecuta Fastfetch una sola vez.
- [ ] Fish no interactivo no lo ejecuta.
- [ ] Shell POSIX de login ejecuta Fastfetch una sola vez cuando carga `/etc/profile`.
- [ ] La variable `CAMBONOS_NO_FASTFETCH` desactiva la ejecución en Bash, Zsh, Fish y login POSIX.
- [ ] `_CAMBONOS_FASTFETCH_RAN` evita ejecuciones duplicadas entre `/etc/profile` y el rc del shell.
- [ ] `install` añade los bloques administrados sin borrar contenido preexistente.
- [ ] `repair` es idempotente.
- [ ] `remove` elimina solo los bloques administrados y conserva el resto.
- [ ] Marcadores incompletos, duplicados o desordenados provocan fallo conservador sin reescribir el archivo.
- [ ] Un enlace simbólico o directorio en `/etc/bash.bashrc` o `/etc/zsh/zshrc` no se reemplaza.
- [ ] Se comprueba el comportamiento con Bash/Zsh instalados y con cada shell opcional ausente/presente.
- [ ] El hook ALPM repara la integración después de actualizar Bash.
- [ ] El hook ALPM repara la integración después de actualizar Zsh.
- [ ] Una instalación/actualización con fallo de integración muestra un mensaje útil y no deja una transacción silenciosamente incompleta.
- [ ] La desinstalación elimina los bloques administrados y no elimina configuraciones ajenas.
- [ ] `pacman -Qkk cambonos-fastfetch` no detecta daños inesperados.

## Limitaciones

Las pruebas de shell deben realizarse en sesiones reales; los tests unitarios del gestor Python no validan automáticamente todos los caminos de inicio de Bash, Zsh, Fish y POSIX.
