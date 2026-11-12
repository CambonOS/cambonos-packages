# Despliegue automatizado

Este documento describe los workflows que validan, construyen, firman y publican los
paquetes CambonOS. La planificación y la reutilización de artefactos se explican en
[BUILD.md](BUILD.md); la política de versiones está en [VERSIONING.md](VERSIONING.md).

## Canales

| Rama | Canal | Uso |
|---|---|---|
| `dev` | `testing` | Validación de cambios antes de su promoción. |
| `main` | `stable` | Distribución estable. |

Cada canal se valida y construye desde su propio snapshot. Al comenzar la ejecución, el
workflow fija los commits de ambas ramas y utiliza esos mismos commits durante la
validación y la construcción.

Los paquetes `cambonos-installer` y `cambonos-mkiso` proceden de repositorios externos.
Sus commits también se resuelven y fijan al inicio. Para `testing` se utiliza `dev` y,
si esa rama no existe en el repositorio externo, se utiliza `main`; `stable` utiliza
`main`. Las fuentes se incorporan temporalmente al árbol de paquetes y sus commits
quedan registrados en el manifiesto de build.

## Workflows y triggers

La automatización se divide en dos workflows:

- `.github/workflows/package-build.yml`: valida los snapshots y construye ambos canales.
- `.github/workflows/package-publish.yml`: comprueba la procedencia de la ejecución de
  build, firma los artefactos y despliega el sitio.

`package-build.yml` se inicia mediante:

- `push` a `dev` o `main`.
- `repository_dispatch` de tipo `external-package-updated`, utilizado para notificar
  cambios en los repositorios externos.

No existe un trigger `workflow_dispatch`: la ejecución manual desde la interfaz de
GitHub Actions no forma parte de la configuración actual. El evento
`repository_dispatch` requiere una notificación externa con el payload que valida
`scripts/validate_external_dispatch.py`.

`package-publish.yml` escucha la finalización de `CambonOS package build` mediante
`workflow_run`. Solo continúa si el build terminó correctamente y el evento de origen
cumple las condiciones del workflow: un `push` de `dev` o `main`, o un
`repository_dispatch` admitido desde `main`. Una notificación externa no equivale, por
sí sola, a una publicación garantizada.

## Construcción: `package-build.yml`

El workflow contiene dos jobs:

### `validate`

- Ejecuta `python -m unittest discover -s tests -v`.
- Obtiene los commits actuales de `dev` y `main` y crea worktrees separados para validar
  snapshots inmutables.
- Valida el payload de `repository_dispatch`, cuando corresponde, y comprueba que el
  commit notificado pertenece al historial de la rama externa.
- Resuelve y fija los commits de `cambonos-installer` y `cambonos-mkiso`.
- Incorpora temporalmente esas fuentes a cada snapshot.
- Comprueba que `cambonos.gpg`, `cambonos-trusted` y `cambonos-revoked` son idénticos en
  ambos canales.
- Recupera el manifiesto publicado y su firma. Si no existe, solo admite la primera
  publicación cuando `CAMBONOS_BOOTSTRAP=true`.
- Valida los paquetes y la política de versiones de `testing` y `stable` por separado.

La validación estática inspecciona los `PKGBUILD`, sus metadatos, dependencias, archivos
y rutas sin ejecutar las recetas en el runner. Las pruebas automatizadas se ejecutan
antes de validar los snapshots.

### `build`

Utiliza una matriz con dos ejecuciones independientes:

| Canal | Rama | Snapshot |
|---|---|---|
| `testing` | `dev` | Commit fijado por `validate`. |
| `stable` | `main` | Commit fijado por `validate`. |

Cada ejecución prepara las fuentes inmutables y construye los paquetes en contenedores
Arch Linux desechables. Las dependencias de construcción (`makedepends` y, si existe
`check()`, `checkdepends`) se instalan para cada paquete; las dependencias de ejecución
no se instalan automáticamente como parte de la construcción.

Antes de construir, intenta recuperar los artefactos de la publicación anterior para
aplicar compilación selectiva. El comportamiento exacto y sus garantías se describen en
[BUILD.md](BUILD.md). Si la recuperación no está disponible o falla, el builder realiza
una compilación completa segura. Los artefactos de ambos canales se publican como
`build-testing` y `build-stable`, junto con sus manifiestos e informes.

La construcción no recibe claves privadas de firma.

## Firma y publicación: `package-publish.yml`

El workflow de publicación contiene dos jobs:

### `sign`

- Comprueba que la ejecución que lo ha activado procede del repositorio, rama, evento y
  workflow esperados.
- Descarga el contexto inmutable y los artefactos de ambos canales.
- Rechaza builds obsoletos o cuyos commits no coincidan con los snapshots actuales.
- Comprueba que el mirror no haya cambiado desde que comenzó el build.
- Verifica los manifiestos de compilación y los artefactos.
- Firma los paquetes nuevos, conserva las firmas de los paquetes reutilizados y firma
  las bases de datos de Pacman y el manifiesto global.
- Ensambla el sitio completo que se publicará.

Este es el único job que utiliza el entorno protegido `package-signing` y los secretos
de firma. No ejecuta `PKGBUILD` ni scripts de instalación.

### `deploy`

Antes de desplegar, vuelve a comprobar los snapshots de las ramas y que el manifiesto y
su firma publicados no hayan cambiado durante la fase de firma. Si las comprobaciones
pasan, publica el sitio ensamblado mediante GitHub Pages.

La publicación no debe sobrescribir una ejecución más reciente ni un estado del mirror
distinto del que se verificó al comenzar el proceso.

## Configuración de GitHub

Configura el entorno protegido `package-signing` y limita su uso a las ramas `dev` y
`main`.

**Secretos del entorno:**

- `CAMBONOS_SIGNING_KEY`: subclave privada operativa exportada para firma.
- `CAMBONOS_SIGNING_PASSPHRASE`: contraseña de la clave exportada.

**Variable del entorno:**

- `CAMBONOS_SIGNING_FINGERPRINT`: fingerprint completo de la subclave de firma.

**Variables del repositorio:**

- `CAMBONOS_PAGES_URL`: URL base del sitio publicado. Es opcional si se utiliza la URL
  predeterminada de GitHub Pages.
- `CAMBONOS_BOOTSTRAP`: debe ser `true` únicamente para autorizar la primera publicación
  cuando todavía no existe un manifiesto anterior firmado. Después de verificar esa
  publicación, debe establecerse en `false`.

Configura GitHub Pages para publicar mediante GitHub Actions. La clave primaria privada
de GPG debe permanecer fuera de GitHub y de sus runners. Consulta
[GPG-SETUP.md](GPG-SETUP.md) para preparar las claves y el entorno.

## Manifiestos, versiones y confianza

El sitio incluye `metadata/manifest.json` y su firma detached. El manifiesto registra
los commits de origen, las versiones de los paquetes y los hashes de los artefactos. La
ejecución siguiente verifica la firma antes de utilizarlo como referencia.

La política CPV se aplica independientemente a cada canal. Los cambios funcionales
incrementan `pkgver`; los cambios exclusivamente de empaquetado incrementan `pkgrel`. No
se permiten retrocesos ni sustituir un artefacto publicado por otro binario con la misma
identidad. Consulta [VERSIONING.md](VERSIONING.md).

Los tres archivos públicos de `cambonos-keyring` deben ser idénticos en `dev` y `main`.
Esto mantiene la misma raíz de confianza en ambos canales.

## Requisitos y límites

La construcción necesita Docker y acceso a los repositorios rolling de Arch. La firma
necesita GPG y los secretos del entorno protegido. La imagen `archlinux:base-devel` está
fijada por digest, pero sus repositorios se actualizan; por tanto, el proceso no
garantiza reproducibilidad binaria entre fechas distintas.

Los tests y la validación estática no sustituyen la instalación y comprobación funcional
en un sistema Arch real. Antes de fusionar `dev` en `main`, deben estar verificadas las
funciones incluidas en el alcance soportado de esa versión. El estado se registra en
[PACKAGE-TEST-CHECKLIST.md](PACKAGE-TEST-CHECKLIST.md).
