# Clave GPG de CambonOS y paquete cambonos-keyring

Esta guía crea una clave primaria de certificación que se mantiene fuera de GitHub y una
subclave de firma que se utiliza en GitHub Actions.

> **Importante:** ejecuta la generación en un equipo de confianza que no sea el runner de GitHub. Conserva la clave primaria privada y su certificado de revocación fuera del repositorio. Nunca subas claves privadas al repositorio ni a GitHub Pages.

## 1. Crear la clave primaria y la subclave de firma

Instala GnuPG y prepara un directorio GPG separado. El ejemplo utiliza Ed25519:

```bash
sudo pacman -S --needed gnupg

export GNUPGHOME="$HOME/.gnupg-cambonos"
install -d -m 700 "$GNUPGHOME"

gpg --quick-generate-key \
  "CambonOS Package Signing" \
  ed25519 cert 2y
```

GnuPG solicitará una contraseña. Utiliza una contraseña fuerte y guárdala en un gestor
de contraseñas. Esta protege la clave primaria y la subclave que se añadirá a
continuación.

Consulta las huellas:

```bash
gpg --list-secret-keys --keyid-format long --with-subkey-fingerprint
```

Copia el fingerprint completo de la clave primaria y añádelo como subclave de firma:

```bash
PRIMARY_FPR="7B6BE3ABE5E7636F9019690C98C362C2C2E22906"

gpg --quick-add-key "$PRIMARY_FPR" ed25519 sign 2y

gpg --list-secret-keys --keyid-format long --with-subkey-fingerprint
```

Identifica y copia el fingerprint completo de la subclave que aparece bajo `ssb` y tiene
capacidad `s`. No confundas el fingerprint de la clave primaria con el de la subclave.

Guarda una copia segura de:
- La clave primaria privada.
- El certificado de revocación que GnuPG crea en `$GNUPGHOME/openpgp-revocs.d/`.
- La contraseña.
- Los fingerprints de la clave primaria y de la subclave.

La clave primaria se utilizará para administrar y certificar la identidad. No se
exportará a GitHub Actions.

## 2. Exportar el material público para cambonos-keyring

Desde el mismo `GNUPGHOME`, define los fingerprints:

```bash
PRIMARY_FPR="7B6BE3ABE5E7636F9019690C98C362C2C2E22906"
SIGNING_SUBKEY_FPR="3D25435E6225B152D1C67935A317EFDA327F34A2"

KEYRING_DIR="packages/cambonos-keyring/files"
```

Exporta el certificado público completo:

```bash
gpg --export "$PRIMARY_FPR" > "$KEYRING_DIR/cambonos.gpg"
```

Marca la clave primaria como de confianza ultimate en el almacén GPG de trabajo y
exporta el fichero de ownertrust:

```bash
printf '%s:6:\n' "$PRIMARY_FPR" | gpg --import-ownertrust
gpg --export-ownertrust > "$KEYRING_DIR/cambonos-trusted"
```

Crea inicialmente el fichero de revocaciones vacío:

```bash
: > "$KEYRING_DIR/cambonos-revoked"
```

Comprueba que los archivos se han generado:

```bash
gpg --show-keys --with-subkey-fingerprint "$KEYRING_DIR/cambonos.gpg"
grep -i "^${PRIMARY_FPR}:6:" "$KEYRING_DIR/cambonos-trusted"

ls -l "$KEYRING_DIR"/cambonos*
```

El archivo `cambonos.gpg` debe contener la clave primaria pública y la subclave pública
de firma. `cambonos-trusted` debe contener la línea de ownertrust de la clave primaria
con valor `6`. `cambonos-revoked` puede permanecer vacío inicialmente.

Estos tres archivos son material público y **sí deben incorporarse al repositorio Git**.

## 3. Exportar únicamente la subclave privada de firma

Esta es la operación sensible. Exporta el material secreto seleccionando el fingerprint
de la subclave y usando `!` para seleccionar exactamente esa clave:

```bash
umask 077
gpg --armor --export-secret-subkeys "${SIGNING_SUBKEY_FPR}!" \
  > "$HOME/cambonos-signing-subkey.asc"
```

GnuPG exporta la subclave privada seleccionada junto con el stub de la clave primaria
necesario para identificarla. No exporta la clave primaria privada.

Comprueba el fichero sin mostrar su contenido:

```bash
test -s "$HOME/cambonos-signing-subkey.asc"
chmod 600 "$HOME/cambonos-signing-subkey.asc"
```

No añadas este fichero a Git. No lo guardes en `packages/cambonos-keyring/files/`.
Mantén una copia segura de respaldo.

## 4. Crear el entorno de GitHub

En el repositorio `CambonOS/cambonos-packages`:

1. Abre **Settings → Environments**.
2. Crea el entorno `package-signing`.
3. Configura sus reglas de despliegue para permitir las ramas `dev` y `main`.
4. En **Environment secrets**, añade:

| Nombre | Valor |
|---|---|
| `CAMBONOS_SIGNING_KEY` | Contenido completo de `cambonos-signing-subkey.asc` |
| `CAMBONOS_SIGNING_PASSPHRASE` | Contraseña de la subclave privada |

5. En **Environment variables**, añade:

| Nombre | Valor |
|---|---|
| `CAMBONOS_SIGNING_FINGERPRINT` | Fingerprint completo de la subclave de firma, no el de la clave primaria |

No guardes el fingerprint como secreto: es información pública.

El job `sign` de `package-publish.yml` es el único que consume estos secretos. Los jobs
de validación y construcción no reciben acceso a ellos.

## 5. Configurar la primera publicación

En **Settings → Secrets and variables → Actions → Variables**, crea:

| Variable | Valor |
|---|---|
| `CAMBONOS_BOOTSTRAP` | `true` |

Opcionalmente, si utilizas un dominio personalizado o una URL distinta de GitHub Pages,
define `CAMBONOS_PAGES_URL` con la URL base del sitio, sin barra final.

Asegúrate de que GitHub Pages está configurado para publicar mediante **GitHub
Actions**.

Antes de construir, el workflow compara byte a byte los tres archivos públicos del
keyring entre los snapshots de `dev` y `main`. Si difieren, la validación falla. La
clave pública debe estar disponible en ambas ramas y el fingerprint de la subclave
configurado en GitHub debe corresponder a una subclave de firma presente en ese
certificado.

La variable `CAMBONOS_BOOTSTRAP=true` permite únicamente la primera publicación cuando
todavía no existe `metadata/manifest.json`. Después de que la primera publicación
termine correctamente y compruebes que el manifiesto está accesible, cambia la variable
a:

```text
CAMBONOS_BOOTSTRAP=false
```

No mantengas el bootstrap habilitado de forma permanente. Si una publicación posterior
no puede recuperar el manifiesto, el pipeline debe detenerse.

## 6. Incorporar cambonos-keyring al repositorio

Los archivos públicos generados en el paso 2 deben estar en:

```text
packages/cambonos-keyring/
├── PKGBUILD
├── cambonos-keyring.install
└── files/
    ├── cambonos.gpg
    ├── cambonos-trusted
    └── cambonos-revoked
```

Revisa el estado antes de hacer commit:

```bash
git status --short
git diff -- packages/cambonos-keyring
```

Solo deben aparecer los archivos públicos. Si aparece `cambonos-signing-subkey.asc`,
detente y elimínalo del árbol Git antes de continuar.

El paquete instala los tres archivos en `/usr/share/pacman/keyrings/` y ejecuta
`pacman-key --populate cambonos` después de instalarse o actualizarse, siempre que el
keyring de pacman ya esté inicializado.

La ISO debe inicializar `pacman-key` e instalar `cambonos-keyring` desde el medio local
antes de habilitar la confianza obligatoria del repositorio remoto. Después debe
instalar `cambonos-pacman`, que depende del keyring y configura los Include
administrados de opciones y repositorios en `/etc/pacman.conf`. Ese bootstrap pertenece
al proceso de instalación de la ISO, no a este pipeline.

## 7. Probar y publicar

Una vez incorporado el material público y configurados los secretos:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/cambonos.py validate \
  --source-root . \
  --channel testing \
  --branch dev \
  --allow-bootstrap
```

La validación del paquete keyring debe pasar únicamente si el certificado público y el
ownertrust son válidos. Las publicaciones posteriores firman también
`metadata/manifest.json`; el siguiente pipeline verifica su firma antes de confiar en
sus datos de versión.

Cada rama mantiene su propio desarrollo y su propio snapshot de paquetes: no es
necesario fusionar `dev` en `main` ni mantener sincronizados sus paquetes. El pipeline
valida cada canal contra su propio manifiesto anterior, pero aplica una regla común de
confianza: compara byte a byte `cambonos.gpg`, `cambonos-trusted` y `cambonos-revoked`
entre los snapshots de `dev` y `main` antes de continuar. Por tanto, ambos canales deben
contener exactamente el mismo material público de keyring, aunque los demás paquetes y
sus versiones puedan diferir. Un push reconstruye los dos canales a partir de los
snapshots independientes de `dev` y `main`.

Cuando termine la primera publicación:
- Comprueba `stable/` y `testing/`.
- Comprueba `metadata/manifest.json`.
- Comprueba las firmas de la base de datos y de los paquetes.
- Cambia `CAMBONOS_BOOTSTRAP` a `false`.

## 8. Renovación y revocación

No reemplaces la clave de firma de forma improvisada. Los equipos ya instalados confían
en la clave pública distribuida por `cambonos-keyring`. Una rotación requiere una
transición planificada que permita a los clientes confiar en la nueva clave antes de
exigir firmas de ella. El procedimiento operativo de rotación y recuperación todavía
debe ensayarse con clientes de prueba; no debe considerarse validado solo porque el
pipeline acepte el nuevo material.

Conserva la clave primaria y el certificado de revocación en almacenamiento seguro. Si
la clave o subclave se compromete, detén las publicaciones y planifica la revocación y
distribución de un keyring actualizado. El fichero `cambonos-revoked` forma parte del
formato de pacman-key; sigue el procedimiento de la documentación de Arch para añadir
revocaciones. Ante compromiso de la clave primaria, asume que algunos clientes
necesitarán una intervención manual y una nueva raíz distribuida por un canal
autenticado independiente.
