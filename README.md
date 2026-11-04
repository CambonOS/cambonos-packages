# CambonOS Packages

Repositorio de paquetes e infraestructura de construcción y publicación de CambonOS, una distribución basada en Arch Linux rolling release.

Esta primera versión funcional reconstruye los dos canales en cada publicación:

| Rama | Repositorio pacman | Estado predeterminado |
|---|---|---|
| `main` | `stable` (`[cambonos]`) | Habilitado |
| `dev` | `testing` (`[cambonos-testing]`) | Comentado/deshabilitado |

Cada publicación reconstruye todos los paquetes de ambas ramas, firma los paquetes y las bases de datos, verifica los artefactos y despliega un sitio completo en GitHub Pages. No se conservan versiones antiguas dentro de un canal.

## Estructura

```text
cambonos-packages/
├── .github/workflows/package-pipeline.yml
├── packages/
│   ├── cambonos-release/
│   ├── cambonos-fastfetch/
│   └── cambonos-keyring/
├── scripts/
│   ├── cambonos.py
│   └── cambonos_lib/
├── tests/
├── docs/
│   ├── GPG-SETUP.md
│   └── IMPLEMENTATION.md
└── README.md
```

## Preparación obligatoria antes de la primera publicación

1. Sigue [`docs/GPG-SETUP.md`](docs/GPG-SETUP.md) para generar la clave primaria y la subclave de firma.
2. Copia únicamente el material público (`cambonos.gpg`, `cambonos-trusted`, `cambonos-revoked`) a `packages/cambonos-keyring/files/`.
3. Añade `CAMBONOS_SIGNING_KEY` y `CAMBONOS_SIGNING_PASSPHRASE` como secretos del entorno GitHub `package-signing`.
4. Añade `CAMBONOS_SIGNING_FINGERPRINT` como variable de ese entorno. Debe ser el fingerprint de la subclave privada de firma.
5. Configura GitHub Pages con origen **GitHub Actions**.
6. Establece temporalmente la variable de repositorio `CAMBONOS_BOOTSTRAP=true` para la primera publicación. Tras comprobar el manifiesto publicado, cámbiala a `false`.

No ejecutes el pipeline antes de provisionar el material GPG: la validación de `cambonos-keyring` rechazará los archivos placeholder vacíos.

La ISO de CambonOS debe instalar `cambonos-keyring` desde el medio local después de inicializar pacman-key y antes de utilizar el repositorio remoto. Ese bootstrap está fuera del alcance de este repositorio.

## Herramientas locales

Para validar y probar el código:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/cambonos.py --help
```

La validación estática requiere Python 3.10+, Bash y GPG. La comparación de versiones utiliza `vercmp` de pacman; si no está instalado en el host, el gestor lo ejecuta dentro de la imagen Docker fijada.

Validar localmente un snapshot:

```bash
python3 scripts/cambonos.py validate \
  --source-root . \
  --channel testing \
  --branch dev
```

La validación local no consulta automáticamente Pages. Para comparar con una publicación anterior:

```bash
python3 scripts/cambonos.py validate \
  --source-root . \
  --channel testing \
  --branch dev \
  --previous-manifest ./manifest.json \
  --previous-manifest-signature ./manifest.json.sig \
  --keyring-public-key ./packages/cambonos-keyring/files/cambonos.gpg \
  --keyring-trusted ./packages/cambonos-keyring/files/cambonos-trusted
```

Construir un canal local requiere Docker:

```bash
python3 scripts/cambonos.py build \
  --source-root . \
  --channel testing \
  --branch dev \
  --commit "$(git rev-parse HEAD)" \
  --output ./build-testing
```

El comando construye cada paquete en un contenedor Arch Linux desechable. El contenedor actualiza los repositorios rolling, instala `makedepends` y, cuando existe `check()`, instala `checkdepends`. No instala automáticamente `depends`.

La firma y el ensamblado del sitio se realizan en el job protegido de GitHub Actions; no se recomienda exportar la clave privada a un equipo de construcción local.

## Política de versiones

Cualquier cambio en los archivos de un paquete, incluido `PKGBUILD`, scripts `.install`, parches y payloads de `files/`, debe incrementar `pkgrel` o `pkgver`.

El pipeline compara el hash del contenido fuente y la versión del mismo paquete en el canal correspondiente:
- Cambia el contenido y no cambia la versión: error.
- Cambia el contenido y aumenta la versión: permitido.
- La versión retrocede: error.
- Un paquete nuevo: permitido.
- Un paquete eliminado de una rama: desaparece únicamente del canal de esa rama.
- Si el binario reconstruido cambia de SHA256 manteniendo la misma versión, la firma/publicación se bloquea y requiere incrementar `pkgrel` o `pkgver`.

La comparación de versiones utiliza `vercmp`, no ordenación textual. Para estabilizar las reconstrucciones, `SOURCE_DATE_EPOCH` se fija al último commit Git que modificó el directorio de cada paquete. El hash binario se compara también con el manifiesto anterior para impedir que el rolling de Arch sustituya silenciosamente un paquete con la misma versión.

`stable` y `testing` se comparan de forma independiente. Es válido que tengan versiones diferentes.

## Dependencias

- `depends`: dependencias de ejecución declaradas en el paquete; no se instalan automáticamente durante la construcción.
- `makedepends`: se instalan en el contenedor de construcción.
- `checkdepends`: se instalan cuando el paquete define `check()` y se ejecutan las pruebas.
- Dependencias internas de construcción se ordenan topológicamente y se instalan desde los artefactos temporales ya construidos.

Cada paquete se construye en su propio contenedor, por lo que no comparte las dependencias instaladas por otro paquete.

## Repositorios pacman

El sitio contiene:

```text
stable/x86_64/
testing/x86_64/
metadata/manifest.json
metadata/manifest.json.sig
index.html
```

El manifiesto global también se firma. En las ejecuciones posteriores, `validate` verifica esa firma con la clave pública del paquete `cambonos-keyring` antes de utilizar el manifiesto como referencia de versionado.

Cada repositorio se genera desde cero. Los nombres de base de datos son:
- `stable`: `cambonos.db` / `cambonos.files`.
- `testing`: `cambonos-testing.db` / `cambonos-testing.files`.

Los paquetes y las bases de datos se firman con la subclave configurada. `repo-add --include-sigs` incorpora las firmas de paquetes a la base de datos. Los alias `.db` y `.files` se materializan como archivos regulares y reciben una firma válida para sus bytes.

Configuración de ejemplo en `pacman.conf`:

```ini
#[cambonos-testing]
#SigLevel = Required
#Server = https://<dominio>/testing/$arch

[cambonos]
SigLevel = Required
Server = https://<dominio>/stable/$arch
```

`SigLevel = Required` exige firmas de paquetes y de la base de datos. El nombre del repositorio pacman debe coincidir con el nombre de la base de datos.

## GitHub Actions

El workflow `.github/workflows/package-pipeline.yml` se ejecuta únicamente con `push` a `dev` o `main`. No se ejecuta en Pull Requests ni tiene disparador manual.

Jobs:
1. `validate`: fija los SHA de `dev` y `main`, ejecuta pruebas y valida los dos snapshots contra el manifiesto anterior de Pages.
2. `build`: matriz `testing`/`stable`, construye todos los paquetes sin secretos GPG.
3. `signing`: valida artefactos, importa la subclave, firma paquetes y bases de datos, crea la portada, genera índices HTML navegables para los directorios del mirror y verifica el sitio. La portada manual se conserva; los índices secundarios se regeneran en cada publicación.
4. `publish`: despliega el sitio completo mediante GitHub Pages.

La imagen oficial `archlinux:base-devel` está fijada por digest para la plataforma `linux/amd64`. El sistema instalado dentro de cada contenedor se actualiza desde los repositorios rolling actuales de Arch; por tanto, el digest fija la imagen inicial, no las versiones de todos los paquetes de construcción.

El workflow usa una única concurrencia global y no cancela una publicación activa. Si una validación, construcción, firma o verificación falla, `publish` no se ejecuta y la publicación anterior permanece.

## Configuración opcional de Actions

Variables de repositorio:
- `CAMBONOS_BOOTSTRAP`: `true` únicamente durante la primera publicación; después `false`.
- `CAMBONOS_PAGES_URL`: URL base del sitio si no coincide con `https://<owner>.github.io/<repo>`.

Secretos del entorno `package-signing`:
- `CAMBONOS_SIGNING_KEY`: exportación ASCII-armored de la subclave privada de firma.
- `CAMBONOS_SIGNING_PASSPHRASE`: contraseña de esa subclave.

Variable del entorno `package-signing`:
- `CAMBONOS_SIGNING_FINGERPRINT`: fingerprint completo de la subclave de firma.

Consulta [`docs/GPG-SETUP.md`](docs/GPG-SETUP.md) para el procedimiento completo.
