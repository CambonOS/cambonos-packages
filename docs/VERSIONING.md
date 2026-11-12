# Versionado de paquetes CambonOS (CPV)

**Especificación: CPV 1.0**

CPV define la política de versiones de los paquetes mantenidos por CambonOS. Está
inspirada en SemVer, pero utiliza directamente los campos de versión de Arch Linux y no
sustituye el modelo de versiones de Pacman.

## Formato

Todos los `PKGBUILD` de CambonOS deben utilizar:

```bash
pkgver=MAJOR.MINOR.PATCH
pkgrel=1
# epoch se omite o se establece en 0, salvo una reparación excepcional del orden de versiones de Arch.
```

`pkgver` contiene exactamente tres enteros decimales no negativos separados por puntos.
No se permiten ceros iniciales, componentes adicionales ni metadatos de pre-release o
build. `pkgrel` es un entero positivo y `epoch` un entero no negativo.

La versión Arch resultante es `[epoch:]pkgver-pkgrel`. Las comparaciones de orden deben
utilizar `vercmp` de Pacman; no se debe sustituir el orden de Arch por comparaciones de
cadenas o por las reglas de SemVer.

## Clasificación de cambios

Cuando un cambio incluya varias clases, se aplica la de mayor impacto.

| Campo | Cuándo incrementarlo | Ejemplo |
|---|---|---|
| MAJOR | Cambio incompatible, ruptura de interfaz o configuración, o rediseño sustancial incompatible. | `1.4.2` → `2.0.0` |
| MINOR | Nueva función o capacidad compatible, incluidas integraciones, opciones, recursos o mejoras visuales funcionales. | `1.4.2` → `1.5.0` |
| PATCH | Corrección de una función o comportamiento existente, incluidos errores visuales. | `1.4.2` → `1.4.3` |
| `pkgrel` | Cambio exclusivo de empaquetado que no modifica el comportamiento funcional. | `1.4.2-1` → `1.4.2-2` |

Cuando cambia `pkgver`, `pkgrel` debe volver a `1`. Si solo cambia el empaquetado,
`pkgver` se mantiene y `pkgrel` aumenta. Un cambio funcional nunca debe expresarse
únicamente mediante `pkgrel`.

La clasificación MAJOR/MINOR/PATCH corresponde al mantenedor. La automatización valida
el formato, el orden monotónico y el reinicio de `pkgrel`, pero no deduce la importancia
funcional de un diff. Registra el motivo en el mensaje del commit o en el changelog del
paquete.

## Canales

`testing` y `stable` utilizan la misma política CPV. La identidad del canal no se
codifica en `pkgver` ni en `pkgrel`: no añadas sufijos `alpha`, `beta`, `rc`, `dev` ni
identificadores de canal.

Cuando un paquete se promueve de testing a stable, debe promoverse el mismo artefacto,
identificado por su SHA-256, en lugar de reconstruirlo. El pipeline actual construye de
forma independiente los snapshots `dev/testing` y `main/stable`; CPV no rediseña ese
flujo. Por tanto, la promoción binaria idéntica entre canales sigue siendo un requisito
de pipeline y no una garantía que establezca por sí sola esta política.

## Inmutabilidad de artefactos

La tupla nombre/versión/arquitectura de un paquete publicado identifica un binario
inmutable. Solo se permite volver a publicar la misma versión si el SHA-256 del paquete
es idéntico. Un binario diferente requiere una versión CPV nueva. También se rechazan
cambios de fuente bajo una versión sin modificar.

El manifiesto de publicación mantiene la continuidad de cada canal. Un paquete puede
retirarse, pero uno que continúa publicado no puede retroceder en el orden de versiones
de Arch.

## Epoch

`epoch` se reserva para reparaciones excepcionales del orden de versiones de Arch. No es
un identificador de ciclo de publicación, un marcador de canal ni un sustituto de MAJOR.
No debe añadirse ni incrementarse en los cambios ordinarios.

## Alcance y migración

CPV se aplica únicamente a los paquetes mantenidos en este repositorio. Las dependencias
de Arch y AUR conservan sus políticas de versión upstream.

Las versiones ya publicadas no se reescriben. La política se aplica a todos los cambios
futuros. Las versiones existentes se aceptan como línea base inicial si cumplen el
formato numérico. No reinicies un `pkgrel` publicado solo para simplificarlo; el
siguiente cambio de `pkgver` comenzará en `pkgrel=1`.

## Línea base de la migración CPV

La migración inicial se aplicó sobre el snapshot `e530c5d` (11 de noviembre de 2026).
Las versiones existentes no se reiniciaron mecánicamente. Los paquetes con cambios
funcionales posteriores a su línea base anterior de `pkgver` se reclasificaron según
CPV; los cambios de metadatos exclusivamente de empaquetado no exigieron un incremento
funcional.

| Paquete | Versión anterior | Línea base CPV | Clasificación |
|---|---:|---:|---|
| `cambonos-base` | `0.1.0-1` | `0.1.0-1` | Sin cambios; línea base del metapaquete |
| `cambonos-branding` | `0.1.2-3` | `0.1.3-1` | PATCH: corrección de contraste de Dialog |
| `cambonos-fastfetch` | `0.1.1-3` | `0.1.2-1` | PATCH: corrección de color ANSI del terminal |
| `cambonos-grub` | `0.1.1-2` | `0.2.0-1` | MINOR: actualización del comportamiento de parámetros de arranque |
| `cambonos-gtk-theme` | `0.6.2-12` | `0.7.0-1` | MINOR: estilos de widgets y mejoras de accesibilidad |
| `cambonos-keyring` | `0.1.0-5` | `0.1.0-5` | Sin cambios; cambios solo de metadatos |
| `cambonos-lightdm` | `0.1.0-5` | `0.2.0-1` | MINOR: integración del tema Slick Greeter |
| `cambonos-pacman` | `0.1.0-4` | `0.1.0-4` | Sin cambios; corrección de dependencias |
| `cambonos-plymouth` | `0.1.1-9` | `0.2.0-1` | MINOR: escalado de resolución e integración de branding |
| `cambonos-release` | `0.1.1-3` | `0.1.2-1` | PATCH: corrección de color en os-release |
| `cambonos-shell-prompt` | `0.1.0-9` | `0.2.0-1` | MINOR: módulo de prompt para directorios personalizados |
| `cambonos-zsh` | `0.1.0-5` | `0.2.0-1` | MINOR: integración automática de sudo |

Estas versiones corresponden a la migración del árbol de fuentes. Antes de publicar, el
manifiesto debe confirmar que cada versión propuesta es superior a la última publicada
en su canal y que no sustituye una versión ya publicada. Si una versión de esta línea
base ya se publicó con otro binario, la discrepancia debe reconciliarse con el
manifiesto; no se debe eludir la regla de inmutabilidad.

## Ejemplos

```bash
# Paquete nuevo
pkgver=0.1.0
pkgrel=1

# Corrección funcional
pkgver=0.1.1
pkgrel=1

# Función compatible
pkgver=0.2.0
pkgrel=1

# Cambio incompatible
pkgver=1.0.0
pkgrel=1

# Corrección exclusiva de empaquetado tras 1.0.0-1
pkgver=1.0.0
pkgrel=2
```
