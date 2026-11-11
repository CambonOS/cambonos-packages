# Compilación selectiva (fase 4)

La fase 4 activa la reutilización de paquetes publicados únicamente cuando se
cumplen todas estas condiciones:

- El manifiesto global anterior y su firma son válidos.
- La recuperación del canal está completa y vinculada al hash del manifiesto.
- Cada paquete recuperado coincide con el manifiesto en identidad y hashes.
- La firma detached de cada paquete se vuelve a verificar con el keyring CambonOS.
- Los metadatos internos del paquete se inspeccionan con la imagen Arch fijada.
- El fingerprint actual coincide con el publicado.
- La versión, arquitectura y nombre de archivo actuales coinciden con el artefacto.

Si no hay recuperación disponible, el workflow hace un build completo. Si la
recuperación termina correctamente pero la validación para reutilizar falla, el
build selectivo se aborta: no se degrada silenciosamente a reutilización insegura.

## Flujo CI

1. Validar ambos snapshots y la política CPV.
2. Recuperar el manifiesto publicado.
3. Recuperar y verificar todos los paquetes del canal.
4. Calcular el plan actual.
5. Reutilizar únicamente candidatos cuya recuperación y firma vuelven a validarse.
6. Construir el resto en orden topológico.
7. Incluir todos los paquetes (nuevos y recuperados) en `packages/`.
8. Generar `build-plan.json`, `build-selection-report.json` y `build-manifest.json`.
9. El job de firma conserva la firma original de los paquetes reutilizados y firma
   únicamente los paquetes recién construidos.

La recuperación falla de forma no bloqueante para permitir un build completo de
respaldo. Un error posterior al activar reutilización sí bloquea el job de build,
por lo que no llega a firma ni publicación.

## Informes

`build-selection-report.json` muestra `mode`, `summary` y la acción de cada paquete:

- `build`: compilado en esta ejecución.
- `reuse`: copiado desde una publicación firmada y verificada.

`build-plan.json` conserva la decisión del planificador y el motivo.

## Comportamiento CPV

Una modificación de entradas de compilación con la misma versión se rechaza
durante la validación CPV. Los cambios de dependencias, receta o entorno pueden
obligar a reconstruir dependientes aunque sus entradas propias no hayan cambiado.
Si el binario resultante difiere y conserva la misma versión, la validación final
de publicación lo rechaza por inmutabilidad. En ese caso se debe incrementar
`pkgrel` y volver a ejecutar el pipeline.

Si la reconstrucción produce exactamente el mismo SHA-256, la versión existente
puede conservarse.

## Primer despliegue de esta fase

El cambio en el código del planificador y del builder cambia el fingerprint de
receta respecto a la publicación anterior. Por ello, el primer push que active
esta fase puede reconstruir los paquetes que antes eran candidatos. Es una
invalidación conservadora y esperada. Una ejecución posterior sin cambios de
receta ni entradas debería reutilizar los paquetes.

## Recuperación fallida

Si el manifiesto anterior existe pero no se puede recuperar por un fallo de red,
GPG, Docker o integridad, el workflow ejecuta un build completo. No reutiliza
ningún artefacto no verificado. Si la validación CPV o la firma/publicación
detectan una inconsistencia, el workflow falla y el mirror anterior permanece
intacto.
