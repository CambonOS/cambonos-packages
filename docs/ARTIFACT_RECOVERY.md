# Recuperación y verificación de artefactos publicados

La fase 2 incorpora `recover-artifacts`. Es una operación de solo lectura sobre el mirror: recupera en un directorio local los paquetes de un canal de la publicación anterior y no modifica el repositorio remoto ni el sitio.

## Verificaciones realizadas

1. Comprueba que el manifiesto global, su firma detached, el keyring público y el ownertrust están presentes.
2. Verifica la firma del manifiesto con `verify_previous_manifest_signature` y carga el esquema publicado.
3. Comprueba que la identidad de cada paquete es coherente entre el nombre de paquete, `pkgver`, `pkgrel`, `epoch`, arquitectura, `version`, nombre de archivo y nombre de firma.
4. Descarga el paquete y su firma desde `https://mirror.cambonos.org/<canal>/x86_64/` (o desde una base HTTPS explícita).
5. Comprueba SHA-256 del paquete y de la firma frente al manifiesto firmado.
6. Verifica la firma detached del paquete y exige que proceda de una subclave de firma presente en el keyring CambonOS cuya clave primaria tenga ownertrust ultimate.
7. Inspecciona la identidad interna del paquete mediante `pacman -Qp` y `pacman -Qip` dentro de la imagen Arch fijada; compara nombre, versión (incluido epoch) y arquitectura con el manifiesto.
8. Escribe un informe local y publica el directorio recuperado mediante un rename atómico. Si falla cualquier comprobación, elimina el staging y no deja un resultado parcial.

El directorio de salida debe no existir. El comando nunca sobrescribe datos existentes.

## Ejemplo

```bash
python scripts/cambonos.py recover-artifacts \
  --previous-manifest /tmp/previous-manifest.json \
  --previous-manifest-signature /tmp/previous-manifest.json.sig \
  --keyring-public-key packages/cambonos-keyring/files/cambonos.gpg \
  --keyring-trusted packages/cambonos-keyring/files/cambonos-trusted \
  --channel testing \
  --output /tmp/cambonos-recovered-testing
```

Para stable, cambia `--channel stable` y usa un directorio de salida diferente.

## Límites deliberados de esta fase

- No se integra todavía en el workflow automático.
- No modifica el planificador ni activa la reutilización de paquetes.
- No firma, reconstruye, promueve ni publica nada.
- La recuperación exige que el manifiesto contenga `signature_file`, `signature_hash`, `pkgver`, `pkgrel`, `epoch` y `architecture`. Un manifiesto antiguo sin estos campos falla de forma cerrada; no se intenta adivinar ni descargar artefactos no autenticados.
- La comprobación de la identidad interna utiliza Docker y la imagen de construcción configurada; no se confía únicamente en el nombre del archivo.
