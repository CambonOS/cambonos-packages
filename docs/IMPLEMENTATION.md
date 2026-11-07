# CambonOS Packages — arquitectura de implementación

## Resumen

El repositorio utiliza un pipeline modular de validación, construcción, firma y publicación. Cada push a `dev` o `main` fija los commits de ambas ramas y procesa los dos canales a partir de esos snapshots Git inmutables. Para los repos fuente externos, `stable` usa `main` y `testing` usa `dev` cuando está publicada, con fallback a `main`; esos commits se verifican y staged temporalmente como `cambonos-installer` y `cambonos-mkiso`, sin copiar sus fuentes al historial de `cambonos-packages`.

## Cambios principales

### 1. Gestor Python modular

` scripts/cambonos.py` pasa a ser el punto de entrada. La lógica se separa en `scripts/cambonos_lib/`:

- `config.py`: ramas, canales, arquitectura e imagen.
- `common.py`: comandos, errores y SHA256.
- `models.py`: modelos de paquetes, snapshots y artefactos.
- `validation.py`: validación estática de PKGBUILD y material GPG.
- `manifest.py`: manifiestos y política de versionado.
- `build.py`: construcción aislada con Docker.
- `signing.py`: importación, firma y verificación GPG.
- `repository.py`: generación de bases de datos pacman.
- `site.py`: comprobación básica de la estructura del sitio.

La validación estática no hace `source` ni ejecuta PKGBUILD. El PKGBUILD solo se ejecuta como usuario no privilegiado dentro de un contenedor Arch independiente.

### 2. Reconstrucción completa

- `dev` genera `testing`.
- `main` genera `stable`.
- Cada ejecución construye todos los paquetes de las dos ramas.
- Cada canal se genera en un directorio vacío.
- No se copian paquetes de la publicación anterior.
- Los paquetes eliminados de una rama desaparecen de su canal en la siguiente publicación.

Los SHA de ambas ramas se resuelven al principio y se mantienen durante toda la ejecución.

### 3. Construcción Arch en Docker

La imagen oficial `archlinux:base-devel` está fijada por digest para `linux/amd64`.

Cada paquete se construye en su propio contenedor:
- Se actualiza el entorno contra los repositorios rolling actuales.
- Se instalan `makedepends`.
- Se instalan `checkdepends` cuando existe `check()`.
- Se ejecuta `makepkg --nodeps`; no se instalan automáticamente dependencias de ejecución.
- Se valida nombre, versión y arquitectura del archivo generado.
- Se registra `pacman -Q` para trazabilidad.

Las dependencias internas de construcción se ordenan topológicamente. Las dependencias internas de ejecución no obligan a construir o instalar primero el paquete dependiente.

Los dos repositorios externos se clonan en los SHA resueltos en `validate`. El helper `scripts/stage_external_packages.py` verifica origen, commit limpio y nombre de paquete antes de copiar temporalmente el checkout al árbol que consume el validador. Añade `.cambonos-source.json` con repositorio, SHA y timestamp; ese archivo forma parte del hash de fuente. Las rutas estáticas del `PKGBUILD` pueden referenciar archivos dentro del checkout únicamente cuando existe metadata válida, y el validador impide que una ruta o symlink escape del árbol del paquete.

### 4. Manifiestos y versionado

El sitio publica `metadata/manifest.json`, con información de ambos canales:
- Rama y commit exacto.
- Versión del paquete.
- Hash de los archivos fuente.
- Nombre y SHA256 del paquete generado.
- Imagen y entorno de construcción.

El pipeline recupera el manifiesto anterior firmado desde GitHub Pages y verifica su firma antes de utilizarlo. Cada canal se valida únicamente contra sus propios registros anteriores: no se comparan los conjuntos de paquetes, las versiones ni los hashes de `stable` y `testing`. Esta independencia no se aplica al material público de confianza, cuyos tres archivos sí deben coincidir byte a byte entre `dev` y `main`. Para cada paquete dentro de su canal:
- Cambio de contenido sin aumento de versión: error.
- Aumento de versión: permitido.
- Retroceso de versión según `vercmp`: error.
- Paquete nuevo o eliminado: permitido.

`stable` y `testing` se comparan de manera independiente.

### 5. Firma y seguridad

- `SOURCE_DATE_EPOCH` se deriva del último commit que modificó cada directorio de paquete. Para los paquetes externos se toma del commit upstream fijado.
- La política de versión compara `source_hash` y la versión del paquete con el manifiesto anterior de su propio canal. Si cambia el contenido fuente sin aumentar `pkgrel`/`pkgver`, la publicación se bloquea.
- Una reconstrucción con la misma fuente y versión puede producir un binario distinto por los cambios del entorno rolling de Arch y está permitida. `package_hash` se utiliza para verificar la integridad del artefacto y registrar exactamente qué binario se ha firmado y publicado; nunca determina por sí solo la obligación de incrementar la versión.
- La fase de firma verifica los manifiestos de construcción, los artefactos y la política de fuente/versión antes de importar la subclave privada. La política de versionado tiene una única implementación compartida con la validación previa a la construcción.
- El job `build` no recibe secretos de firma.
- El job `signing` es el único que importa la subclave privada.
- El job `signing` no ejecuta PKGBUILD ni scripts de instalación.
- Se verifica por separado que el fingerprint secreto coincide con la subclave pública incluida en el paquete `cambonos-keyring` de cada canal. Además, el workflow compara byte a byte `cambonos.gpg`, `cambonos-trusted` y `cambonos-revoked` entre `dev` y `main`; ambos canales deben distribuir exactamente el mismo material de confianza, según la política del proyecto.
- El manifiesto global también se firma; la siguiente ejecución verifica su firma antes de utilizarlo como referencia de versionado.
- Cada paquete se firma individualmente.
- `repo-add --include-sigs` genera las bases de datos incluyendo las firmas de paquetes.
- Las bases de datos y sus alias estáticos se firman y verifican.
- `publish` no recibe la clave privada.

La firma acredita la procedencia criptográfica del paquete, no la ausencia de código malicioso. La protección de ramas y la revisión del código siguen siendo necesarias.

### 6. GitHub Pages

Se elimina `pages-bootstrap.yml` y se incorpora `package-pipeline.yml`.

El workflow se activa con `push` a `dev` y `main`, o manualmente desde GitHub
Actions seleccionando una de esas ramas. Para que GitHub ofrezca el disparo
manual, el archivo debe estar presente en la rama predeterminada. La ejecución
manual permite reconstruir y publicar ambos canales cuando cambian los
repositorios externos; los SHA de ambas ramas fuente y de los repositorios
externos se resuelven al comenzar cada ejecución. No hay workflow de PR.

Los cuatro jobs son:
1. `validate`
2. `build` (matriz `testing` y `stable`)
3. `signing`
4. `publish`

El despliegue utiliza `actions/upload-pages-artifact` y `actions/deploy-pages`. Se publica un único artefacto de sitio completo. Si falla cualquier fase, el job de despliegue no se ejecuta.

## Paquetes de integración del sistema

### `cambonos-branding`

El paquete distribuye cuatro recursos gráficos en
`/usr/share/cambonos/branding/`: `cambonos-icon.svg`,
`cambonos-text.svg`, `cambonos-icon.png` y `cambonos-text.png`. Los SVG son
los recursos vectoriales y los PNG sus exportaciones rasterizadas
(1024 × 1024 para el icono y 3792 × 1024 para el logotipo textual). También
instala la fuente `CambonOS-Symbols.ttf` en `/usr/share/fonts/TTF/`, la regla
Fontconfig de `files/ttf/` y la licencia.

Se eliminan las variantes `cambonos-icon-black.svg`,
`cambonos-icon-white.svg`, `cambonos-text-black.svg`,
`cambonos-text-white.svg` y `cambonos-logo.txt`. No se crean enlaces
simbólicos en `/usr/share/icons/` ni `/usr/share/pixmaps/`, ni se mantiene
compatibilidad con las rutas anteriores: los consumidores propios de
CambonOS deben utilizar directamente los cuatro recursos gráficos canónicos.
Se conserva exclusivamente el enlace Fontconfig `conf.default` → `conf.avail`
necesario para activar el fallback de `CambonOS Symbols` para `U+10FFFD`.
El cambio de contenido incrementa `pkgrel` de 1 a 3, manteniendo
`pkgver=0.1.1`.


### `cambonos-release`: recuperación al desinstalar

El `post_remove` restaura `/etc/os-release` únicamente si todavía apunta al
enlace administrado por CambonOS. Para `/etc/lsb-release`, exige que el archivo
siga siendo regular y coincida con `lsb-release.managed`; no sobrescribe
cambios administrativos, enlaces simbólicos ni directorios.

La restauración valida que exista exactamente un marcador del estado original
(`lsb-release.original` o `lsb-release.was-absent`) y que el snapshot gestionado
sea válido. Un `/etc/lsb-release.pacnew` regular tiene prioridad tanto si había
backup como si el archivo original no existía. Sin `.pacnew`, el backup se copia
con `cp -a` a un directorio temporal en `/etc` y se instala mediante `mv`
atómico; el marcador de ausencia permite retirar únicamente el archivo
gestionado.

`/var/lib/cambonos-release` se elimina solo después de completar la
restauración. Si hay cambios manuales, metadatos incompletos/contradictorios,
rutas inesperadas o errores de `mktemp`, `cp` o `mv`, se conservan los datos de
recuperación para intervención manual. Este cambio incrementa `pkgrel` de 7 a
8, manteniendo `pkgver=0.1.0`. La regresión se cubre con
`tests/test_release_install.py`.

### `cambonos-keyring`

Añade el certificado público y la información de confianza de pacman en:

```text
/usr/share/pacman/keyrings/cambonos.gpg
/usr/share/pacman/keyrings/cambonos-trusted
/usr/share/pacman/keyrings/cambonos-revoked
```

El paquete instala el material público en `/usr/share/pacman/keyrings/` y ejecuta `pacman-key --populate cambonos` cuando el keyring local ya está inicializado. El repositorio contiene el certificado público y los datos de confianza; nunca debe contener claves privadas.

### `cambonos-pacman`

Distribuye `/etc/pacman.d/cambonos.conf` con el mirror canónico `https://mirror.cambonos.org`, habilita stable y deja testing comentado. Declara `cambonos-keyring` como dependencia y configura `SigLevel = Required TrustedOnly` para ambos canales. El paquete es opcional: cada canal puede incluirlo o no, sin exigir que esté presente en el otro canal. El único paquete obligatorio en ambos canales es `cambonos-keyring`, necesario para la verificación de firmas.

También distribuye `/etc/pacman.d/cambonos-options.conf`, que contiene únicamente las diferencias acordadas respecto a la configuración de referencia de Arch: `Color`, `CheckSpace`, `VerbosePkgLists`, `ParallelDownloads = 3` e `ILoveCandy`. No redefine `HoldPkg`, `Architecture`, `SigLevel` ni modifica `DownloadUser` o el sandbox.

El helper `/usr/lib/cambonos-pacman/manage-pacman-config` administra dos bloques independientes: incluye las opciones desde dentro de `[options]` y añade el Include de repositorios al final para conservar la prioridad de los repositorios oficiales. Reconoce y migra los marcadores antiguos de `cambonos-repo`. Realiza escrituras atómicas, evita duplicados, conserva los Include manuales y falla de forma conservadora ante marcadores incompletos o una sección `[options]` ambigua.

El script `.install` ejecuta `--ensure` en `post_install` y `post_upgrade`, y `--remove` en `pre_remove`. El hook `cambonos-pacman-conf.hook` usa un disparador `Type = Path` sobre `etc/pacman.conf`, para operaciones `Install` y `Upgrade`, y vuelve a garantizar la integración tras esas transacciones. El hook no detecta modificaciones manuales arbitrarias ni cambios realizados por scriptlets que no formen parte de la lista de archivos de la transacción.

El paquete declara la transición desde `cambonos-repo` mediante `provides`, `conflicts` y `replaces`.

### `cambonos-zsh`, `cambonos-shell-prompt` y `cambonos-fastfetch`

La configuración de shells se divide por responsabilidad:

- `cambonos-zsh` depende de `zsh`, `zsh-completions`, `zsh-autosuggestions`, `zsh-syntax-highlighting` y `cambonos-shell-prompt`. Mantiene el único bloque administrado de `/etc/zsh/zshrc` y carga en orden lexicográfico los fragmentos `*.zsh` de `/usr/share/cambonos/zsh/conf.d/`. Proporciona un `/etc/skel/.zshrc` vacío para nuevos usuarios, sin modificar archivos personales existentes ni cambiar shells de cuentas; la selección de shell pertenece al instalador ISO.
- `cambonos-shell-prompt` depende de `starship`, `bash` y `util-linux`, pero no depende de Zsh ni de Fish. Proporciona la configuración CambonOS y las integraciones Bash, Zsh y Fish. Zsh utiliza un fragmento en el directorio `conf.d` de `cambonos-zsh`; sin ese paquete la integración Zsh requiere configuración manual. Bash utiliza un bloque propio en `/etc/bash.bashrc`; Fish utiliza `vendor_conf.d`.
- `cambonos-fastfetch` mantiene sus integraciones Bash, Fish y POSIX de login. Su fragmento Zsh se instala en `conf.d`; no modifica `/etc/zsh/zshrc`. Al actualizar desde versiones anteriores retira su antiguo bloque Zsh de forma conservadora, preservando el cargador y el contenido ajeno.

Los gestores que modifican `/etc/bash.bashrc` utilizan marcadores distintos y el mismo bloqueo `/run/lock/cambonos-shell-integration.lock`, escrituras atómicas y rechazo de archivos no regulares, enlaces simbólicos y marcadores ambiguos. Cada paquete elimina exclusivamente su propio bloque.

### `cambonos-grub`

El paquete depende de `grub>=2:2.16`, versión mínima que proporciona el soporte de `/etc/default/grub.d/*.cfg`, y de `os-prober` para multiboot. Instala sus opciones en `/etc/default/grub.d/60-cambonos.cfg`, sin reemplazar `/etc/default/grub`, propiedad del paquete `grub`. Pacman conserva cambios locales mediante `backup` y `.pacnew`.

El tema de `/usr/share/grub/themes/CambonOS/` deriva de Vimix de Vinceliuice. Mantiene el fondo y recursos de Vimix con colores de CambonOS, el icono de distribución, aviso de atribución y licencia GPL-3.0. La fuente Unifont incluida se redistribuye bajo GPL-2.0-or-later con la excepción GNU de incrustación; ambas licencias y avisos se incluyen en el paquete. La configuración conserva IPv6, usa `GRUB_GFXMODE=auto`, habilita `os-prober` y no define `GRUB_GFXPAYLOAD_LINUX`.

Los scriptlets regeneran `/boot/grub/grub.cfg` al instalar, actualizar y retirar el paquete. Un hook `PostTransaction` detecta Install/Upgrade/Remove sobre `usr/lib/modules/*/vmlinuz` y regenera el menú después de cambios de kernel. El helper omite sistemas sin un `grub.cfg` existente y rechaza enlaces simbólicos y rutas no regulares. El paquete no ejecuta `grub-install` ni decide el destino UEFI/BIOS; las ediciones directas en `grub.cfg` se pierden al regenerarlo.

### `cambonos-plymouth`

Proporciona un tema `two-step` con el fondo gráfico CambonOS, el icono canónico para diálogos, y barra turquesa. Desactiva las animaciones circulares y mantiene la barra de progreso (`UseAnimation=false`, `UseProgressBar=true`), sin añadir retardo (`TransitionDuration=0.0`, `ShowDelay=0`).

El paquete depende de `plymouth` y `mkinitcpio>=36`. Un drop-in con política `backup` en `/etc/mkinitcpio.conf.d/90-cambonos-plymouth.conf` agrega el hook Plymouth sin reemplazar la configuración principal: se inserta antes de `encrypt`/`sd-encrypt`, o después de `udev`/`systemd` cuando no hay cifrado. Los scriptlets seleccionan el tema al instalar, preservan una elección de tema del administrador durante actualizaciones y restauran el predeterminado al desinstalar si CambonOS sigue seleccionado. Instalar, actualizar o retirar reconstruye los presets presentes; sin presets se informa que hace falta reconstruir tras instalar un kernel.

GRUB añade `splash quiet loglevel=3` para activar el splash y suprimir mensajes de consola. Otros cargadores requieren configurar esos parámetros por separado. El paquete no modifica `/etc/mkinitcpio.conf`, los presets de kernel ni configuraciones de otros cargadores. Presets que fuerzan `ALL_config` deben actualizarse para cargar archivos drop-in.

## Configuración requerida en GitHub

Crear el entorno `package-signing`, limitarlo a las ramas `dev` y `main`, y añadir:

**Environment secrets**
- `CAMBONOS_SIGNING_KEY`
- `CAMBONOS_SIGNING_PASSPHRASE`

**Environment variable**
- `CAMBONOS_SIGNING_FINGERPRINT` (fingerprint de la subclave de firma).

**Repository variables**
- `CAMBONOS_BOOTSTRAP=true` solo durante la primera publicación; cambiar a `false` después.
- `CAMBONOS_PAGES_URL` opcional para una URL personalizada.

GitHub Pages debe utilizar el origen **GitHub Actions**.

## Requisitos operativos y límites

Para ejecutar el pipeline de publicación deben estar configurados el entorno protegido `package-signing`, sus secretos y fingerprint, las variables de Actions, y GitHub Pages con origen **GitHub Actions**. La primera publicación requiere habilitar `CAMBONOS_BOOTSTRAP=true` de forma temporal; tras verificar el manifiesto firmado publicado, debe cambiarse a `false`.

La construcción requiere Docker y acceso a los repositorios rolling de Arch desde los contenedores. La firma requiere GPG y los secretos del entorno protegido. La suite unitaria y la validación estática no sustituyen una construcción real, la instalación en una máquina Arch ni una prueba de cliente contra el mirror publicado. Registra por separado qué fases se han ejecutado realmente en cada release.
