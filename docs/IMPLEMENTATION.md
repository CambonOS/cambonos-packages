# CambonOS Packages — arquitectura de implementación

## Resumen

El repositorio utiliza un pipeline modular de validación, construcción, firma y publicación. Cada push a `dev` o `main` fija los commits de ambas ramas y procesa los dos canales a partir de esos snapshots Git inmutables.

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

- `SOURCE_DATE_EPOCH` se deriva del último commit que modificó cada directorio de paquete, para normalizar marcas temporales entre reconstrucciones del mismo contenido.
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

El workflow se activa exclusivamente con `push` a `dev` y `main`. No hay workflow de PR ni ejecución manual.

Los cuatro jobs son:
1. `validate`
2. `build` (matriz `testing` y `stable`)
3. `signing`
4. `publish`

El despliegue utiliza `actions/upload-pages-artifact` y `actions/deploy-pages`. Se publica un único artefacto de sitio completo. Si falla cualquier fase, el job de despliegue no se ejecuta.

## Paquetes de integración del sistema

### `cambonos-keyring`

Añade el certificado público y la información de confianza de pacman en:

```text
/usr/share/pacman/keyrings/cambonos.gpg
/usr/share/pacman/keyrings/cambonos-trusted
/usr/share/pacman/keyrings/cambonos-revoked
```

El paquete instala el material público en `/usr/share/pacman/keyrings/` y ejecuta `pacman-key --populate cambonos` cuando el keyring local ya está inicializado. El repositorio contiene el certificado público y los datos de confianza; nunca debe contener claves privadas.

### `cambonos-repo`

Distribuye `/etc/pacman.d/cambonos.conf` con el mirror canónico `https://mirror.cambonos.org`, habilita stable y deja testing comentado. Declara `cambonos-keyring` como dependencia y configura `SigLevel = Required TrustedOnly` para ambos canales. El paquete es opcional: cada canal puede incluirlo o no, sin exigir que esté presente en el otro canal. El único paquete obligatorio en ambos canales es `cambonos-keyring`, necesario para la verificación de firmas.

El paquete integra el fichero mediante un bloque marcado al final de `/etc/pacman.conf`. Su script `.install`:
- `post_install()`: añade el bloque administrado si no existe.
- `post_upgrade()`: comprueba y repara el bloque.
- `pre_remove()`: elimina exclusivamente el bloque administrado.

El helper realiza escrituras atómicas, evita duplicados y conserva cualquier `Include` manual preexistente. Si encuentra marcadores incompletos, falla de forma conservadora y no reescribe el archivo.

El hook `cambonos-repo-pacman-conf.hook` usa un disparador `Type = Path` sobre `etc/pacman.conf`, para operaciones `Install` y `Upgrade`. Se ejecuta después de transacciones que incluyen ese archivo y llama al mismo helper. ALPM también utiliza la ruta original como objetivo cuando el archivo se instala como `.pacnew`. El hook no detecta modificaciones manuales arbitrarias ni cambios realizados por scriptlets que no formen parte de la lista de archivos de la transacción.

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
