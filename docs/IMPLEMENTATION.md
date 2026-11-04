# CambonOS Packages — cambios de la primera versión funcional

## Resumen

Esta versión sustituye el flujo local incremental anterior por un pipeline de publicación completo y modular. Cada push a `dev` o `main` reconstruye ambos canales a partir de snapshots Git inmutables.

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

El pipeline recupera el manifiesto anterior desde GitHub Pages. Para cada paquete y canal:
- Cambio de contenido sin aumento de versión: error.
- Aumento de versión: permitido.
- Retroceso de versión según `vercmp`: error.
- Paquete nuevo o eliminado: permitido.

`stable` y `testing` se comparan de manera independiente.

### 5. Firma y seguridad

- `SOURCE_DATE_EPOCH` se deriva del último commit que modificó cada directorio de paquete, para normalizar marcas temporales entre reconstrucciones del mismo contenido.
- Si el SHA256 del binario cambia sin cambiar la versión respecto al manifiesto anterior, la publicación se bloquea y exige incrementar `pkgrel`/`pkgver`. Esto también detecta cambios de salida provocados por el entorno rolling de Arch.
- El job `build` no recibe secretos de firma.
- El job `signing` es el único que importa la subclave privada.
- El job `signing` no ejecuta PKGBUILD ni scripts de instalación.
- Se verifica que el fingerprint secreto coincide con la subclave pública incluida en ambos paquetes `cambonos-keyring`.
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

Distribuye `/etc/pacman.d/cambonos.conf` con el mirror canónico `https://mirror.cambonos.org`, habilita stable y deja testing comentado. Declara `cambonos-keyring` como dependencia y configura `SigLevel = Required TrustedOnly` para ambos canales. El paquete forma parte de `REQUIRED_PACKAGES`, por lo que la validación exige su presencia tanto en el snapshot `dev`/testing como en `main`/stable.

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

## Comprobaciones realizadas sobre esta entrega

- Compilación sintáctica de todos los módulos Python.
- Pruebas unitarias del parser, mapeo de canales, hashes, versionado y orden de dependencias.
- Validación estática de los paquetes preexistentes `cambonos-release` y `cambonos-fastfetch`.
- Validación del nuevo paquete keyring: se espera que falle hasta que se añada el material público GPG real.

## Limitaciones y pasos previos al primer despliegue

Esta entrega es la primera implementación funcional del flujo, pero no puede realizar una publicación real desde el archivo por sí solo:
1. Provisionar la clave siguiendo `GPG-SETUP.md`.
2. Configurar secretos y variables de GitHub.
3. Configurar GitHub Pages con GitHub Actions.
4. Confirmar que el paquete keyring se incorpora tanto a `dev` como a `main`.
5. Ejecutar la primera publicación con `CAMBONOS_BOOTSTRAP=true`.

La compilación en contenedores Arch y la generación real de bases de datos requieren Docker y herramientas Arch. No se afirma que esas operaciones se hayan ejecutado en este entorno de trabajo.
