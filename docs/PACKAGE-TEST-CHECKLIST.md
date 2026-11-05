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
- [ ] El paquete contiene la licencia y los recursos de `files/` instalados por el `PKGBUILD`.
- [ ] Los seis SVG y `cambonos-logo.txt` se instalan en `/usr/share/cambonos/branding/`.
- [ ] El enlace `/usr/share/icons/hicolor/scalable/apps/cambonos-logo.svg` apunta al SVG canónico `cambonos-icon.svg`.
- [ ] No se publica el nombre histórico `/usr/share/icons/hicolor/scalable/apps/cambonos.svg`; se considera obsoleto y no se mantiene como alias.
- [ ] Los enlaces `/usr/share/pixmaps/cambonos-logo.svg` y `/usr/share/pixmaps/cambonos-logo-text.svg` apuntan a `cambonos-icon.svg` y `cambonos-text.svg`, respectivamente.
- [ ] `xmllint --noout` valida los seis SVG instalados.
- [ ] Confirmar que los SVG distribuidos son los artefactos aprobados por el equipo de diseño.
- [ ] La validación visual, la paleta, la legibilidad y las variantes de tamaño se verifican en el flujo del equipo de diseño, no en este repositorio de empaquetado.

### Ciclo de vida
- [ ] Instalar el paquete en una VM limpia.
- [ ] Actualizar a una compilación con recursos modificados e incrementar `pkgrel`/`pkgver`.
- [ ] Confirmar que la actualización reemplaza los recursos por los nuevos.
- [ ] Desinstalar y confirmar que solo se eliminan archivos propiedad del paquete.
- [ ] Confirmar que no se modifican `/etc`, `$HOME` ni configuraciones de escritorio.

## 3. cambonos-fastfetch

### Construcción y contenido
- [ ] `makepkg` termina correctamente.
- [ ] Verificar todas las rutas instaladas declaradas en el PKGBUILD.
- [ ] Confirmar dependencias obligatorias (`fastfetch`, `cambonos-release`, `bash`, `util-linux`).
- [ ] Instalar y probar por separado los opcionales Zsh y Fish.
- [ ] Ejecutar `cambonos-fastfetch` y comprobar código de salida y salida visual.
- [ ] Confirmar que carga `/usr/share/cambonos/fastfetch/config.jsonc`.
- [ ] Confirmar que carga `/usr/share/cambonos/fastfetch/logo.txt`.
- [ ] Validar la configuración con la versión real de Fastfetch instalada.

### Inicio de shells
- [ ] Bash interactivo de login: Fastfetch aparece una vez.
- [ ] Bash interactivo no-login: Fastfetch aparece una vez.
- [ ] Bash no interactivo: no aparece Fastfetch.
- [ ] Zsh interactivo de login: Fastfetch aparece una vez.
- [ ] Zsh interactivo no-login: Fastfetch aparece una vez.
- [ ] Zsh no interactivo: no aparece Fastfetch.
- [ ] Fish interactivo: Fastfetch aparece una vez.
- [ ] Fish no interactivo: no aparece Fastfetch.
- [ ] Shell POSIX de login que carga `/etc/profile`: Fastfetch aparece una vez.
- [ ] Combinaciones donde `/etc/profile` y rc del shell se ejecutan en la misma sesión: solo una invocación.
- [ ] Shell opcional ausente: no se produce error ni se crean integraciones para un ejecutable inexistente.
- [ ] `CAMBONOS_NO_FASTFETCH=1` desactiva el inicio automático en cada shell aplicable.
- [ ] Valor vacío de `CAMBONOS_NO_FASTFETCH` no lo desactiva.
- [ ] `_CAMBONOS_FASTFETCH_RAN` evita ejecuciones duplicadas.

### Gestor de integraciones
- [ ] Ejecutar `install` con archivos globales preexistentes y comprobar que conserva todo el contenido exterior.
- [ ] Ejecutar `install` dos veces y comprobar idempotencia.
- [ ] Ejecutar `repair` dos veces y comprobar idempotencia.
- [ ] Eliminar manualmente el bloque completo y comprobar que `repair` lo restaura.
- [ ] Insertar marcadores duplicados, invertidos o incompletos y comprobar que el helper falla sin reescribir el archivo.
- [ ] Sustituir `/etc/bash.bashrc` por un enlace simbólico en una VM de prueba y comprobar que no lo reemplaza.
- [ ] Repetir con `/etc/zsh/zshrc`.
- [ ] Repetir con una ruta que sea directorio.
- [ ] Comprobar permisos y propietario de los archivos después de reparación.
- [ ] Comprobar bloqueo concurrente ejecutando dos instancias del helper.
- [ ] Comprobar limpieza de temporales tras éxito y tras fallo inducido.
- [ ] Ejecutar `check` con todos los shells instalados y comprobar su resultado.
- [ ] Ejecutar `check` con solo Bash, con Bash+Zsh y con Bash+Zsh+Fish.

### Hooks y ciclo de vida
- [ ] Instalar el paquete y revisar el resultado de `post_install`.
- [ ] Actualizar el paquete y revisar `post_upgrade`.
- [ ] Simular actualización de Bash y comprobar hook ALPM.
- [ ] Simular actualización de Zsh y comprobar hook ALPM.
- [ ] Comprobar que el hook no se ejecuta para operaciones no declaradas.
- [ ] Desinstalar y confirmar que se eliminan solo los bloques gestionados.
- [ ] Confirmar que los archivos globales conservan las personalizaciones externas al bloque.
- [ ] Comprobar comportamiento cuando el helper falla: mensaje visible y transacción no abortada según diseño.

## 4. cambonos-keyring

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

## 5. cambonos-release

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
- [ ] Desinstalar y confirmar que se conserva la modificación manual y que `/var/lib/cambonos-release` mantiene el backup y el estado gestionado.
- [ ] Desinstalar sin modificación manual y confirmar restauración del original y limpieza del estado solo tras una restauración satisfactoria.
- [ ] Probar presencia de `/etc/lsb-release.pacnew` y verificar prioridad.
- [ ] Si `/etc/lsb-release` ha desaparecido pero existe un backup original, comprobar que se restaura el backup y no se elimina el estado antes de completar la recuperación.
- [ ] Si `lsb-release` no está instalado, comprobar que el helper conserva cualquier estado de recuperación existente.
- [ ] Simular un fallo al crear el directorio temporal de restauración y comprobar que el backup permanece disponible.
- [ ] Simular error de escritura o falta de espacio y comprobar que no queda un archivo parcial.

### Hooks y ciclo de vida
- [ ] Instalar/actualizar/eliminar `lsb-release` y comprobar hook.
- [ ] Comprobar triggers de rutas declaradas.
- [ ] Desinstalar el paquete con y sin `lsb-release`.
- [ ] Confirmar que no se eliminan archivos o enlaces ajenos.
- [ ] Revisar logs de helper ante errores.
- [ ] `pacman -Qkk cambonos-release` sin daños inesperados.

## 6. cambonos-repo

### Construcción y configuración
- [ ] `makepkg` termina correctamente.
- [ ] El paquete contiene `cambonos.conf`, helper, hook y scriptlet.
- [ ] Stable apunta a `https://mirror.cambonos.org/stable/$arch`.
- [ ] Testing está comentado por defecto y apunta al canal `/testing/$arch`.
- [ ] Ambos bloques utilizan `SigLevel = Required TrustedOnly`.
- [ ] Confirmar dependencia de `cambonos-keyring`.
- [ ] Confirmar `backup=('etc/pacman.d/cambonos.conf')`.

### Helper `manage-pacman-include`
- [ ] `--ensure` añade el bloque al final de un `pacman.conf` normal.
- [ ] `--ensure` repetido es idempotente.
- [ ] `--ensure` repara un bloque administrado ausente.
- [ ] Include manual idéntico fuera del bloque: se conserva y no se adopta.
- [ ] Include manual junto con bloque administrado duplicado: se conserva el manual y se elimina el bloque administrado.
- [ ] `--remove` elimina exclusivamente el bloque administrado.
- [ ] `--remove` sin bloque devuelve éxito sin modificar el archivo.
- [ ] Marcador de inicio sin final: error y archivo intacto.
- [ ] Marcador final sin inicio: error y archivo intacto.
- [ ] Marcadores desordenados o duplicados: error y archivo intacto.
- [ ] Archivo sin salto final: comportamiento correcto.
- [ ] Archivo vacío: comportamiento correcto.
- [ ] Ruta inexistente: error sin crear archivo.
- [ ] Ruta simbólica: error sin modificar destino.
- [ ] Ruta directorio: error.
- [ ] Preservación de modo y propietario.
- [ ] Comprobar ACL/xattrs si son relevantes para el entorno objetivo.
- [ ] Ejecutar pruebas de concurrencia y fallo inducido durante escritura temporal.

### Pacman, hooks y ciclo de vida
- [ ] Instalar `cambonos-keyring` desde fuente local confiable.
- [ ] Inicializar/popular keyring.
- [ ] Instalar `cambonos-repo`.
- [ ] Confirmar bloque administrado en `/etc/pacman.conf`.
- [ ] Ejecutar `pacman-conf` y verificar que reconoce el repositorio `cambonos`.
- [ ] Habilitar testing en una VM de prueba y verificar `cambonos-testing`.
- [ ] Ejecutar `pacman -Syy` y comprobar descarga/verificación de bases de datos.
- [ ] Instalar un paquete desde stable con firmas válidas.
- [ ] Simular actualización de `pacman.conf` y comprobar hook ALPM.
- [ ] Comprobar comportamiento con `.pacnew`.
- [ ] Confirmar que edición manual arbitraria no queda prometida como detectada por el hook.
- [ ] Desinstalar `cambonos-repo` y comprobar retirada del bloque gestionado.
- [ ] Confirmar preservación de otros repositorios, opciones y comentarios.
- [ ] Confirmar que un Include manual permanece tras la desinstalación.
- [ ] `pacman -Qkk cambonos-repo` sin daños inesperados.

## 7. Validación del repositorio y publicación

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

## 8. Evidencias de cierre

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
