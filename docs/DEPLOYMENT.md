# Despliegue automatizado de paquetes

El workflow `.github/workflows/package-pipeline.yml` construye y publica los canales `testing` y `stable` en GitHub Pages.

## Flujo de publicación

El workflow se ejecuta al recibir cambios en `dev` o `main`, o manualmente desde GitHub Actions.

1. **Validación:** fija los commits de `dev` y `main`, prepara las fuentes externas, ejecuta los tests y valida los dos conjuntos de paquetes y su política de versiones.
2. **Construcción:** genera todos los paquetes de `testing` y `stable` en contenedores Arch Linux independientes. Los dos canales se construyen desde sus respectivas ramas.
3. **Firma y ensamblado:** verifica los artefactos, firma los paquetes y las bases de datos de ambos canales, y genera el contenido completo del mirror.
4. **Publicación:** despliega el sitio generado en GitHub Pages. Si una fase anterior falla, no se ejecuta la publicación.

La fase de construcción no recibe claves privadas. Los secretos de firma solo están disponibles en el entorno protegido `package-signing`.

## Ramas y canales

| Rama | Canal | Finalidad |
|---|---|---|
| `dev` | `testing` | Pruebas y validación previa a stable. |
| `main` | `stable` | Distribución estable. |

Cada canal se valida y construye de forma independiente. Los commits de origen se fijan al comienzo de la ejecución para que validación y construcción utilicen exactamente las mismas fuentes.

Los paquetes `cambonos-installer` y `cambonos-mkiso` proceden de repositorios externos. El workflow fija sus commits y los incorpora temporalmente al árbol de construcción; no mantiene copias de sus fuentes en este repositorio.

## Requisitos de GitHub Actions

Configura el entorno protegido `package-signing` y limita su uso a las ramas `dev` y `main`.

**Secretos del entorno:**

- `CAMBONOS_SIGNING_KEY`: subclave privada operativa exportada para firma.
- `CAMBONOS_SIGNING_PASSPHRASE`: contraseña de la clave exportada.

**Variables del entorno:**

- `CAMBONOS_SIGNING_FINGERPRINT`: fingerprint de la subclave de firma.

**Variables del repositorio:**

- `CAMBONOS_PAGES_URL`: URL base del sitio publicado. Es opcional si se utiliza la URL predeterminada de GitHub Pages.
- `CAMBONOS_BOOTSTRAP`: debe ser `true` únicamente para la primera publicación, cuando todavía no existe un manifiesto anterior firmado. Tras verificar la primera publicación, establecerlo en `false`.

Configura GitHub Pages para desplegar mediante GitHub Actions.

La clave primaria de GPG debe permanecer fuera de GitHub Actions. La preparación y custodia de las claves se describe en [Gestión de claves GPG](GPG-SETUP.md).

## Validación y construcción

La fase `validate` ejecuta la suite de tests y valida los snapshots de ambas ramas antes de construir. La validación estática inspecciona los `PKGBUILD` sin ejecutarlos en el runner: comprueba metadatos, dependencias internas, rutas de origen y destino, archivos requeridos, sintaxis disponible y coherencia básica del contenido. La construcción real ejecuta `makepkg` dentro de contenedores Arch desechables.

Cada paquete se construye en su propio contenedor. Se instalan `makedepends` y, cuando el paquete define `check()`, sus `checkdepends`. Las dependencias internas de construcción se ordenan según su relación de dependencias. Las dependencias de ejecución no se instalan automáticamente durante la construcción.

Los dos repositorios externos se fijan a commits concretos al comienzo de la ejecución. Para `testing` se utiliza `dev` si existe y, en caso contrario, `main`; `stable` utiliza `main`. El workflow comprueba el origen y el commit antes de incorporar temporalmente esas fuentes al árbol de construcción.

## Manifiestos y artefactos

El sitio publicado incluye `metadata/manifest.json`. El manifiesto registra los commits de origen, versiones de paquetes y hashes de fuentes y artefactos. El pipeline recupera el manifiesto anterior y verifica su firma antes de utilizarlo como referencia.

La política de versiones se aplica de forma independiente a cada canal:

- Si cambia el comportamiento funcional del paquete, debe incrementarse `pkgver` según CPV (MAJOR, MINOR o PATCH). `pkgrel` se incrementa únicamente para cambios de empaquetado que no alteran el comportamiento funcional.
- No se permiten retrocesos de versión.
- La incorporación o retirada de paquetes está permitida.
- Una reconstrucción puede producir un binario distinto aunque la fuente no haya cambiado, debido a la naturaleza rolling de Arch. El hash del paquete identifica el artefacto concreto y no sustituye la política de versión.

El material público de `cambonos-keyring` debe ser idéntico entre `dev` y `main`: `cambonos.gpg`, `cambonos-trusted` y `cambonos-revoked`. Esta igualdad permite mantener una única raíz de confianza en ambos canales.

## Firma y mirror

El job `signing` es el único que recibe los secretos de firma. Verifica los artefactos construidos, firma cada paquete y las bases de datos de Pacman, genera sus índices y firma el manifiesto global. No ejecuta `PKGBUILD` ni scripts de instalación.

El job `publish` recibe el sitio completo ya ensamblado y lo despliega en GitHub Pages. No recibe la clave privada. El mirror publica ambos canales y sus metadatos de integridad y firma.

La firma acredita la procedencia criptográfica del artefacto, no que el código sea benigno. La revisión de cambios y la protección de ramas siguen siendo necesarias.

## Versionado de paquetes

Cuando cambian las entradas de construcción, el pipeline exige un incremento de versión. La clasificación entre MAJOR, MINOR y PATCH corresponde al mantenedor conforme a [VERSIONING.md](VERSIONING.md); los cambios exclusivamente de empaquetado incrementan `pkgrel`. La automatización comprueba la forma de la versión, su orden monotónico y el reinicio de `pkgrel` al cambiar `pkgver`, pero no deduce la naturaleza funcional del diff. `testing` y `stable` aplican esta política de forma independiente.

Los manifiestos publicados registran los commits de origen, versiones y hashes de los paquetes. El manifiesto anterior se verifica criptográficamente antes de utilizarse como referencia para una publicación posterior.

## Ejecución manual

La ejecución manual permite reconstruir y publicar ambos canales, por ejemplo cuando cambian los repositorios externos aunque no haya habido un commit nuevo en este repositorio.

Antes de habilitar una publicación inicial, comprueba que las claves públicas están incorporadas en `cambonos-keyring` y que los secretos y variables del entorno están configurados correctamente.

## Requisitos y límites operativos

La construcción requiere Docker y acceso a los repositorios rolling de Arch. La firma requiere GPG y los secretos del entorno protegido. El pipeline usa una imagen `archlinux:base-devel` fijada por digest, pero actualiza el entorno de construcción desde los repositorios rolling; por ello no garantiza reproducibilidad binaria entre fechas distintas.

Los tests unitarios y la validación estática detectan defectos automatizables, pero no sustituyen una instalación y comprobación funcional en un sistema Arch real. La aceptación funcional se registra en la [checklist funcional](PACKAGE-TEST-CHECKLIST.md): antes del merge de `dev` a `main` deben estar verificadas todas las funciones incluidas en el alcance soportado de esa versión. Las pruebas excluidas del alcance por limitaciones documentadas y expresamente aceptadas pueden permanecer pendientes, pero nunca deben presentarse como verificadas.
