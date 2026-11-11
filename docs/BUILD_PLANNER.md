# Planificador de compilaciones (fase sombra)

El comando `plan` calcula qué paquetes necesitan reconstrucción, pero **no compila,
descarga, firma ni publica artefactos**. El workflow actual continúa siendo el
responsable de construir todos los paquetes y publicar como hasta ahora.

```bash
python3 scripts/cambonos.py plan \\
  --source-root . \\
  --channel testing \\
  --image 'archlinux:base-devel-20261011.0.609700@sha256:d6979123107e7a9f52c2de19104966b5f809e13a4593017780bd8c0b140f80ff' \\
  --previous-manifest /ruta/al/manifest.json \\
  --output /tmp/cambonos-build-plan.json
```

Sin un manifiesto anterior compatible, todos los paquetes se marcan como `build`.
Los manifiestos publicados antes de incorporar `build_fingerprint` tampoco permiten
reutilizar paquetes: se consideran conservadoramente candidatos a reconstrucción.

## Huella de compilación

La huella combina:

- `PKGBUILD`, scripts `.install`, contenido de `files/` y metadata de fuentes externas.
- Receta del builder y código auxiliar que determina el orden y la ejecución.
- Imagen de Arch configurada y arquitectura.
- Huella de dependencias internas de construcción (`makedepends` y
  `checkdepends` cuando existe `check()`).
- Perfil del canal. `cambonos-pacman` tiene perfiles distintos para `testing` y
  `stable`; los demás paquetes comparten perfil.

El README del paquete queda fuera de las entradas de build. Los recursos bajo
`files/` se incluyen completos, aunque sean documentación instalada por el paquete.

## Interpretación del resultado

- `build`: la huella actual no coincide con una huella previa compatible.
- `reuse-candidate`: la huella coincide y el manifiesto anterior contiene los
  metadatos mínimos del artefacto.
- `reuse_candidates`: número de candidatos, no reutilizaciones ya autorizadas.

Un candidato **no es todavía un artefacto reutilizable confirmado**. La siguiente
fase debe recuperar el paquete y su firma del repositorio publicado, comprobar
nombre, versión, arquitectura, SHA-256 y firma, y solo entonces permitir su
reutilización. No debe modificarse el pipeline de publicación hasta implementar y
probar esas verificaciones.

## Transición de `source_hash`

Los manifiestos actuales usan `source_hash`, que incluye documentación. Los nuevos
registros añaden `build_input_hash`, que representa las entradas que afectan al
paquete. Si el manifiesto anterior no contiene `build_input_hash`, la política
mantiene la comparación histórica de `source_hash` (conservadora): durante esa
transición un cambio documental puede seguir exigiendo una nueva versión. Una vez
que ambos lados dispongan de `build_input_hash`, los cambios documentales externos
al payload no provocan un cambio de entradas de build.

Este planificador es una primera fase de observación. No ofrece reproducibilidad
binaria absoluta ni decide por sí solo incrementos de `pkgrel`.
