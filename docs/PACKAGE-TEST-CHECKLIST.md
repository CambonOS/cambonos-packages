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
- [ ] Zsh interactivo con `cambonos-zsh`: Fastfetch aparece una vez mediante `conf.d`.
- [ ] Zsh interactivo sin `cambonos-zsh`: no hay integración automática y el fragmento puede cargarse manualmente.
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
- [ ] Zsh interactivo con `cambonos-zsh` carga Starship desde `conf.d`.
- [ ] Zsh sin `cambonos-zsh` no tiene integración automática y puede integrarse manualmente desde `~/.zshrc`.
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
- [ ] El helper crea `/etc/zsh/zshrc` si no existe.
- [ ] El bloque global carga los fragmentos `*.zsh` de `conf.d` en orden lexicográfico.
- [ ] Los fragmentos base de completions, teclas, historial y plugins están presentes.
- [ ] `compinit` se inicializa antes de cargar los plugins.
- [ ] Autosuggestions se carga antes de syntax highlighting.
- [ ] El modo de edición Emacs está activo.
- [ ] Home y End mueven el cursor al principio/final de la línea actual.
- [ ] Delete elimina el carácter bajo el cursor.
- [ ] PageUp y PageDown buscan en el historial por el prefijo actual.
- [ ] Historial persistente de 100.000 entradas.
- [ ] `autocd`, `correct` y aliases acordados funcionan.
- [ ] No se fuerza `EDITOR` ni se mantiene el alias `tar` que altera su uso normal.
- [ ] `cambonos-shell-prompt` se carga desde su fragmento Zsh.
- [ ] Fastfetch se carga si está instalado, sin ser dependencia de Zsh.
- [ ] Una configuración personal `~/.zshrc` se ejecuta después de la configuración global y puede personalizarla.
- [ ] Un usuario creado usando `/etc/skel` recibe un `.zshrc` vacío y la configuración global CambonOS sigue cargándose.

### Gestor y ciclo de vida
- [ ] `install` crea el bloque sin borrar contenido preexistente.
- [ ] `repair` es idempotente.
- [ ] `remove` retira solo el bloque administrado.
- [ ] Si el helper creó `/etc/zsh/zshrc` y no queda contenido externo, lo elimina al desinstalar.
- [ ] Si el archivo existía previamente o contiene contenido externo, lo conserva.
- [ ] Marcadores incompletos, duplicados o desordenados provocan fallo conservador.
- [ ] Un enlace simbólico o directorio en `/etc/zsh/zshrc` no se reemplaza.
- [ ] El helper utiliza `/run/lock/cambonos-shell-integration.lock`.
- [ ] `pacman -Qkk cambonos-zsh` no detecta daños inesperados.



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
- [ ] Confirmar dependencia de `cambonos-keyring`.
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
- [ ] Validar el tema y todos los recursos referenciados; revisar visualmente en GRUB UEFI y BIOS cuando estén disponibles.
- [ ] Confirmar que `theme.txt` contiene una sola definición de menú y cuenta atrás, usa la paleta CambonOS, separa iconos y texto con `item_icon_space = 12` y no conserva colores heredados de Vimix.
- [ ] Confirmar atribución de Vimix, GPL-3.0, licencia de Unifont y excepción de incrustación distribuidas.

### Configuración y multiboot
- [ ] El drop-in conserva IPv6 y los parámetros `splash quiet loglevel=3`.
- [ ] `GRUB_GFXMODE=auto`; no se define `GRUB_GFXPAYLOAD_LINUX`.
- [ ] `GRUB_DISABLE_OS_PROBER=false` y `os-prober` detecta otras instalaciones en una VM de prueba multiboot.
- [ ] Se conservan timeout/menu y módulos GPT/MBR; las opciones avanzadas aparecen sin submenú, recovery está habilitado y `BootNext` desactivado.
- [ ] Las modificaciones locales al drop-in sobreviven a actualización o generan `.pacnew` según la política de pacman.

### Regeneración y ciclo de vida
- [ ] El helper no crea `/boot/grub/grub.cfg` si no existe.
- [ ] El helper rechaza enlaces simbólicos y destinos que no sean archivos regulares.
- [ ] Instalar/actualizar/retirar un kernel activa el hook `PostTransaction`.
- [ ] Instalar, actualizar y retirar `cambonos-grub` regenera el menú existente.
- [ ] La salida generada pasa `grub-script-check`.
- [ ] Un fallo de regeneración se informa sin ocultarse; se puede ejecutar `grub-mkconfig -o /boot/grub/grub.cfg` manualmente.
- [ ] No se ejecuta `grub-install` ni se altera la selección de disco o firmware.
- [ ] Confirmar que `/boot` está montado antes de las pruebas de actualización del kernel.
- [ ] `pacman -Qkk cambonos-grub` no detecta daños inesperados.

## 10. cambonos-plymouth

### Construcción y configuración
- [ ] `makepkg` termina correctamente y el paquete declara `plymouth` y `mkinitcpio>=36`.
- [ ] Todos los recursos de `files/themes/cambonos/` se instalan en `/usr/share/plymouth/themes/cambonos/`.
- [ ] El icono de cabecera coincide visualmente con el recurso canónico de branding y mide 256 × 256.
- [ ] El tema usa el fondo `#061C31`, la barra `#70E7E6` y transición inmediata.
- [ ] La configuración conserva `ShowDelay=0`; el parámetro `splash` activa el tema sin una espera añadida.
- [ ] `quiet` está configurado en GRUB para ocultar mensajes de consola; comprobar el parámetro equivalente en otros cargadores.

### mkinitcpio y ciclo de vida
- [ ] El drop-in se instala en `/etc/mkinitcpio.conf.d/` con política `backup` y no reemplaza `/etc/mkinitcpio.conf`.
- [ ] Con `udev` o `systemd`, Plymouth se inserta después del hook de init y antes de `encrypt`/`sd-encrypt`.
- [ ] Sin cifrado, Plymouth se inserta tras `udev`/`systemd`; con un hook preexistente no se duplica.
- [ ] Revisar presets con `ALL_config`; actualizar los presets antiguos que no carguen drop-ins.
- [ ] En una VM Arch limpia, instalar con un kernel presente y comprobar selección del tema y regeneración de todos los presets.
- [ ] Actualizar preservando un tema personalizado y comprobar que el initramfs se reconstruye.
- [ ] Desinstalar: restaurar el tema predeterminado solo si CambonOS seguía seleccionado, retirar el hook propio y regenerar initramfs.
- [ ] Probar root cifrado con `encrypt` y `sd-encrypt`, desbloqueo por teclado y fallback de consola.
- [ ] Comprobar visualmente en UEFI/BIOS y GPU real: aparición temprana, ausencia de líneas de arranque, resolución, varios monitores y transición al display manager.

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
