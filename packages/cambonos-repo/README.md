# cambonos-repo

Configuración de los repositorios pacman de CambonOS e integración reversible con `/etc/pacman.conf`.

## Responsabilidad

Este paquete distribuye la configuración de los repositorios CambonOS y añade un bloque administrado a la configuración global de pacman. Depende del paquete `cambonos-keyring` para que las firmas puedan verificarse.

## Dependencias

- `bash`
- `coreutils`
- `gawk`
- `cambonos-keyring`

## Configuración distribuida

Archivo: `/etc/pacman.d/cambonos.conf`.

```ini
#[cambonos-testing]
#SigLevel = Required TrustedOnly
#Server = https://mirror.cambonos.org/testing/$arch

[cambonos]
SigLevel = Required TrustedOnly
Server = https://mirror.cambonos.org/stable/$arch
```

Stable queda habilitado y testing comentado. Testing se reserva principalmente para desarrollo y pruebas internas.

## Integración con `/etc/pacman.conf`

El helper `/usr/lib/cambonos-repo/manage-pacman-include` ofrece:

```bash
sudo /usr/lib/cambonos-repo/manage-pacman-include --ensure
sudo /usr/lib/cambonos-repo/manage-pacman-include --remove
sudo /usr/lib/cambonos-repo/manage-pacman-include --ensure /ruta/a/pacman.conf
```

El argumento de ruta alternativo está destinado a pruebas aisladas. En operación normal se utiliza `/etc/pacman.conf`.

El bloque insertado es:

```ini
# >>> cambonos-repo: managed by cambonos-repo
# Gestionado por cambonos-repo: desinstala el paquete para deshabilitarlo.
Include = /etc/pacman.d/cambonos.conf
# <<< cambonos-repo
```

El helper:
- Solo modifica archivos regulares, no enlaces simbólicos.
- Elimina únicamente bloques completos delimitados por sus marcadores.
- Falla sin reescribir el archivo si detecta marcadores incompletos o desordenados.
- Conserva un `Include` manual fuera del bloque.
- Evita duplicados.
- Es idempotente.
- Escribe mediante un temporal en el mismo directorio y renombrado atómico.
- Conserva modo y propietario del archivo original.

El paquete declara `backup=('etc/pacman.d/cambonos.conf')`, por lo que pacman puede preservar modificaciones locales y generar `.pacnew` durante una actualización.

## Hooks y scriptlet

- `post_install`: garantiza el bloque `Include`.
- `post_upgrade`: repara el bloque.
- `pre_remove`: elimina exclusivamente el bloque administrado.
- Hook ALPM `Type = Path`, `Target = etc/pacman.conf`, en `PostTransaction`: vuelve a garantizar la integración después de transacciones que incluyan esa ruta.

El hook no detecta todas las modificaciones manuales arbitrarias ni cambios realizados por scriptlets que no formen parte de la lista de archivos de la transacción.

## Bootstrap

En instalaciones nuevas, instalar primero `cambonos-keyring` desde el medio local confiable y poblar el keyring de pacman. Después instalar `cambonos-repo` y habilitar el repositorio remoto. No se debe depender del repositorio remoto para obtener la primera copia de su propia clave de confianza.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-repo

grep -n -A4 -B1 'cambonos-repo: managed' /etc/pacman.conf
cat /etc/pacman.d/cambonos.conf
sudo pacman -Syy
```

Verificar que `pacman -Syy` descarga y valida las bases de datos firmadas. No deshabilitar la comprobación de firmas para resolver errores de confianza.

## Pruebas de validación

- [ ] Construcción correcta con `makepkg`.
- [ ] El paquete contiene `cambonos.conf`, helper, hook y licencia según el PKGBUILD.
- [ ] La configuración stable apunta al mirror canónico y exige firmas.
- [ ] Testing está comentado por defecto y, al habilitarse, exige firmas.
- [ ] La dependencia `cambonos-keyring` se instala antes de utilizar el repositorio.
- [ ] `post_install` añade el bloque al final de `/etc/pacman.conf`.
- [ ] `post_upgrade` repara un bloque eliminado o incompleto cuando los marcadores siguen siendo válidos.
- [ ] `--ensure` es idempotente.
- [ ] Un `Include` manual existente se conserva y no se adopta.
- [ ] Si hay `Include` manual y bloque administrado duplicado, se elimina el bloque administrado y se conserva el manual.
- [ ] `--remove` elimina únicamente el bloque administrado.
- [ ] `--remove` conserva un `Include` manual.
- [ ] Marcadores incompletos, duplicados o desordenados provocan error y el archivo permanece byte a byte intacto.
- [ ] Un archivo sin salto de línea final se procesa correctamente.
- [ ] Si `/etc/pacman.conf` falta, el helper falla sin crear una configuración global.
- [ ] Si `/etc/pacman.conf` es un enlace simbólico o no es archivo regular, no lo reemplaza.
- [ ] Se preservan modo y propietario tras la modificación.
- [ ] Se comprueba el comportamiento con `/etc/pacman.d/cambonos.conf` modificado y generación de `.pacnew`.
- [ ] El hook ALPM se ejecuta tras una transacción que instala/actualiza `pacman.conf`.
- [ ] El hook no entra en bucle ni provoca una transacción recursiva.
- [ ] La desinstalación elimina la integración sin tocar el resto de `pacman.conf`.
- [ ] Una sincronización real con el mirror valida firmas de bases de datos.
- [ ] Una instalación de paquete desde stable valida firma y confianza.
- [ ] Una firma incorrecta o clave no confiable provoca rechazo.
- [ ] `pacman -Qkk cambonos-repo` no detecta alteraciones inesperadas.

## Notas

El orden de repositorios en `pacman.conf` influye en la selección de paquetes. La integración añade el bloque al final para no alterar la prioridad de los repositorios oficiales de Arch.
