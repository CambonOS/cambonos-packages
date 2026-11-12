# Comparación de artefactos en modo sombra (fase 3)

La fase 3 compara una compilación completa con los artefactos recuperados y
verificados de una publicación anterior. El workflow ejecuta esta comparación
automáticamente en cada job de build y conserva `shadow-report.json` dentro del
artefacto de build. También puede ejecutarse manualmente con el CLI.

Es una operación estrictamente de observación: no omite builds, no firma, no
sustituye artefactos y no publica. La recuperación y la comparación usan
`continue-on-error`: un fallo de observación genera un aviso, pero no bloquea
la construcción, firma o publicación del pipeline legado.

## Flujo

1. Ejecutar de nuevo `recover-artifacts` para el canal contra el manifiesto global
   firmado. Es necesario regenerar la recuperación después de instalar esta fase:
   los informes de fase 2 no transportaban los fingerprints al `recovery-report.json`.
2. Ejecutar el build completo del canal con el comando `build` habitual.
3. Ejecutar `compare-shadow` sobre el directorio del build y el directorio
   recuperado.
4. Revisar `shadow-report.json` y conservar ambos resultados para comparar
   futuras ejecuciones.

## Ejemplo

```bash
python scripts/cambonos.py compare-shadow \
  --build-dir /tmp/cambonos-build/testing \
  --recovered-dir /tmp/cambonos-recovery/testing \
  --previous-manifest /tmp/cambonos-recovery/manifest.json \
  --previous-manifest-signature /tmp/cambonos-recovery/manifest.json.sig \
  --keyring-public-key packages/cambonos-keyring/files/cambonos.gpg \
  --keyring-trusted packages/cambonos-keyring/files/cambonos-trusted \
  --output /tmp/cambonos-shadow-testing.json
```

El directorio de build debe contener `build-manifest.json` y `packages/`. El
directorio recuperado debe contener `recovery-report.json`, los paquetes y sus
firmas. El comparador vuelve a calcular los hashes de los archivos recuperados
para detectar modificaciones posteriores a la recuperación. También valida
los hashes de los paquetes recién construidos mediante `verify_build_manifest`.

## Clasificaciones

| Clasificación | Significado |
|---|---|
| `reusable` | Fingerprint, identidad y SHA-256 coinciden; paquete y firma anteriores serían conservables. |
| `input_changed` | Cambió `build_input_hash`. |
| `fingerprint_changed` | Las entradas del paquete coinciden, pero cambió receta, entorno, perfil o fingerprint de dependencias. |
| `binary_mismatch` | Fingerprint idéntico, pero SHA-256 binario diferente. No reutilizable. |
| `identity_mismatch` | Fingerprint idéntico, pero versión, arquitectura o nombre de archivo no coinciden. No reutilizable. |
| `legacy_unverifiable` | El manifiesto anterior no contiene fingerprint; no se puede autorizar reutilización. |
| `new_package` | El paquete no existía en la publicación recuperada. |
| `removed_package` | El paquete anterior ya no aparece en el build actual. |

La firma detached anterior puede diferir de una firma generada de nuevo incluso
cuando el binario es idéntico. Para `reusable`, se conserva la firma recuperada;
no se exige que una firma nueva tenga los mismos bytes.

## Garantías y límites

- El comparador exige que los canales coincidan.
- El informe de recuperación debe acreditar firma del manifiesto, firma de cada
  paquete y metadatos internos verificados.
- Los hashes del paquete y de la firma recuperados se recalculan antes de comparar.
- Las publicaciones antiguas sin `build_fingerprint` se clasifican como
  `legacy_unverifiable`; nunca se declaran reutilizables.
- Un fingerprint coincidente con SHA-256 diferente se informa como
  `binary_mismatch`. Es una señal de entradas no capturadas o de falta de
  reproducibilidad, no una autorización para reutilizar.
- El informe JSON se crea de forma atómica y no sobrescribe uno existente.
- `publication_modified` y `build_skipped` permanecen en `false`.
- En GitHub Actions, el informe se incorpora al artefacto `build-testing` o
  `build-stable`. Si la recuperación o comparación falla, el job registra el
  fallo de observación, pero continúa para no convertir esta fase en una puerta
  que pueda detener el pipeline de publicación existente.

Esta fase no activa compilación selectiva ni reutilización. La activación requiere
revisar informes reales de ambos canales y probar escenarios de cambios, paquetes
nuevos/eliminados y discrepancias binarias.
