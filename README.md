# CambonOS Packages

Repositorio de paquetes e infraestructura de construcción de CambonOS, una distribución basada en Arch Linux rolling release.

## Estructura

```text
cambonos-packages/
├── packages/
│   ├── cambonos-release/
│   │   ├── PKGBUILD
│   │   ├── cambonos-release.install
│   │   └── files/
│   └── cambonos-fastfetch/
│       ├── PKGBUILD
│       └── files/
├── scripts/
│   └── cambonos.py          # Punto de entrada para validar, construir y publicar
├── dist/                    # Salida local; no se versiona
│   ├── build/<arch>/         # Artefactos de build sin publicar
│   ├── testing/<arch>/       # Repositorio local de pruebas
│   └── stable/<arch>/        # Repositorio local estable
└── README.md
```

`files/` contiene los archivos fuente mantenidos por CambonOS. No se utiliza `src/` para almacenarlos: makepkg reserva `src/` como directorio temporal de compilación y puede eliminarlo durante `--cleanbuild`.

## Gestor de paquetes

Toda la gestión se realiza mediante `scripts/cambonos.py`. El gestor está implementado en Python y utiliza las herramientas nativas de Arch (`makepkg`, `pacman` y `repo-add`) para las operaciones propias del empaquetado. La validación estática no ejecuta ni hace `source` de los PKGBUILD.

Ejecuta los comandos desde la raíz del repositorio y como usuario normal para las operaciones de construcción y publicación. No ejecutes `makepkg` como root.

### Ayuda

```bash
python3 scripts/cambonos.py --help
python3 scripts/cambonos.py validate --help
python3 scripts/cambonos.py build --help
python3 scripts/cambonos.py publish --help
```

### Validar

Valida todos los paquetes:

```bash
python3 scripts/cambonos.py validate
```

Valida un paquete concreto:

```bash
python3 scripts/cambonos.py validate --package cambonos-release
```

Se pueden indicar varios paquetes repitiendo `--package`:

```bash
python3 scripts/cambonos.py validate \
  --package cambonos-release \
  --package cambonos-fastfetch
```

La validación comprueba, entre otros aspectos:

- Sintaxis Bash de los PKGBUILD y de los scripts asociados.
- Coherencia entre `pkgname` y el nombre del directorio.
- Presencia de `pkgver` y `pkgrel`.
- Uso de arrays estáticos `depends` y ausencia de `source=()`/`sha256sums=()` en este modelo de payload local.
- Existencia y ubicación de los archivos referenciados bajo `files/`.
- Rutas de destino utilizadas con `$pkgdir`.
- Existencia y sintaxis del script `.install`, si está declarado.
- Estructura básica de los hooks `.hook`.
- Dependencias internas sin paquete correspondiente y ciclos entre dependencias del monorepo.

Es una validación estática y deliberadamente conservadora. No sustituye a `makepkg`, a la instalación del paquete ni a las pruebas en una máquina virtual.

### Validar y construir

Construye todos los paquetes después de validarlos:

```bash
python3 scripts/cambonos.py build
```

Construye solo uno o varios paquetes:

```bash
python3 scripts/cambonos.py build --package cambonos-release

python3 scripts/cambonos.py build \
  --package cambonos-release \
  --package cambonos-fastfetch
```

Los artefactos resultantes se guardan en `dist/build/<arch>/`. Esta operación no modifica los repositorios `testing` ni `stable`, ni genera una base de datos pacman.

El gestor utiliza un directorio temporal independiente para `BUILDDIR` y `PKGDEST`; no limpia ni elimina manualmente `src/`, `pkg/` o paquetes preexistentes dentro de los directorios de los PKGBUILD. `makepkg --cleanbuild --clean` administra su área temporal de compilación.

Se utiliza `makepkg --nodeps`: las dependencias de ejecución se conservan en la metadata del paquete, pero no se exige que estén instaladas en el host. Si en el futuro se declaran `makedepends`, las herramientas necesarias deberán estar disponibles en el entorno de construcción.

### Validar, construir y publicar

La publicación exige indicar explícitamente el canal. No existe un canal predeterminado:

```bash
python3 scripts/cambonos.py publish --channel testing
python3 scripts/cambonos.py publish --channel stable
```

Publicación selectiva:

```bash
python3 scripts/cambonos.py publish \
  --channel testing \
  --package cambonos-release
```

Se pueden indicar varios `--package`. Si no se indica ninguno, se procesan todos los paquetes del monorepo.

El destino local es `dist/<channel>/<arch>/`, por ejemplo `dist/testing/x86_64/`. La arquitectura se detecta mediante `pacman-conf Architecture` y, si no está disponible o devuelve `auto`, mediante `uname -m`. Se puede especificar manualmente con `--arch`:

```bash
python3 scripts/cambonos.py publish --channel testing --arch x86_64
```

Comportamiento de publicación:

1. Valida los paquetes seleccionados.
2. Construye los paquetes en un área temporal y comprueba su nombre con `pacman -Qqp`.
3. Prepara una copia de trabajo del canal y conserva los paquetes que no se están actualizando.
4. Comprueba que las dependencias internas de los paquetes seleccionados estarán disponibles en el canal resultante.
5. Sustituye los artefactos de los paquetes seleccionados y retira los nombres declarados como obsoletos en `OBSOLETE_PACKAGES` dentro del gestor.
6. Regenera la base de datos a partir del conjunto completo de paquetes que queda en el canal.
7. Sustituye el directorio de arquitectura preparado. Si falla el cambio de directorio, intenta restaurar la copia anterior.

La base de datos se genera de nuevo con `repo-add`; no se modifica incrementalmente. Los alias `cambonos.db` y `cambonos.files` se materializan como archivos regulares además de sus archivos `.tar.gz`, para facilitar su publicación en hosting estático como GitHub Pages.

La publicación selectiva no elimina paquetes que ya no estén en el código fuente salvo que su nombre esté incluido en `OBSOLETE_PACKAGES`. Cuando se retire un paquete del proyecto, añade su nombre a esa lista y publica de nuevo el canal correspondiente.

### Simulación (`--dry-run`)

`--dry-run` está disponible en los tres subcomandos:

```bash
python3 scripts/cambonos.py validate --dry-run
python3 scripts/cambonos.py build --package cambonos-release --dry-run
python3 scripts/cambonos.py publish --channel testing --dry-run
```

La simulación ejecuta la validación estática y muestra los paquetes y operaciones previstas, pero no ejecuta `makepkg` ni `repo-add`, no crea directorios de salida, no adquiere el bloqueo de publicación y no modifica `dist/`. En una simulación de publicación no inspecciona mediante `pacman` los archivos que ya existan en el canal; la comprobación definitiva de dependencias y metadata se realiza durante la publicación real.

### Bloqueo y concurrencia

Las operaciones que escriben en `dist/` utilizan un bloqueo exclusivo mediante `flock` (módulo `fcntl` de Python). Esto evita que dos procesos del gestor actualicen simultáneamente las salidas locales. El bloqueo se guarda en `dist/.cambonos-repository.lock`.

Este bloqueo es local al sistema de archivos donde se ejecuta el gestor. No coordina por sí solo ejecuciones de GitHub Actions en máquinas diferentes; los workflows deberán utilizar también un grupo de concurrencia de GitHub Actions.

## Paquetes

### cambonos-release

Gestiona la identidad de distribución de CambonOS:

- Instala la identidad vendor en `/usr/lib/cambonos/os-release`.
- Mantiene `/etc/os-release` apuntando mediante un enlace relativo a `../usr/lib/cambonos/os-release`.
- Instala un hook de pacman para volver a comprobar la identidad después de transacciones que afecten a `filesystem`, `systemd`, `lsb-release` o a los archivos de release relevantes.
- Si el paquete opcional `lsb-release` está instalado, adapta `/etc/lsb-release` para que `lsb_release` identifique CambonOS. El contenido original se guarda en `/var/lib/cambonos-release/` y se restaura al desinstalar `cambonos-release`, siempre que el archivo siga conteniendo el contenido administrado por CambonOS.

`cambonos-release` ofrece `lsb-release` y `cambonos-fastfetch` como dependencias opcionales. No instala ninguno de ellos automáticamente.

`cambonos-release` no modifica estos archivos de Arch:

- `/usr/lib/os-release`: permanece como identidad vendor original de Arch.
- `/etc/arch-release`: permanece como marcador de Arch Linux, propiedad del paquete `filesystem`.

Esto es intencionado: CambonOS se identifica como distribución derivada de Arch (`ID_LIKE=arch`), pero no oculta la base tecnológica sobre la que se construye. Tampoco se modifican `/etc/issue` ni `/etc/issue.net`, que son banners de inicio de sesión y no identificadores estándar de distribución. No se gestionan `/etc/initrd-release` ni los archivos `extension-release.*`: identifican entornos initrd o imágenes de extensiones, no la identidad del sistema anfitrión.

**Sobre `/etc/lsb-release`:** el paquete oficial `lsb-release` de Arch es propietario de esta ruta. Por eso `cambonos-release` no instala un segundo archivo ni un symlink competidor en esa ubicación. El hook actualiza el archivo después de que el paquete de Arch lo instale o actualice. Se omite `LSB_VERSION`, ya que ese campo declara conformidad con módulos LSB y CambonOS no está afirmando dicha conformidad.

### cambonos-fastfetch

Proporciona exclusivamente la integración visual con Fastfetch:

- Perfil JSONC de CambonOS.
- Logo ASCII de CambonOS.
- Lanzador `/usr/bin/cambonos-fastfetch`.
- Inicio automático en shells interactivos mediante mecanismos globales no invasivos:
  - Bash: sesiones interactivas de login mediante `/etc/profile.d/`. Las sesiones interactivas no-login no se modifican ni ejecutan Fastfetch.
  - Zsh: sesiones interactivas de login mediante `/etc/profile.d/`, que Arch carga desde `/etc/zsh/zprofile`. Las sesiones interactivas no-login no se modifican ni ejecutan Fastfetch.
  - Otros shells compatibles con `/etc/profile`: sesiones interactivas de login, siempre que el shell cargue el perfil global.
  - Fish: todas las sesiones interactivas, login y no-login, mediante `/usr/share/fish/vendor_conf.d/`. Fish es opcional y no se instala como dependencia.
- No modifica `/etc/bash.bashrc`, `/etc/zsh/zshrc`, archivos de configuración de Fish ni archivos personales (`~/.bashrc`, `~/.zshrc`, `~/.config/fish/config.fish`).
- Para desactivar el inicio automático en shells nuevos, la variable `CAMBONOS_NO_FASTFETCH` debe estar definida en el entorno antes de iniciar el shell. Por ejemplo: `CAMBONOS_NO_FASTFETCH=1 zsh -l`.

Tiene `fastfetch` y `cambonos-release` como dependencias obligatorias. `fish` es una dependencia opcional únicamente para disponer de su integración automática. No se instala ni se configura Fastfetch desde `cambonos-release`. Al desinstalar `cambonos-fastfetch`, pacman elimina sus dos fragmentos de integración junto con el resto de sus archivos.

### cambonos-base (futuro)

El nombre `cambonos-base` queda libre para un futuro metapaquete que agrupe los componentes básicos que CambonOS decida incluir por defecto. No forma parte de esta versión. Se mantiene en la lista de paquetes obsoletos para retirarlo de los repositorios durante la publicación.

## Migración desde cambonos-base 0.1.0-3

El nuevo paquete `cambonos-release` declara `replaces=('cambonos-base')` y `conflicts=('cambonos-base')` para facilitar el cambio de nombre.

Para migrar y conservar también la integración de Fastfetch:

```bash
sudo pacman -Syu cambonos-release cambonos-fastfetch
```

Si no se desea Fastfetch:

```bash
sudo pacman -Syu cambonos-release
```

Pacman puede solicitar confirmar la sustitución del antiguo `cambonos-base`. La base de datos del repositorio deja de publicar el paquete antiguo y pasa a publicar los dos paquetes nuevos.

## Instalación de archivos desde `files/`

Los paquetes instalan sus archivos locales directamente desde el árbol Git mediante `$startdir/files/...` dentro de `package()`:

```bash
install -Dm644 "$startdir/files/cambonos/os-release" \
  "$pkgdir/usr/lib/cambonos/os-release"
```

Para estos archivos locales no se declaran arrays `source=()` ni `sha256sums=()`. `makepkg` no necesita copiarlos al directorio de compilación: `install` los lee desde su ubicación original y los incorpora directamente a `$pkgdir`.

El validador comprueba que las rutas literales de origen estén dentro de `files/`, que existan y que los destinos sean rutas de instalación admisibles. El validador es estático: no ejecuta ni hace `source` del PKGBUILD.

## Requisitos

En Arch Linux:

```bash
sudo pacman -S --needed base-devel pacman python
```

- `python`: gestor y validación estática.
- `bash`: análisis sintáctico de PKGBUILD y scripts.
- `base-devel`: incluye `makepkg` y las herramientas habituales de construcción.
- `pacman`: inspección de metadata de los paquetes.
- `repo-add`: generación de la base de datos del repositorio (incluido con pacman).
- El bloqueo exclusivo utiliza `fcntl`, incluido en la biblioteca estándar de Python.

El gestor requiere Python 3.10 o posterior. La validación estática puede ejecutarse fuera de Arch siempre que haya Python 3.10+ y Bash. La construcción y publicación deben probarse en Arch Linux, con las herramientas anteriores y las dependencias de compilación que requiera cada paquete.

## Flujo de ramas previsto

- `dev`: desarrollo y publicación automatizada en el canal `testing`.
- `main`: recibe cambios mediante Pull Request desde `dev` y publica en `stable`.
- `gh-pages`: rama técnica prevista para alojar el árbol de repositorios servido mediante GitHub Pages.

La herramienta gestiona los repositorios locales en `dist/`. La sincronización de esos directorios con GitHub Pages y la concurrencia entre workflows se implementarán en GitHub Actions; no forman parte todavía de este gestor local.

## Alcance de las pruebas

Las comprobaciones estáticas, la sintaxis Python y la planificación `--dry-run` pueden verificarse sin construir paquetes. La construcción real, la lectura de metadata mediante pacman y la generación de bases de datos deben probarse en Arch Linux. Una compilación satisfactoria tampoco sustituye a una instalación y prueba funcional de cada paquete en una máquina virtual.


### Nombres de las bases de datos por canal

El nombre de la base de datos debe coincidir con el nombre de la sección del
repositorio configurada en `pacman.conf`:

- Canal `testing`, sección `[cambonos-testing]`: `cambonos-testing.db` y
  `cambonos-testing.files` (además de sus archivos `.tar.gz`).
- Canal `stable`, sección `[cambonos]`: `cambonos.db` y `cambonos.files`
  (además de sus archivos `.tar.gz`).

El gestor selecciona automáticamente el nombre correcto según `--channel`.
Los nombres de los paquetes no cambian entre canales.
