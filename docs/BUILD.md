# Planificación y compilación de paquetes

El sistema de compilación calcula qué paquetes deben reconstruirse, recupera artefactos
publicados y reutiliza únicamente aquellos cuya identidad e integridad puede verificar.
La automatización de GitHub Actions ejecuta este proceso desde `package-build.yml`.

## Flujo general

Para cada canal (`testing` o `stable`), el builder:

1. Carga y ordena los paquetes según sus dependencias internas de construcción.
2. Recupera y verifica los artefactos de la publicación anterior, si están disponibles.
3. Calcula el plan a partir de las entradas, la receta, la imagen y las dependencias.
4. Reutiliza los artefactos que superan todas las verificaciones o construye los
   paquetes restantes.
5. Genera los paquetes y los informes de compilación para su posterior firma y publicación.

La compilación selectiva está integrada en el workflow. `plan`, `recover-artifacts` y
`compare-shadow` también están disponibles como comandos independientes para inspección,
recuperación y diagnóstico.

## Planificación y fingerprints

El comando `plan` calcula las acciones sin compilar, descargar, firmar ni publicar:

```bash
python3 scripts/cambonos.py plan \
  --source-root . \
  --channel testing \
  --image 'archlinux:base-devel-20261011.0.609700@sha256:d6979123107e7a9f52c2de19104966b5f809e13a4593017780bc8c0b140f80ff' \
  --previous-manifest /ruta/al/manifest.json \
  --output /tmp/cambonos-build-plan.json
```

El plan compara la huella actual con los registros del canal correspondiente en el
manifiesto anterior. La huella de entradas del paquete incluye:

- `PKGBUILD` y scripts `.install`.
- Archivos y enlaces simbólicos del directorio `files/`.
- Metadatos de fuentes externas almacenados en `.cambonos-source.json`, cuando existe.

La documentación del paquete, como su `README.md`, no forma parte de las entradas de
compilación. Los recursos de `files/` sí se incluyen, aunque sean documentación que el
paquete instala en el sistema.

El fingerprint completo combina las entradas del paquete con la receta del builder
(`build.py`, `validation.py`, `common.py` y `planner.py`), la imagen de Arch, la
arquitectura, el perfil del canal y los fingerprints de sus dependencias internas de
construcción. Se incluyen `makedepends` y `checkdepends` cuando el paquete define
`check()`. Los paquetes se procesan en orden topológico para incorporar las huellas de
sus dependencias.

`cambonos-pacman` utiliza perfiles diferentes para `testing` y `stable`; el resto de
paquetes utiliza el perfil común.

Los enlaces simbólicos del payload se incorporan mediante su ruta, permisos y destino
literal. Los enlaces absolutos representan rutas de la raíz del sistema destino y no se
resuelven contra el runner. Los enlaces relativos deben apuntar a entradas existentes
dentro de `files/`; se rechazan los enlaces rotos, cíclicos o que escapen de ese árbol.

### Acciones del plan

- `build`: las entradas, la receta o la identidad no permiten reutilizar el artefacto
  anterior.
- `reuse-candidate`: el fingerprint y los metadatos del manifiesto coinciden. Todavía
  requiere recuperar y verificar criptográficamente el artefacto.

Un candidato no es una reutilización autorizada. La decisión definitiva se toma después
de verificar la recuperación. Sin un manifiesto anterior compatible, todos los paquetes
se marcan para construcción.

Los manifiestos antiguos sin `build_fingerprint` no permiten reutilizar paquetes.
Durante la transición de `source_hash` a `build_input_hash`, los registros antiguos se
tratan de forma conservadora: no se deducen fingerprints que no estén presentes.

## Recuperación de artefactos publicados

`recover-artifacts` recupera los paquetes de un canal sin modificar el mirror:

```bash
python3 scripts/cambonos.py recover-artifacts \
  --previous-manifest /ruta/previous-manifest.json \
  --previous-manifest-signature /ruta/previous-manifest.json.sig \
  --keyring-public-key packages/cambonos-keyring/files/cambonos.gpg \
  --keyring-trusted packages/cambonos-keyring/files/cambonos-trusted \
  --channel testing \
  --output /tmp/cambonos-recovered-testing
```

El comando exige un manifiesto firmado y realiza estas comprobaciones:

1. Verifica la firma del manifiesto con el keyring público y el ownertrust
   proporcionados.
2. Comprueba que la identidad de cada paquete coincide con el registro firmado: nombre,
   versión, epoch, arquitectura, archivo y firma.
3. Descarga el paquete y su firma desde el mirror HTTPS configurado.
4. Comprueba los hashes SHA-256 del paquete y de la firma.
5. Verifica la firma detached del paquete y que procede de una subclave autorizada del
   keyring CambonOS.
6. Inspecciona los metadatos internos del paquete con `pacman` dentro de la imagen Arch
   fijada.
7. Genera `recovery-report.json` y publica el directorio recuperado mediante un rename
   atómico.

El directorio de salida debe no existir. La recuperación no sobrescribe datos y elimina
el staging si falla una comprobación. Para `stable`, cambia `--channel` y utiliza otro
directorio de salida.

## Compilación selectiva integrada

En `package-build.yml`, la recuperación de la publicación anterior se intenta antes de
ejecutar `build`:

- Si la recuperación falla o no está disponible, el paso de recuperación no bloquea el
  job y el builder realiza una compilación completa.
- Si la recuperación termina correctamente, el builder vuelve a verificar que el informe
  y los archivos recuperados correspondan al manifiesto firmado, comprueba hashes y
  firmas y valida los metadatos antes de admitir cualquier reutilización.
- Si una comprobación falla después de activar la ruta selectiva, el build falla de
  forma cerrada. No se reutiliza ningún artefacto que no haya superado todas las
  verificaciones.

El builder reutiliza solo los paquetes cuyo fingerprint, versión, arquitectura, nombre
de archivo y hashes coinciden. Copia el paquete y su firma original al resultado. El
resto se construye en orden topológico dentro de contenedores Arch independientes.

Los paquetes reutilizados conservan su firma original; el job `sign` firma los paquetes
recién construidos. Ambos conjuntos se incluyen en el artefacto del canal para ensamblar
una publicación completa.

### Informes del build

Los directorios de salida incluyen estos informes:

- `build-plan.json`: acciones previstas y motivos del planificador.
- `build-selection-report.json`: modo de ejecución y acción final por paquete (`build` o
  `reuse`).
- `build-manifest.json`: identidad, fingerprints y hashes de los artefactos construidos
  o reutilizados.

Los informes acompañan a los artefactos de compilación y permiten auditar por qué se construyó
o reutilizó cada paquete.

## Comparación en modo sombra

`compare-shadow` es una herramienta CLI de diagnóstico. No se invoca actualmente desde
`package-build.yml` ni forma parte automática de la publicación. Compara un build
completo con una recuperación verificada, sin reutilizar, firmar ni publicar:

```bash
python3 scripts/cambonos.py compare-shadow \
  --build-dir /ruta/al/build \
  --recovered-dir /ruta/a/la/recuperacion \
  --previous-manifest /ruta/previous-manifest.json \
  --previous-manifest-signature /ruta/previous-manifest.json.sig \
  --keyring-public-key packages/cambonos-keyring/files/cambonos.gpg \
  --keyring-trusted packages/cambonos-keyring/files/cambonos-trusted \
  --output /tmp/cambonos-shadow-testing.json
```

El directorio de compilación debe contener `build-manifest.json` y `packages/`; el recuperado
debe contener `recovery-report.json`, los paquetes y sus firmas. El comparador vuelve a
verificar la relación con el manifiesto firmado y los hashes antes de generar el
informe. El archivo de salida, si se especifica, no debe existir previamente.

Clasificaciones principales:

| Clasificación | Significado |
|---|---|
| `reusable` | Fingerprint, identidad y SHA-256 coinciden. |
| `input_changed` | Han cambiado las entradas del paquete. |
| `fingerprint_changed` | Han cambiado la receta, el entorno, el perfil o las dependencias. |
| `binary_mismatch` | El fingerprint coincide, pero el binario es diferente. |
| `identity_mismatch` | No coincide la versión, arquitectura o nombre de archivo. |
| `legacy_unverifiable` | El manifiesto anterior no contiene fingerprint suficiente. |
| `new_package` | El paquete no existía en la publicación anterior. |
| `removed_package` | El paquete ya no forma parte de la compilación actual. |

La firma detached anterior puede ser distinta de una firma nueva aunque el binario sea
idéntico. Cuando un paquete es reutilizable, se conserva la firma recuperada.

## Versionado y límites

Los cambios en entradas de compilación deben respetar la política CPV. Una
reconstrucción que genere un binario diferente no puede sustituir el artefacto publicado
bajo la misma identidad; debe utilizar una versión nueva conforme a
[VERSIONING.md](VERSIONING.md).

Una huella coincidente no garantiza por sí sola reproducibilidad binaria. Si el hash del
binario difiere, el artefacto no se reutiliza. La imagen de Arch está fijada por digest,
pero sus repositorios rolling pueden cambiar entre ejecuciones.

La firma y la publicación se realizan en el workflow independiente
`package-publish.yml`, descrito en [DEPLOYMENT.md](DEPLOYMENT.md).
