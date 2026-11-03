# CambonOS Packages

Monorepo de paquetes para CambonOS, una distribución basada en Arch Linux rolling release.

## Estructura

```text
cambonos-packages/
├── packages/
│   ├── cambonos-release/
│   │   ├── PKGBUILD
│   │   ├── cambonos-release.install
│   │   └── files/
│   │       ├── cambonos/
│   │       │   ├── os-release
│   │       │   ├── lsb-release
│   │       │   └── lib/restore-release-files
│   │       └── libalpm/hooks/zzzz-cambonos-release.hook
│   └── cambonos-fastfetch/
│       ├── PKGBUILD
│       └── files/cambonos/
│           ├── bin/cambonos-fastfetch
│           └── fastfetch/
│               ├── config.jsonc
│               └── logo.txt
├── scripts/
│   ├── build.sh
│   ├── repo-add.sh
│   ├── validate.sh
│   └── lib/pkgbuild_tools.py
└── dist/                 # generado; ignorado por Git
```

`files/` contiene los archivos fuente mantenidos por CambonOS. No se utiliza `src/` para almacenarlos: makepkg reserva `src/` como directorio temporal de compilación y puede eliminarlo durante `--cleanbuild`.

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

El nombre `cambonos-base` queda libre para un futuro metapaquete que agrupe los componentes básicos que CambonOS decida incluir por defecto. No forma parte de esta versión.

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

## Instalación desde `files/`

Los paquetes instalan sus archivos locales directamente desde el árbol Git mediante `$startdir/files/...` dentro de `package()`:

```bash
install -Dm644 "$startdir/files/cambonos/os-release" \
  "$pkgdir/usr/lib/cambonos/os-release"
```

Para estos archivos locales no se declaran arrays `source=()` ni `sha256sums=()`. `makepkg` no necesita copiarlos al directorio de compilación: `install` los lee desde su ubicación original y los incorpora directamente a `$pkgdir`.

El validador comprueba que las rutas literales de origen estén dentro de `files/`, que existan y que los destinos sean rutas de instalación admisibles. El validador es estático: no ejecuta ni hace `source` del PKGBUILD.

## Flujo de trabajo

Desde la raíz del repositorio y como usuario normal (no como root), el flujo normal de publicación requiere un único comando:

```bash
./scripts/repo-add.sh
```

Este comando ejecuta, en orden:

1. `validate.sh`: comprueba sintaxis Bash, metadatos, payloads, hooks y dependencias internas entre paquetes.
2. `build.sh`: construye todos los PKGBUILD con `makepkg --nodeps`, por lo que no exige que las dependencias de ejecución estén instaladas en el host. Las herramientas realmente necesarias para compilar (futuras `makedepends`) sí deben existir en el entorno.
3. `repo-add`: genera una base de datos nueva a partir de todos los paquetes publicados en `dist/<arquitectura>/`.

La construcción es transaccional: primero genera todos los paquetes en un área temporal y valida su metadata con `pacman -Qqp` (consulta silenciosa del nombre del paquete desde el archivo).. Solo cuando todos se han construido correctamente reemplaza los artefactos anteriores. Si falla una compilación, la publicación anterior permanece intacta.

La publicación completa también mantiene una copia de recuperación de `dist/<arquitectura>/`. Si falla la generación o sustitución de la base de datos, restaura el contenido anterior, incluidos paquetes, bases de datos y enlaces. La base de datos se reconstruye desde cero, por lo que no depende de `repo-remove` y deja fuera los paquetes retirados. Los paquetes obsoletos conocidos se declaran en `scripts/lib/common.sh`.

`build.sh` también puede ejecutarse de forma independiente cuando solo se quieran generar paquetes; en ese caso, la base de datos no se actualiza. `validate.sh` puede ejecutarse por separado para una comprobación rápida. Los scripts comparten un bloqueo `flock` para impedir que dos procesos de construcción/publicación se solapen.

Los directorios temporales de compilación (`src/`, `pkg/` y los artefactos sueltos junto a los PKGBUILD) se limpian al finalizar, tanto si la operación termina correctamente como si falla. Los originales de `files/` nunca se eliminan.

## Requisitos

En Arch Linux:

```bash
sudo pacman -S --needed base-devel pacman python util-linux
```

`makepkg` y `repo-add` forman parte de las herramientas de Arch/pacman; `flock` lo proporciona `util-linux`.

## Alcance de las pruebas

La validación estática y las pruebas de sintaxis pueden realizarse fuera de Arch. La construcción real debe verificarse con `makepkg` en un sistema Arch Linux. La validación estática no sustituye a una compilación real ni a una instalación de prueba en una máquina virtual.
