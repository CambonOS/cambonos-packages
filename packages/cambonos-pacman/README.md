# cambonos-pacman

Configuración de los repositorios CambonOS y personalizaciones diferenciales de pacman, con integración reversible en `/etc/pacman.conf`.

## Responsabilidad

Este paquete distribuye los canales Stable y Testing de CambonOS y aplica únicamente las opciones que difieren de la configuración de referencia de Arch Linux. No reemplaza `/etc/pacman.conf` ni redefine valores predeterminados que Arch ya proporciona.

Depende de `cambonos-keyring` para que las firmas de los repositorios puedan verificarse.

## Dependencias

- `bash`
- `coreutils`
- `gawk`
- `cambonos-keyring`

## Configuración distribuida

### Repositorios: `/etc/pacman.d/cambonos.conf`

```ini
#[cambonos-testing]
#SigLevel = Required TrustedOnly
#Server = https://mirror.cambonos.org/testing/$arch

[cambonos]
SigLevel = Required TrustedOnly
Server = https://mirror.cambonos.org/stable/$arch
```

Stable queda habilitado y testing comentado. Testing se reserva principalmente para desarrollo y pruebas internas. Ambos canales exigen firmas cuando se habilitan.

### Opciones diferenciales: `/etc/pacman.d/cambonos-options.conf`

```ini
Color
CheckSpace
VerbosePkgLists
ParallelDownloads = 3
ILoveCandy
```

El archivo no contiene una sección `[options]`: se incluye desde dentro de la sección `[options]` existente en `/etc/pacman.conf`.

Estas directivas representan las personalizaciones de CambonOS respecto a la configuración de referencia de Arch: salida en color, comprobación de espacio, lista detallada de paquetes, tres descargas paralelas y barra de progreso estilo Pac-Man. No se duplican `HoldPkg`, `Architecture`, `SigLevel` ni otras opciones que deben conservar el valor predeterminado de Arch. Tampoco se modifica `DownloadUser` ni se desactiva el sandbox.

Ambos archivos se declaran en `backup`, de modo que pacman puede conservar modificaciones locales y generar `.pacnew` durante una actualización.

## Integración con `/etc/pacman.conf`

El helper `/usr/lib/cambonos-pacman/manage-pacman-config` ofrece:

```bash
sudo /usr/lib/cambonos-pacman/manage-pacman-config --ensure
sudo /usr/lib/cambonos-pacman/manage-pacman-config --remove
sudo /usr/lib/cambonos-pacman/manage-pacman-config --ensure /ruta/a/pacman.conf
```

El argumento de ruta alternativo está destinado a pruebas aisladas. En operación normal se utiliza `/etc/pacman.conf`.

El helper administra dos bloques independientes:

- El `Include` de `cambonos-options.conf`, insertado dentro de la sección `[options]`.
- El `Include` de `cambonos.conf`, añadido al final para no alterar la prioridad de los repositorios oficiales de Arch.

Si ya existe un `Include` manual de cualquiera de esos archivos, se conserva y no se añade otro bloque administrado para esa configuración. La integración reconoce y migra los marcadores del paquete anterior `cambonos-repo`.

El helper:
- Solo modifica archivos regulares, no enlaces simbólicos.
- Elimina únicamente bloques completos delimitados por sus marcadores.
- Falla sin reescribir el archivo si detecta marcadores incompletos, anidados o desordenados.
- Exige exactamente una sección `[options]` cuando necesita insertar su `Include`.
- Conserva `Include` manuales fuera de los bloques administrados.
- Evita duplicados y es idempotente.
- Escribe mediante temporales en el mismo directorio y renombrado atómico.
- Conserva modo y propietario del archivo original.
- No crea `/etc/pacman.conf` si falta.

## Hooks y scriptlet

- `post_install`: garantiza ambos bloques `Include`.
- `post_upgrade`: repara ambos bloques.
- `pre_remove`: elimina exclusivamente los bloques administrados.
- Hook ALPM `Type = Path`, `Target = etc/pacman.conf`, en `PostTransaction`: vuelve a garantizar la integración después de transacciones que incluyan esa ruta.

El hook no detecta todas las modificaciones manuales arbitrarias ni cambios realizados por scriptlets que no formen parte de la lista de archivos de la transacción.

## Migración desde `cambonos-repo`

El paquete declara `provides`, `conflicts` y `replaces` para `cambonos-repo`. El helper nuevo reconoce también el bloque de repositorios antiguo, por lo que puede migrarlo incluso si el scriptlet anterior no lo ha retirado durante la sustitución del paquete.

Los identificadores `[cambonos]` y `[cambonos-testing]` no cambian: son nombres de repositorio, no nombres de paquete.

## Bootstrap

En instalaciones nuevas, instalar primero `cambonos-keyring` desde el medio local confiable y poblar el keyring de pacman. Después instalar `cambonos-pacman` y habilitar el repositorio remoto. No se debe depender del repositorio remoto para obtener la primera copia de su propia clave de confianza.

## Instalación y comprobación

```bash
sudo pacman -S cambonos-pacman
pacman-conf --repo-list
pacman-conf Color
pacman-conf CheckSpace
pacman-conf VerbosePkgLists
pacman-conf ParallelDownloads
pacman-conf ILoveCandy
```

Verificar también el contenido de `/etc/pacman.d/cambonos.conf` y `/etc/pacman.d/cambonos-options.conf`. En una instalación real, `pacman -Syy` debe descargar y validar las bases de datos firmadas. No deshabilitar la comprobación de firmas para resolver errores de confianza.

## Pruebas de validación

- [ ] Construcción correcta con `makepkg`.
- [ ] El paquete contiene ambos archivos de configuración, helper, hook y scriptlet.
- [ ] Stable apunta al mirror canónico y exige firmas.
- [ ] Testing está comentado por defecto y, al habilitarse, exige firmas.
- [ ] Las opciones diferenciales son exactamente las documentadas.
- [ ] `pacman-conf` devuelve `ParallelDownloads = 3` y reconoce las demás opciones.
- [ ] `post_install` integra opciones y repositorios en sus secciones correctas.
- [ ] `post_upgrade` repara ambos bloques sin duplicarlos.
- [ ] Un `Include` manual existente se conserva y no se adopta.
- [ ] `--remove` elimina únicamente los bloques administrados.
- [ ] Los marcadores antiguos de `cambonos-repo` se migran correctamente.
- [ ] Marcadores incompletos o desordenados provocan error y el archivo permanece byte a byte intacto.
- [ ] Un archivo sin salto de línea final se procesa correctamente.
- [ ] Si `/etc/pacman.conf` falta, el helper falla sin crear una configuración global.
- [ ] Si `/etc/pacman.conf` es un enlace simbólico o no es archivo regular, no lo reemplaza.
- [ ] Se preservan modo y propietario tras la modificación.
- [ ] El hook ALPM se ejecuta tras una transacción que instala/actualiza `pacman.conf`.
- [ ] La desinstalación elimina la integración sin tocar el resto de `pacman.conf`.
- [ ] `pacman -Qkk cambonos-pacman` no detecta alteraciones inesperadas.
