# CambonOS — Checklist esencial de paquetes y repositorio

Checklist breve para validar un candidato de `dev` antes de integrarlo en `main`. Ejecutar las pruebas de instalación en una VM Arch desechable o snapshot restaurable, nunca en el equipo principal. Aplicar las comprobaciones al paquete o componente cambiado; los casos de error y límites se cubren en `tests/` y no se repiten manualmente en cada release.

## 1. Gate de release

- [ ] Registrar SHA exactos de `dev` y `main`, fecha, arquitectura, versión Arch y snapshot utilizado.
- [ ] Ejecutar `python3 -m unittest discover -s tests -v`; validar estáticamente ambos snapshots y la política de versiones.
- [ ] Confirmar que CI valida y construye los snapshots fijados; registrar los resultados de `validate`, `build` y `signing`.
- [ ] Para cada paquete cambiado, revisar `pkgver`/`pkgrel`, arquitectura, `depends`, `makedepends`, `checkdepends`, `backup` y rutas instaladas.
- [ ] Construir los paquetes afectados en el entorno Arch aislado del pipeline e inspeccionar contenido y dependencias.
- [ ] Confirmar que los tres ficheros públicos de `cambonos-keyring` son idénticos entre ramas y que no se incluye material secreto.
- [ ] Verificar firmas de bases de datos y paquetes desde un cliente con `Required TrustedOnly`; no relajar `SigLevel`.

## 2. Ciclo de vida

Aplicar estas comprobaciones a cada paquete afectado, no repetir la matriz completa si el paquete no cambió.

- [ ] En una VM/snapshot Arch, instalar o actualizar desde el canal previsto; comprobar que todas las dependencias se resuelven automáticamente.
- [ ] Reinstalar el paquete y confirmar que sus scriptlets y hooks terminan sin errores.
- [ ] Comprobar `pacman -Qkk` y que las rutas instaladas coinciden con el contenido declarado.
- [ ] Si usa `backup` o configura archivos compartidos, confirmar que preserva la configuración ajena y revisar los `.pacnew` sin sobrescribirlos a ciegas.
- [ ] Desinstalar solo cuando el cambio requiera validar retirada; comprobar que se retiran los archivos/bloques propios y se conserva el contenido administrativo.
- [ ] Guardar versiones, comandos, logs e incidencias de la ejecución.

## 3. Smoke tests por familia

Ejecutar solo el bloque correspondiente a los paquetes cambiados.

- [ ] `cambonos-branding`: verificar rutas de recursos canónicos, dimensiones PNG, licencia y `fc-match 'CambonOS Symbols'`. Los recursos gráficos son `cambonos-icon.svg`, `cambonos-text.svg`, `cambonos-icon.png` y `cambonos-text.png`; se excluyen `cambonos-icon-black.svg`, `cambonos-icon-white.svg`, `cambonos-text-black.svg`, `cambonos-text-white.svg` y `cambonos-logo.txt`. Para una actualización desde `0.1.1-1` a `0.1.1-3`, confirmar la retirada de los recursos obsoletos. No se depende de rutas antiguas ni aliases; el fallback conserva la fuente.
- [ ] `cambonos-fastfetch`, `cambonos-shell-prompt`, `cambonos-zsh`: comprobar la salida principal y sesiones interactivas de los shells instalados; no ejecutar en shells no interactivos, respetar el opt-out y no modificar archivos personales.
- [ ] `cambonos-release`: verificar la identidad CambonOS; install/upgrade/remove preservan enlaces, archivos y cambios administrativos ajenos.
- [ ] `cambonos-pacman`: confirmar dependencias en `.PKGINFO` (incluido `diffutils`), `Required TrustedOnly` en stable/testing, opciones efectivas de `pacman-conf`, lista de repositorios e idempotencia de `manage-pacman-config`.
- [ ] `cambonos-grub`: verificar los defaults acordados y la regeneración segura del menú; probar arranque visual solo si cambian tema, configuración o hooks.
- [ ] `cambonos-plymouth`: verificar drop-in, orden de hooks, tema y reconstrucción de initramfs; probar arranque visual solo si cambia el tema o su integración.
- [ ] `cambonos-keyring`: verificar fingerprint por canal autenticado, igualdad entre ramas, aceptación de paquete firmado válido y rechazo de firma inválida/no confiable; nunca incluir claves privadas.

## 4. Repositorio y publicación

- [ ] Confirmar que los manifiestos corresponden a los SHA fijados y que las versiones cumplen la política de fuente/`pkgver`/`pkgrel`.
- [ ] Confirmar que `testing` y `stable` se validan independientemente y que cada paquete, firma e índice publicado está representado en el manifiesto.
- [ ] Desde un cliente de prueba, sincronizar ambos canales con verificación activa e instalar/actualizar el paquete candidato.
- [ ] Confirmar que un fallo en validación, construcción o firma impide publicar y conserva el sitio anterior.

## 5. Pruebas condicionales

No son parte del ciclo ordinario; ejecutarlas solo cuando el cambio afecte a esa responsabilidad. Los escenarios de fallo unitarios no se repiten manualmente salvo regresión o cambio de diseño.

- Keyring: rotación, revocación y recuperación solo en entorno aislado cuando cambie la cadena de confianza.
- Configuración `backup`: casos especiales de `.pacnew` y preservación de cambios cuando cambie el archivo administrado.
- GRUB/Plymouth: arranque UEFI/BIOS, cifrado, multiboot, hardware y generación de initramfs cuando cambien esos componentes.
- Gestores de shell y release: concurrencia, marcadores dañados y recuperación solo si cambia esa lógica.

## 6. Registro reciente

- `dev` probado: `9e75fb15db9c2518e2fdd920326dc8383dbbb309`; corrección de `cambonos-pacman` publicada en `1a75c1dbc92f9018c686ec5b683a238e7f578811`.
- La suite registró 183 tests correctos; la validación estática cubrió los nueve paquetes.
- En `arch-pruebas`, desde una snapshot sin paquetes CambonOS ni `diffutils`, pacman instaló `diffutils` como dependencia de `cambonos-pacman 0.1.0-2`. La reinstalación, `pacman -Qkk` e idempotencia del helper pasaron.
- Pacman rechazó un paquete temporal con firma detached alterada. No se probó una clave firmante no confiable ni recuperación de keyring.
- Las pruebas visuales/funcionales de GRUB, Plymouth y Zsh fueron confirmadas por el usuario; la VM no tiene kernel ni contenido en `/boot`, así que no validó arranque real.
- Cinco `.pacnew` difieren de sus archivos activos y quedan pendientes de revisión administrativa; no se modificaron.
- No se construyó localmente con `makepkg`; se probó el artefacto publicado y firmado.
