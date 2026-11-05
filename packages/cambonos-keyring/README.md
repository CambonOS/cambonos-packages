# cambonos-keyring

Material público de confianza utilizado por pacman para verificar paquetes y bases de datos de los repositorios CambonOS.

## Responsabilidad

Este paquete distribuye el certificado público CambonOS y los ficheros de confianza/revocación reconocidos por `pacman-key`. No contiene claves privadas.

## Archivos instalados

| Ruta | Función |
|---|---|
| `/usr/share/pacman/keyrings/cambonos.gpg` | Certificado público. |
| `/usr/share/pacman/keyrings/cambonos-trusted` | Datos de confianza de GnuPG. |
| `/usr/share/pacman/keyrings/cambonos-revoked` | Certificados o claves revocadas. |

## Dependencias

- `pacman`

## Inicialización

El script `.install` ejecuta `pacman-key --populate cambonos` después de instalar o actualizar el paquete, siempre que exista `/etc/pacman.d/gnupg`.

Si pacman no está inicializado, muestra instrucciones y termina sin propagar un error:

```bash
sudo pacman-key --init
sudo pacman-key --populate cambonos
```

El paquete no sustituye el bootstrap de confianza de una instalación nueva. La ISO/instalador debe instalar este paquete desde un medio local confiable antes de habilitar el repositorio remoto.

## Política de confianza y canales

`stable` y `testing` utilizan una única clave de firma y deben contener exactamente el mismo material de keyring. El workflow compara byte a byte `cambonos.gpg`, `cambonos-trusted` y `cambonos-revoked` entre los snapshots de `dev` y `main`.

Una rotación se distribuye simultáneamente en ambos canales.

## Custodia y rotación

- La clave primaria se conserva offline.
- La subclave privada operativa se almacena como secreto protegido del entorno `package-signing`.
- El repositorio Git contiene únicamente material público.
- En una rotación ordinaria, el nuevo material debe distribuirse en un paquete firmado por la clave anterior para que los clientes existentes puedan verificar la transición.
- Ante compromiso de la subclave, debe detenerse la publicación, revocar la clave comprometida y establecer una transición autenticada. Si la clave anterior ya no es confiable, se requiere recuperación externa.
- Ante compromiso de la clave primaria, debe establecerse una nueva cadena de confianza. Algunos clientes necesitarán intervención manual y se publicará una ISO con la nueva cadena.

Consulta [`../../docs/GPG-SETUP.md`](../../docs/GPG-SETUP.md) para la generación y configuración de claves.

## Instalación y comprobación

En un equipo que ya tiene confianza establecida:

```bash
sudo pacman -S cambonos-keyring
sudo pacman-key --populate cambonos
sudo pacman-key --list-keys
```

Comprobar los archivos:

```bash
pacman -Qkk cambonos-keyring
gpg --show-keys --with-fingerprint /usr/share/pacman/keyrings/cambonos.gpg
```

Fingerprint de la clave primaria contenida en el material público actual:

`7B6BE3ABE5E7636F9019690C98C362C2C2E22906`

No utilizar esta referencia como sustituto de verificar el fingerprint por un canal autenticado independiente antes de una instalación inicial.

## Pruebas de validación

- [ ] Los tres ficheros públicos existen y son legibles.
- [ ] `cambonos.gpg` puede ser inspeccionado por GPG y contiene la clave esperada.
- [ ] El fingerprint primario coincide con el publicado por un canal autenticado.
- [ ] `cambonos-trusted` contiene el fingerprint esperado y el ownertrust previsto.
- [ ] `cambonos-revoked` tiene el contenido de revocación esperado.
- [ ] No hay material secreto ni exportaciones de subclaves privadas en el repositorio, artefactos o logs.
- [ ] `makepkg` construye el paquete y los tres archivos quedan en `/usr/share/pacman/keyrings/`.
- [ ] En un sistema con pacman-key inicializado, `post_install` ejecuta correctamente `pacman-key --populate cambonos`.
- [ ] En un sistema sin `/etc/pacman.d/gnupg`, el scriptlet muestra instrucciones y no falla la instalación.
- [ ] `post_upgrade` incorpora cambios del material público sin perder las claves previamente gestionadas por pacman.
- [ ] Repetir `pacman-key --populate cambonos` es seguro e idempotente.
- [ ] Una firma válida del repositorio se verifica con el keyring instalado.
- [ ] Una firma inválida o artefacto modificado es rechazado por pacman.
- [ ] Un paquete firmado por una clave no confiable es rechazado con `TrustedOnly`.
- [ ] Los tres archivos son idénticos en `dev` y `main`.
- [ ] La actualización ordinaria de clave se verifica desde una instalación que solo conoce la clave anterior.
- [ ] La revocación de una subclave se refleja correctamente después de actualizar el keyring.
- [ ] Se ensaya y documenta el procedimiento manual de recuperación ante compromiso de la clave primaria.
- [ ] La ISO de prueba puede realizar el bootstrap desde el medio local sin depender del mirror remoto.
- [ ] `pacman -Qkk cambonos-keyring` no detecta alteraciones inesperadas.

## Limitaciones

La instalación del paquete no puede establecer por sí misma una raíz de confianza en un equipo que aún no conoce la clave CambonOS. Esa confianza inicial debe llegar por un medio autenticado independiente.
