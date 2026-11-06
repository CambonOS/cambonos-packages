# CambonOS — Checklist de validación de paquetes

Checklist operativa para verificar los paquetes del repositorio en un entorno Arch Linux de pruebas. No ejecutar pruebas destructivas en el equipo principal. Utilizar una máquina virtual o snapshot restaurable, con acceso a consola y copia de seguridad.

## 1. Preparación común

- [ ] Registrar commit exacto, rama, fecha, arquitectura y versión de Arch del entorno.
- [ ] Crear una VM Arch Linux limpia y snapshot inicial.
- [ ] Confirmar que la VM usa `linux/amd64` si se pretende reproducir el entorno CI actual.
- [ ] Instalar herramientas: `base-devel`, `git`, `python`, `bash`, `gawk`, `util-linux`, `gnupg`, `pacman-contrib`, `libxml2` y `file`.
- [ ] Ejecutar `python3 -m unittest discover -s tests -v`.
- [ ] Ejecutar `python3 -m compileall -q scripts`.
- [ ] Ejecutar `bash -n` sobre helpers, scriptlets y scripts shell.
- [ ] Validar sintaxis de hooks ALPM y revisar rutas `Exec`, `Depends`, `Target`, `Operation` y `When`.
- [ ] Construir cada paquete en entorno Arch limpio mediante `makepkg`.
- [ ] Ejecutar `namcap` sobre PKGBUILD y paquetes, si está disponible; revisar manualmente cada advertencia.
- [ ] Inspeccionar contenido con `bsdtar -tf paquete.pkg.tar.zst`.
- [ ] Verificar permisos, propietario, rutas y licencias con `pacman -Qlp` o extracción en directorio temporal.
- [ ] Instalar paquetes en la VM mediante `pacman -U`.
- [ ] Capturar logs de instalación, actualización, hooks y eliminación.
- [ ] Comprobar `pacman -Qkk nombre-paquete` después de instalar.
- [ ] Repetir las pruebas desde snapshots limpios para evitar contaminación entre escenarios.

## 2. cambonos-branding

### Construcción y contenido
- [ ] `makepkg` termina correctamente.
- [ ] El paquete contiene los cuatro recursos gráficos (`cambonos-icon.svg`,
  `cambonos-text.svg`, `cambonos-icon.png` y `cambonos-text.png`), los recursos
  de `files/ttf/` y la licencia.
- [ ] Los cuatro recursos gráficos se instalan en
  `/usr/share/cambonos/branding/`.
- [ ] Los SVG se validan con `xmllint --noout` y se renderizan correctamente.
- [ ] `cambonos-icon.png` tiene 1024 × 1024 píxeles y
  `cambonos-text.png` tiene 3792 × 1024 píxeles; ambos se visualizan
  correctamente.
- [ ] Confirmar que los cuatro recursos distribuidos son los artefactos
  aprobados por el equipo de diseño.
- [ ] `CambonOS-Symbols.ttf` se instala en `/usr/share/fonts/TTF/`.
- [ ] `65-cambonos-symbols.conf` se instala en `conf.avail` y se habilita
  mediante el enlace en `conf.default`.
- [ ] La licencia se instala en
  `/usr/share/licenses/cambonos-branding/LICENSE`.
- [ ] No se incluyen `cambonos-icon-black.svg`, `cambonos-icon-white.svg`,
  `cambonos-text-black.svg`, `cambonos-text-white.svg` ni `cambonos-logo.txt`.
- [ ] No se crean enlaces simbólicos en `/usr/share/icons/` ni
  `/usr/share/pixmaps/`.
- [ ] Validar la cabecera TrueType y comprobar `fc-match 'CambonOS Symbols'`.
- [ ] Fontconfig antepone `CambonOS Symbols` para solicitudes que incluyan
  `U+10FFFD`.

### Rutas y ciclo de vida
- [ ] Los consumidores CambonOS utilizan directamente los recursos
  canónicos SVG o PNG según sus necesidades.
- [ ] No se depende de rutas antiguas ni se crean aliases de compatibilidad.
- [ ] Instalar en una VM limpia y comprobar el contenido real con `pacman -Qlp`.
- [ ] Actualizar desde la versión publicada anterior (`0.1.1-1`) a la nueva
  versión (`0.1.1-3`) y confirmar que pacman elimina las variantes SVG y
  `cambonos-logo.txt` que ya no pertenecen al paquete.
- [ ] Confirmar que la actualización instala los dos PNG y conserva la fuente
  y la integración Fontconfig.
- [ ] Desinstalar y confirmar que solo se eliminan archivos propiedad del
  paquete.
- [ ] Confirmar que no se modifican `/etc`, `$HOME` ni configuraciones de
  escritorio.

## 3. cambonos-fastfetch

### Construcción y contenido
- [ ] `makepkg` termina correctamente.
- [ ] Verificar todas las rutas instaladas declaradas en el PKGBUILD.
- [ ] Confirmar dependencias obligatorias (`fastfetch`, `cambonos-release`, `bash`, `util-linux`).
- [ ] Confirmar `cambonos-zsh` y `fish` como integraciones opcionales.
- [ ] Ejecutar `cambonos-fastfetch` y comprobar código de salida y salida visual.
- [ ] Confirmar que carga `/usr/share/cambonos/fastfetch/config.jsonc` y `logo.txt`.
- [ ] Validar la configuración con la versión real de Fastfetch instalada.

### Inicio de shells
- [ ] Bash interactivo de login: Fastfetch aparece una vez.
- [ ] Bash interactivo no-login: Fastfetch aparece una vez.
- [ ] Bash no interactivo: no aparece Fastfetch.
- [x] Zsh interactivo con `cambonos-zsh`: Fastfetch aparece una vez mediante `conf.d`.
- [x] Zsh interactivo sin `cambonos-zsh`: no hay integración automática y el fragmento puede cargarse manualmente.
- [ ] Zsh no interactivo: no aparece Fastfetch.
- [ ] Fish interactivo: Fastfetch aparece una vez.
- [ ] Fish no interactivo: no aparece Fastfetch.
- [ ] Shell POSIX de login que carga `/etc/profile`: Fastfetch aparece una vez.
- [ ] Combinaciones donde `/etc/profile` y rc del shell se ejecutan en la misma sesión: solo una invocación.
- [ ] `CAMBONOS_NO_FASTFETCH=1` desactiva el inicio automático en cada shell aplicable.
- [ ] Valor vacío de `CAMBONOS_NO_FASTFETCH` no lo desactiva.
- [ ] `_CAMBONOS_FASTFETCH_RAN` evita ejecuciones duplicadas.

### Gestor y migración
- [ ] `install` añade el bloque Bash sin borrar contenido preexistente.
- [ ] `install` y `repair` son idempotentes.
- [ ] `remove` elimina solo el bloque Bash administrado.
- [ ] El helper utiliza `/run/lock/cambonos-shell-integration.lock`.
- [ ] Dos gestores distintos que modifican `/etc/bash.bashrc` se serializan mediante el mismo bloqueo.
- [ ] Marcadores incompletos, duplicados o desordenados provocan fallo conservador sin reescribir el archivo.
- [ ] Un enlace simbólico o directorio en `/etc/bash.bashrc` no se reemplaza.
- [ ] Se preservan permisos, propietario y atributos del archivo Bash cuando se reescribe.
- [ ] Al actualizar desde la versión anterior, se elimina únicamente el antiguo bloque Fastfetch de `/etc/zsh/zshrc`.
- [ ] La migración preserva el bloque de `cambonos-zsh` y todo el contenido ajeno.
- [ ] Marcadores antiguos incompletos/duplicados provocan fallo seguro y mensaje claro.
- [ ] El fragmento nuevo se instala en `/usr/share/cambonos/zsh/conf.d/60-fastfetch.zsh`.
- [ ] Si falta `cambonos-zsh`, la documentación indica cómo cargar manualmente el fragmento.

### Hooks y ciclo de vida
- [ ] `post_install` instala la integración Bash y no modifica `/etc/zsh/zshrc` salvo retirar un bloque antiguo detectado.
- [ ] `post_upgrade` repara Bash y migra el bloque Zsh anterior.
- [ ] Simular actualización de Bash y comprobar hook ALPM.
- [ ] El hook no se ejecuta por actualizaciones de Zsh.
- [ ] Desinstalar y confirmar que se elimina solo el bloque Bash de Fastfetch.
- [ ] Los archivos `profile.d`, Fish y Zsh se retiran mediante propiedad normal de pacman.
- [ ] `pacman -Qkk cambonos-fastfetch` no detecta daños inesperados.

## 4. cambonos-shell-prompt

### Construcción y configuración
- [ ] `makepkg` termina correctamente.
- [ ] Confirmar dependencias obligatorias (`starship`, `bash`, `util-linux`).
- [ ] Confirmar Fish como integración opcional y ausencia de dependencia de Zsh.
- [ ] Validar `starship.toml` como TOML y con el esquema/versión de Starship disponible.
- [ ] Comprobar la paleta CambonOS, formato de dos líneas, módulos Git/Python/usuario/host/estado/duración.
- [ ] No se fuerza la instalación de Nerd Fonts.
- [ ] `STARSHIP_CONFIG` explícito tiene prioridad.
- [ ] `$XDG_CONFIG_HOME/starship.toml` o `~/.config/starship.toml` tiene prioridad sobre la configuración CambonOS.
- [ ] La configuración CambonOS se utiliza como fallback cuando no existe configuración personal.

### Integración
- [ ] Bash interactivo carga Starship una vez.
- [ ] Bash no interactivo no carga Starship.
- [x] Zsh interactivo con `cambonos-zsh` carga Starship desde `conf.d`.
- [x] Zsh sin `cambonos-zsh` no tiene integración automática y puede integrarse manualmente desde `~/.zshrc`.
- [ ] Fish interactivo carga Starship desde `vendor_conf.d`.
- [ ] Fish no interactivo no carga Starship.
- [ ] La integración no depende de que Zsh o Fish estén instalados.
- [ ] La integración no modifica `~/.bashrc`, `~/.zshrc`, `~/.config/fish/config.fish` ni archivos personales Starship.

### Gestor y ciclo de vida
- [ ] `install` añade el bloque propio en `/etc/bash.bashrc`.
- [ ] `repair` es idempotente y restaura el bloque si falta.
- [ ] `remove` elimina exclusivamente el bloque Shell Prompt.
- [ ] El helper utiliza `/run/lock/cambonos-shell-integration.lock` compartido con Fastfetch.
- [ ] Marcadores dañados, archivos no regulares y enlaces simbólicos provocan fallo seguro.
- [ ] Se preservan permisos, propietario y atributos del archivo Bash.
- [ ] El hook ALPM repara la integración tras actualizar Bash.
- [ ] `pacman -Qkk cambonos-shell-prompt` no detecta daños inesperados.

## 5. cambonos-zsh

### Construcción y dependencias
- [ ] `makepkg` termina correctamente.
- [ ] Confirmar dependencias obligatorias (`zsh`, `zsh-completions`, `zsh-autosuggestions`, `zsh-syntax-highlighting`, `cambonos-shell-prompt`, `util-linux`).
- [ ] No se declara Fastfetch como dependencia.
- [ ] Se instala `/etc/skel/.zshrc` vacío y con permisos adecuados.
- [ ] No se modifican `/etc/default/useradd`, `/etc/passwd`, root ni shells de usuarios existentes.

### Configuración y arranque
- [x] El helper crea `/etc/zsh/zshrc` si no existe.
- [x] El bloque global carga los fragmentos `*.zsh` de `conf.d` en orden lexicográfico.
- [x] Los fragmentos base de completions, teclas, historial y plugins están presentes.
- [x] `compinit` se inicializa antes de cargar los plugins.
- [x] Autosuggestions se carga antes de syntax highlighting.
- [x] El modo de edición Emacs está activo.
- [x] Home y End mueven el cursor al principio/final de la línea actual.
- [x] Delete elimina el carácter bajo el cursor.
- [x] PageUp y PageDown buscan en el historial por el prefijo actual.
- [x] Historial persistente de 100.000 entradas.
- [x] `autocd`, `correct` y aliases acordados funcionan.
- [x] No se fuerza `EDITOR` ni se mantiene el alias `tar` que altera su uso normal.
- [x] `cambonos-shell-prompt` se carga desde su fragmento Zsh.
- [x] Fastfetch se carga si está instalado, sin ser dependencia de Zsh.
- [x] Una configuración personal `~/.zshrc` se ejecuta después de la configuración global y puede personalizarla.
- [x] Un usuario creado usando `/etc/skel` recibe un `.zshrc` vacío y la configuración global CambonOS sigue cargándose.

### Gestor y ciclo de vida
- [x] `install` crea el bloque sin borrar contenido preexistente.
- [x] `repair` es idempotente.
- [x] `remove` retira solo el bloque administrado.
- [x] Si el helper creó `/etc/zsh/zshrc` y no queda contenido externo, lo elimina al desinstalar.
- [x] Si el archivo existía previamente o contiene contenido externo, lo conserva.
- [x] Marcadores incompletos, duplicados o desordenados provocan fallo conservador.
- [x] Un enlace simbólico o directorio en `/etc/zsh/zshrc` no se reemplaza.
- [x] El helper utiliza `/run/lock/cambonos-shell-integration.lock`.
- [x] `pacman -Qkk cambonos-zsh` no detecta daños inesperados.



## 6. cambonos-keyring

### Material y construcción
- [ ] Verificar que existen `cambonos.gpg`, `cambonos-trusted` y `cambonos-revoked`.
- [ ] `gpg --show-keys --with-fingerprint cambonos.gpg` funciona.
- [ ] Verificar fingerprint primario mediante un canal autenticado independiente.
- [ ] Verificar fingerprint de la subclave operativa.
- [ ] Confirmar que `cambonos-trusted` expresa el ownertrust previsto.
- [ ] Confirmar que `cambonos-revoked` contiene los datos de revocación esperados.
- [ ] Buscar en Git, artefactos, logs y ZIP cualquier clave privada o exportación `--export-secret-keys` / `--export-secret-subkeys`; no debe existir.
- [ ] Construir con `makepkg` e inspeccionar los tres archivos instalados.
- [ ] Confirmar que `dev` y `main` tienen byte a byte idénticos los tres archivos públicos; el workflow debe fallar si cualquiera difiere.

### Instalación y pacman-key
- [ ] En VM inicializada con `pacman-key --init`, instalar el paquete y comprobar `post_install`.
- [ ] Ejecutar `pacman-key --populate cambonos` manualmente.
- [ ] Repetir populate y comprobar idempotencia.
- [ ] Actualizar el paquete con material público nuevo y comprobar `post_upgrade`.
- [ ] Probar instalación en VM donde `/etc/pacman.d/gnupg` no existe: debe mostrar instrucciones y no bloquear la instalación.
- [ ] Comprobar el estado de claves importadas con `pacman-key --list-keys`.
- [ ] Comprobar que el keyring no elimina ni sustituye claves de Arch.

### Verificación de firmas
- [ ] Sincronizar una base de datos CambonOS con firmas válidas.
- [ ] Instalar un paquete firmado válido.
- [ ] Alterar una copia de un paquete firmado y confirmar rechazo.
- [ ] Probar firma de clave no confiable y confirmar rechazo.
- [ ] Probar base de datos sin firma y confirmar rechazo con `Required`.
- [ ] Probar firma válida pero no confiable y confirmar rechazo con `TrustedOnly`.
- [ ] Confirmar que el cliente no necesita desactivar SigLevel para operar.

### Rotación y recuperación
- [ ] Ensayar rotación ordinaria desde un cliente que solo conoce la clave anterior.
- [ ] Confirmar que el paquete de transición está firmado por la clave anterior.
- [ ] Confirmar que la nueva clave se importa y queda disponible para validar publicaciones siguientes.
- [ ] Ensayar revocación de subclave comprometida en un entorno aislado.
- [ ] Confirmar el orden de distribución de clave nueva y revocación.
- [ ] Ensayar recuperación por compromiso de clave primaria desde un cliente de prueba.
- [ ] Documentar intervención manual y comandos exactos de recuperación.
- [ ] Verificar que una ISO nueva contiene el keyring actualizado.
- [ ] No probar revocaciones reales en el keyring de producción.

## 7. cambonos-release

### Construcción y metadatos
- [ ] `makepkg` termina correctamente.
- [ ] Comprobar presencia de `os-release`, `lsb-release`, helper, hook y licencia.
- [ ] Verificar contenido de `/usr/lib/cambonos/os-release`.
- [ ] Verificar `NAME`, `PRETTY_NAME`, `ID`, `ID_LIKE` y `BUILD_ID`.
- [ ] Verificar contenido de `/usr/lib/cambonos/lsb-release`.

### `/etc/os-release`
- [ ] Instalar sobre Arch con enlace estándar `../usr/lib/os-release`.
- [ ] Confirmar que queda enlazado a `../usr/lib/cambonos/os-release`.
- [ ] Ejecutar helper repetidamente y comprobar idempotencia.
- [ ] Probar ausencia de `/etc/os-release` y confirmar creación del enlace.
- [ ] Probar archivo regular personalizado y confirmar preservación.
- [ ] Probar enlace simbólico personalizado y confirmar preservación.
- [ ] Actualizar `filesystem` y comprobar reparación por hook.
- [ ] Actualizar `systemd` y comprobar reparación por hook.
- [ ] Desinstalar y confirmar restauración del enlace Arch solo cuando el enlace CambonOS siga activo.
- [ ] Modificar el enlace después de instalar y confirmar que la desinstalación respeta el cambio administrativo.

### `/etc/lsb-release`
- [ ] Probar con `lsb-release` no instalado: no debe modificar ni crear `/etc/lsb-release`.
- [ ] Instalar `lsb-release` y después `cambonos-release`; confirmar metadatos CambonOS.
- [ ] Comprobar que se guarda una copia exacta del estado original.
- [ ] Actualizar `cambonos-release` varias veces y confirmar que la copia original no se sobrescribe.
- [ ] Probar que `/etc/lsb-release` era inexistente antes de la instalación.
- [ ] Probar archivo regular preexistente.
- [ ] Probar enlace simbólico preexistente.
- [ ] Probar directorio preexistente y confirmar que se conserva.
- [ ] Modificar manualmente el archivo después de aplicar CambonOS.
- [ ] Desinstalar y confirmar que se conserva la modificación manual y todo el estado de recuperación (`lsb-release.original`, `.was-absent` y `.managed`).
- [ ] Desinstalar sin modificación manual y confirmar restauración del original y limpieza del estado solo tras una restauración satisfactoria.
- [ ] Probar presencia de `/etc/lsb-release.pacnew` y verificar prioridad, tanto con backup original como con marcador de ausencia.
- [ ] Probar `.pacnew` que sea enlace simbólico o directorio: no debe instalarse y el estado debe conservarse.
- [ ] Probar backup que sea directorio: rechazarlo y conservar el estado.
- [ ] Probar que el directorio de estado sea un enlace simbólico o que `.was-absent` sea un directorio: rechazar metadatos y conservarlos.
- [ ] Probar ausencia de `/etc/lsb-release` durante la desinstalación: no eliminar los datos de recuperación.
- [ ] Probar ausencia de backup y marcador `.was-absent`: conservar el estado.
- [ ] Probar backup y marcador `.was-absent` simultáneos: detectar conflicto y conservar el estado.
- [ ] Simular fallos de `mktemp`, `cp` y `mv`; confirmar que el archivo gestionado y los datos originales siguen disponibles.
- [ ] Comprobar que un backup de directorio se rechaza de forma conservadora.
- [ ] Si `lsb-release` no está instalado, comprobar que el helper conserva cualquier estado de recuperación existente.

### Hooks y ciclo de vida
- [ ] Instalar/actualizar/eliminar `lsb-release` y comprobar hook.
- [ ] Comprobar triggers de rutas declaradas.
- [ ] Desinstalar el paquete con y sin `lsb-release`.
- [ ] Confirmar que no se eliminan archivos o enlaces ajenos.
- [ ] Revisar logs de helper ante errores.
- [ ] `pacman -Qkk cambonos-release` sin daños inesperados.

## 8. cambonos-pacman

### Construcción y configuración
- [ ] `makepkg` termina correctamente.
- [ ] El paquete contiene `cambonos.conf`, `cambonos-options.conf`, helper, hook y scriptlet.
- [ ] Stable apunta a `https://mirror.cambonos.org/stable/$arch`.
- [ ] Testing está comentado por defecto y apunta al canal `/testing/$arch`.
- [ ] Ambos bloques utilizan `SigLevel = Required TrustedOnly`.
- [ ] Confirmar dependencias obligatorias (`bash`, `coreutils`, `diffutils`, `gawk`, `cambonos-keyring`).
- [ ] Confirmar `backup` de ambos ficheros de configuración.
- [ ] Las opciones diferenciales son exactamente `Color`, `CheckSpace`, `VerbosePkgLists`, `ParallelDownloads = 3` e `ILoveCandy`.
- [ ] No se duplican `HoldPkg`, `Architecture`, `SigLevel` ni `LocalFileSigLevel`.
- [ ] No se define `DownloadUser` ni `DisableSandbox`.

### Helper `manage-pacman-config`
- [ ] `--ensure` inserta el Include de opciones dentro de `[options]` y el de repositorios al final.
- [ ] `--ensure` repetido es idempotente.
- [ ] `--ensure` repara ambos bloques administrados ausentes.
- [ ] Un Include manual de opciones se conserva y no se duplica.
- [ ] Un Include manual de repositorios se conserva y no se duplica.
- [ ] `--remove` elimina exclusivamente ambos bloques administrados.
- [ ] Los marcadores antiguos de `cambonos-repo` se migran a los nuevos.
- [ ] Marcadores incompletos, anidados o desordenados provocan error y el archivo permanece intacto.
- [ ] La ausencia o duplicidad de `[options]` provoca fallo seguro cuando es necesario insertar su Include.
- [ ] Archivo sin salto final: comportamiento correcto.
- [ ] Ruta inexistente: error sin crear archivo.
- [ ] Ruta simbólica: error sin modificar destino.
- [ ] Ruta directorio: error.
- [ ] Preservación de modo y propietario.
- [ ] Ejecutar pruebas de concurrencia y fallo inducido durante escritura temporal.

### Pacman, hooks y ciclo de vida
- [ ] Instalar `cambonos-keyring` desde fuente local confiable e inicializar/popular el keyring.
- [ ] Instalar `cambonos-pacman` y confirmar ambos bloques administrados.
- [ ] Ejecutar `pacman-conf` y verificar opciones efectivas, especialmente `ParallelDownloads = 3`.
- [ ] Verificar que `pacman-conf --repo-list` reconoce `cambonos`.
- [ ] Habilitar testing en una VM de prueba y verificar `cambonos-testing`.
- [ ] Ejecutar `pacman -Syy` y comprobar descarga/verificación de bases de datos.
- [ ] Simular actualización de `pacman.conf` y comprobar hook ALPM.
- [ ] Comprobar comportamiento con `.pacnew` de ambos ficheros de configuración.
- [ ] Desinstalar `cambonos-pacman` y comprobar retirada de los bloques administrados.
- [ ] Confirmar preservación de otros repositorios, opciones y comentarios.
- [ ] Confirmar que los Include manuales permanecen tras la desinstalación.
- [ ] Probar actualización/reemplazo desde `cambonos-repo`.
- [ ] `pacman -Qkk cambonos-pacman` sin daños inesperados.

## 9. cambonos-grub

### Construcción y contenido
- [ ] `makepkg` termina correctamente en un entorno Arch limpio.
- [ ] Verificar que el paquete contiene el drop-in, helper, hook, tema, iconos y licencias.
- [ ] Confirmar dependencias `grub>=2:2.16`, `os-prober` y `bash`.
- [ ] Confirmar que `/etc/default/grub` no forma parte del paquete.
- [ ] Confirmar que `/etc/default/grub.d/60-cambonos.cfg` está en `backup`.
- [x] Validar el tema y todos los recursos referenciados; revisar visualmente en GRUB UEFI y BIOS cuando estén disponibles.
- [ ] Confirmar que `theme.txt` contiene una sola definición de menú y cuenta atrás, usa la paleta CambonOS, separa iconos y texto con `item_icon_space = 12` y no conserva colores heredados de Vimix.
- [ ] Confirmar atribución de Vimix, GPL-3.0, licencia de Unifont y excepción de incrustación distribuidas.

### Configuración y multiboot
- [x] El drop-in conserva IPv6 y los parámetros `splash quiet loglevel=3`.
- [x] `GRUB_GFXMODE=auto`; no se define `GRUB_GFXPAYLOAD_LINUX`.
- [x] `GRUB_DISABLE_OS_PROBER=false` y `os-prober` detecta otras instalaciones en una VM de prueba multiboot.
- [x] Se conservan timeout/menu y módulos GPT/MBR; las opciones avanzadas aparecen sin submenú, recovery está habilitado y `BootNext` desactivado.
- [x] Las modificaciones locales al drop-in sobreviven a actualización o generan `.pacnew` según la política de pacman.

### Regeneración y ciclo de vida
- [x] El helper no crea `/boot/grub/grub.cfg` si no existe.
- [x] El helper rechaza enlaces simbólicos y destinos que no sean archivos regulares.
- [x] Instalar/actualizar/retirar un kernel activa el hook `PostTransaction`.
- [x] Instalar, actualizar y retirar `cambonos-grub` regenera el menú existente.
- [x] La salida generada pasa `grub-script-check`.
- [x] Un fallo de regeneración se informa sin ocultarse; se puede ejecutar `grub-mkconfig -o /boot/grub/grub.cfg` manualmente.
- [x] No se ejecuta `grub-install` ni se altera la selección de disco o firmware.
- [x] Confirmar que `/boot` está montado antes de las pruebas de actualización del kernel.
- [x] `pacman -Qkk cambonos-grub` no detecta daños inesperados.

## 10. cambonos-plymouth

### Construcción y configuración
- [ ] `makepkg` termina correctamente y el paquete declara `plymouth` y `mkinitcpio>=36`.
- [ ] Todos los recursos de `files/themes/cambonos/` se instalan en `/usr/share/plymouth/themes/cambonos/`.
- [ ] El tema empaqueta el fondo Plymouth como PNG de 3840 × 2160, escala la imagen y conserva el icono de marca para los diálogos.
- [x] El tema usa el fondo CambonOS, la barra `#70E7E6`, desactiva el spinner y conserva solo la barra de progreso durante el arranque.
- [x] La configuración conserva `ShowDelay=0`; el parámetro `splash` activa el tema sin una espera añadida.
- [x] `quiet` está configurado en GRUB para ocultar mensajes de consola; comprobar el parámetro equivalente en otros cargadores.

### mkinitcpio y ciclo de vida
- [x] El drop-in se instala en `/etc/mkinitcpio.conf.d/` con política `backup` y no reemplaza `/etc/mkinitcpio.conf`.
- [x] Con `udev` o `systemd`, Plymouth se inserta después del hook de init y antes de `encrypt`/`sd-encrypt`.
- [x] Sin cifrado, Plymouth se inserta tras `udev`/`systemd`; con un hook preexistente no se duplica.
- [x] Revisar presets con `ALL_config`; actualizar los presets antiguos que no carguen drop-ins.
- [x] En una VM Arch limpia, instalar con un kernel presente y comprobar selección del tema y regeneración de todos los presets.
- [x] Actualizar preservando un tema personalizado y comprobar que el initramfs se reconstruye.
- [x] Desinstalar: restaurar el tema predeterminado solo si CambonOS seguía seleccionado, retirar el hook propio y regenerar initramfs.
- [x] Probar root cifrado con `encrypt` y `sd-encrypt`, desbloqueo por teclado y fallback de consola.
- [x] Comprobar visualmente en UEFI/BIOS y GPU real: aparición temprana, ausencia de líneas de arranque, resolución, varios monitores y transición al display manager.

## 11. Validación del repositorio y publicación

- [ ] Validar snapshots `dev` y `main` con `cambonos.py validate`.
- [ ] Confirmar igualdad del material keyring entre canales.
- [ ] Construir ambos canales desde snapshots fijados.
- [ ] Confirmar que cada paquete se construye en contenedor separado.
- [ ] Confirmar que `depends` no se instala como dependencia de build.
- [ ] Confirmar instalación de `makedepends` y `checkdepends` cuando proceda.
- [ ] Verificar orden topológico de dependencias internas de construcción.
- [ ] Verificar que un ciclo de `makedepends` detiene la construcción.
- [ ] Confirmar que el manifiesto registra commit, rama, imagen, entorno, versiones y hashes.
- [ ] Confirmar que el cambio de fuente sin aumento de versión falla.
- [ ] Confirmar que un retroceso de versión falla.
- [ ] Confirmar que una reconstrucción de la misma fuente y versión con un binario diferente permite publicar.
- [ ] Confirmar que un cambio de fuente con la misma versión bloquea la publicación.
- [ ] Confirmar que un cambio de fuente con incremento de versión permite publicar.
- [ ] Confirmar que un artefacto alterado después de generar el manifiesto se rechaza por discrepancia de `package_hash`.
- [ ] Confirmar que los paquetes de stable y testing se comparan de forma independiente.
- [ ] Verificar firmas de paquetes, bases de datos, alias y manifiestos.
- [ ] Confirmar que el job build no recibe secretos de firma.
- [ ] Confirmar que signing no ejecuta PKGBUILD ni scripts `.install`.
- [ ] Confirmar que publish no recibe secretos de firma.
- [ ] Desplegar a Pages en un entorno de prueba.
- [ ] Descargar desde un cliente Arch de prueba los índices y bases de datos.
- [ ] Sincronizar stable y testing con la política de firmas activa.
- [ ] Instalar y actualizar paquetes desde el mirror público.
- [ ] Alterar un artefacto en un mirror de prueba y confirmar rechazo.
- [ ] Simular fallo en validate/build/signing y confirmar que publish no se ejecuta.
- [ ] Confirmar que una publicación fallida no sustituye la publicación anterior.
- [ ] Confirmar que los índices del sitio y el manifiesto coinciden con los artefactos desplegados.

## 12. Evidencias de cierre

Por cada paquete, guardar:
- Commit auditado.
- Versión `pkgver-pkgrel`.
- Log de construcción.
- Listado de archivos del paquete.
- Resultado de instalación y actualización.
- Resultado de pruebas funcionales.
- Resultado de hooks.
- Resultado de desinstalación.
- Incidencias encontradas y decisión adoptada.

Una casilla solo debe marcarse cuando exista evidencia reproducible (log, salida de comando, captura o resultado de prueba). Las pruebas no ejecutadas deben quedar sin marcar; no inferir su éxito a partir de la suite unitaria.

## 13. Registro de validación de `dev`

### Ejecución del 2026-11-06

- Rama y commit probados: `dev`, `9e75fb15db9c2518e2fdd920326dc8383dbbb309`.
- Referencia comparada: `main`, `c79c5f90bea97079bdaea80976869b7614e7a2f9`; `dev` contiene 28 commits exclusivos y `main` 4. No se realizó merge.
- Entorno local: CambonOS rolling, arquitectura `x86_64`; árbol de trabajo limpio.
- Versiones instaladas en el anfitrión: branding `0.1.1-3`, fastfetch `0.1.0-14`, grub `0.1.0-7`, keyring `0.1.0-3`, pacman `0.1.0-1`, plymouth `0.1.0-2`, release `0.1.0-8`, shell-prompt `0.1.0-5`, zsh `0.1.0-3`.
- `cambonos-grub` y `cambonos-plymouth` están una revisión por detrás de `dev` (`0.1.0-8` y `0.1.0-3`, respectivamente). No se actualizaron en el anfitrión.
- Entorno de paquetes: VM Arch `x86_64` `arch-pruebas`, raíz ZFS `local-ssd/subvol-110-disk-0`; el usuario confirmó que es desechable/restaurable. No había kernel, GRUB, mkinitcpio, Plymouth ni presets, y `/boot` estaba vacío. No hay comando `zfs` para comprobar el snapshot independientemente.
- El manifiesto público de `testing` apunta exactamente al commit de `dev` `9e75fb15db9c2518e2fdd920326dc8383dbbb309` y contiene los nueve paquetes instalados.
- Las casillas visuales/funcionales de GRUB, Plymouth y Zsh marcadas en sus secciones se basan en la confirmación del usuario de que esas pruebas se realizaron fuera de esta VM; no se atribuyen al ensayo de `arch-pruebas`.

### Comprobaciones automáticas ejecutadas

- [x] `python3 -m unittest discover -s tests -v`: 183 tests, resultado `OK`.
- [x] `python3 -m compileall -q scripts`: correcto; el bytecode temporal se mantuvo fuera del repositorio.
- [x] `python3 scripts/cambonos.py validate --source-root . --channel testing --branch dev --commit 9e75fb15db9c2518e2fdd920326dc8383dbbb309`: validación estática correcta para 9 paquetes. No se proporcionó manifiesto anterior, por lo que esta ejecución no valida la política de versiones contra una publicación previa.
- [x] `bash -n` sobre los archivos `.sh`, `.bash` y `.install` de `packages/`: correcto.
- [x] `xmllint --noout` sobre los SVG de `packages/`: correcto. Esto no sustituye la comprobación visual de renderizado.
- [x] `pacman -Syy` sincronizó `core`, `extra`, `cambonos` y `cambonos-testing` bajo la política de firma requerida; la clave CambonOS se verificó contra el fingerprint confirmado independientemente.
- [x] `pacman -Qkk` después de la reinstalación: 0 archivos alterados en cada uno de los nueve paquetes en `arch-pruebas`.
- [x] `pacman-conf --repo-list` mostró `core`, `extra`, `cambonos-testing` y `cambonos`; `ParallelDownloads` efectivo fue `3`.
- [x] El gestor `/usr/lib/cambonos-pacman/manage-pacman-config --ensure` se ejecutó dos veces; el hash de `/etc/pacman.conf` permaneció idéntico.
- [ ] En el anfitrión, `pacman -Qkk` no encontró archivos de paquete alterados, pero sí diferencias de backup en `/etc/default/grub.d/60-cambonos.cfg`, `/etc/pacman.d/cambonos.conf` y `/etc/skel/.zshrc`. No se sobrescribieron; revisar si son cambios administrativos esperados.

### Construcción, instalación y ciclo de vida

- [ ] No se construyeron paquetes con `makepkg`; `Docker`, `Podman` y `namcap` no están disponibles en el anfitrión. Las instalaciones usaron los artefactos firmados del mirror `testing`, publicados para el commit exacto indicado arriba.
- [x] Las cinco firmas del baseline `stable` (branding `0.1.0-3`, fastfetch `0.1.0-10`, keyring `0.1.0-2`, release `0.1.0-4`, repo `0.1.0-2`) verificaron con la clave CambonOS.
- [x] `pacman -Syu` actualizó la base Arch (dos paquetes), instaló el baseline stable y luego actualizó a `testing`: branding `0.1.0-3` → `0.1.1-3`, fastfetch `0.1.0-10` → `0.1.0-14`, keyring `0.1.0-2` → `0.1.0-3`, release `0.1.0-4` → `0.1.0-8`; `cambonos-repo` fue reemplazado por `cambonos-pacman`. GRUB, Plymouth, shell-prompt y Zsh se instalaron por primera vez.
- [x] Se reinstalaron los nueve paquetes de `testing`; versiones finales: branding `0.1.1-3`, fastfetch `0.1.0-14`, grub `0.1.0-8`, keyring `0.1.0-3`, pacman `0.1.0-1`, plymouth `0.1.0-3`, release `0.1.0-8`, shell-prompt `0.1.0-5`, zsh `0.1.0-3`.
- [x] `cambonos-fastfetch` mostró la salida CambonOS; `fc-match 'CambonOS Symbols'` seleccionó la fuente CambonOS; `plymouth-set-default-theme` devolvió `cambonos`; el fondo instalado es PNG de 3840 × 2160.
- [x] Los arranques de prueba de Bash y Zsh ejecutaron Fastfetch y terminaron con código 0. Se ejecutaron sin TTY; no validan interacción visual ni todos los modos login/no-login.
- [ ] Revisar los `.pacnew` que generó la actualización Arch: `/etc/pacman.d/mirrorlist.pacnew`, `/etc/fstab.pacnew`, dos perfiles TPM2 y `/etc/resolv.conf.pacnew`. No se modificaron.
- **Incidencia detectada y corrección solicitada:** el helper de `cambonos-pacman` usa `cmp`, pero `0.1.0-1` no declaraba `diffutils`. En la VM mínima, el primer scriptlet mostró `cmp: command not found`; se instaló `diffutils 3.12-2` manualmente para completar las pruebas de esa revisión. La corrección añade la dependencia y aumenta `pkgrel` a `2`; queda pendiente construir e instalar `0.1.0-2` para validar el artefacto corregido.
- [ ] En `arch-pruebas` no se validó el arranque real de GRUB/Plymouth: la VM no tiene kernel ni presets de mkinitcpio; allí solo se comprobaron instalación, scriptlets y tema seleccionado. Las pruebas visuales/funcionales realizadas por el usuario están registradas como validadas en las secciones de GRUB y Plymouth. No se ejecutó `grub-install` ni se alteró `/boot` en esta VM.

### Pruebas que requieren intervención manual

- [ ] Revisar visualmente branding y Fastfetch en el hardware/resoluciones previstos.
- [x] Revisar visualmente el tema GRUB y el splash Plymouth en el hardware/resoluciones previstos; validación confirmada por el usuario.
- [x] Probar GRUB en UEFI/BIOS y multiboot; probar Plymouth durante el arranque, con cifrado, teclado, varios monitores y transición al display manager; validación confirmada por el usuario.
- [ ] Abrir sesiones con TTY real de Bash y Fish, probar login/no-login y no interactivo, `CAMBONOS_NO_FASTFETCH=1` y la salida visual de sus integraciones.
- [x] Validar sesiones y comportamiento interactivo de Zsh; validación confirmada por el usuario.
- [ ] Probar rechazo de firma inválida/clave no confiable y la recuperación de keyring en un cliente aislado; no ensayar rotación ni revocación en producción.
- [ ] Revisar las diferencias de los archivos `backup` detectados por `pacman -Qkk` y confirmar que las pruebas no sustituyen cambios administrativos.
