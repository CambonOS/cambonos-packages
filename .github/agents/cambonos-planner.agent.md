# CambonOS Planner — Contexto del proyecto y reglas de planificación

> Documento de contexto para agentes de IA que planifiquen cambios en `CambonOS/cambonos-packages`.
>
> **Objetivo del agente:** proponer cambios coherentes con la arquitectura, las decisiones y las restricciones de CambonOS. Este documento sirve como fuente de contexto del proyecto; antes de planificar una modificación concreta, inspecciona siempre el estado real de la rama, los archivos afectados, sus tests, la documentación y el pipeline actuales. No supongas que los datos de versiones o publicación de este documento siguen siendo los últimos.

## 1. Identidad y objetivo del proyecto

CambonOS es una distribución personalizada basada en **Arch Linux**. Su propósito es facilitar la instalación, configuración y uso de Arch mediante una capa propia de paquetes, configuraciones, integración y herramientas.

La filosofía central es:

- **Arch Linux es el núcleo:** se conserva su base, su ecosistema, `pacman` y el modelo rolling-release.
- **CambonOS es la capa de facilitación y personalización:** aporta identidad visual, configuraciones coherentes, integración entre componentes y herramientas propias.
- Las herramientas nuevas se desarrollarán mayoritariamente en **Python** (por ejemplo, gestor de paquetes/publicación y el futuro instalador/actualizador).
- Los componentes deben tener responsabilidades pequeñas, explícitas y bien delimitadas.
- Se prioriza una experiencia de uso integrada sin apropiarse innecesariamente de configuraciones que pertenecen al administrador o al usuario.

CambonOS sigue en construcción. Que un paquete se publique o que sus tests pasen no significa que su funcionamiento esté validado de forma exhaustiva en todas las instalaciones, shells, escritorios y ciclos de actualización. Las pruebas de integración y de largo plazo deben continuar ampliándose.

## 2. Branding e identidad visual

### 2.1 Concepto

El branding utiliza dos mascotas:

- **Pingüino azul:** representa Linux/Arch como núcleo del sistema; sus tonos azules evocan Arch Linux.
- **Serpiente verde:** representa Python y la capa de herramientas y personalización de CambonOS.

La combinación de animales y naturaleza evoca el azul del mar y el verde de praderas y bosques. Las mascotas forman parte de la identidad de la distribución, no son elementos decorativos intercambiables sin criterio.

### 2.2 Paleta cromática oficial

Los valores HEX de referencia son exactos y no deben sustituirse por aproximaciones:

| Color | HEX | Uso orientativo |
|---|---|---|
| Verde lima eléctrico | `#AEFA50` | Identidad, energía y elementos protagonistas. |
| Turquesa luminoso | `#70E7E6` | Frescura, innovación y elementos destacados. |
| Azul noche profundo | `#061C31` | Textos, contornos, fondos oscuros y estructura. |
| Blanco | `#F7F5EC` | Limpieza, espacios negativos y fondos. |
| Verde esmeralda | `#149246` | Color de contraste del verde lima. |
| Azul turquesa | `#019FA7` | Color de contraste del turquesa luminoso. |

Hay una paleta principal de cuatro colores y una paleta ampliada de seis. Los dos colores de contraste no sustituyen a los principales. Si se modifica la paleta oficial, debe actualizarse la documentación de identidad y revisar todos los consumidores afectados.

**Fastfetch:** el logotipo ASCII utiliza intencionadamente una selección simplificada de cuatro colores, porque más colores hacen que el arte ASCII pierda detalle/legibilidad. La configuración actual discutida asigna:

1. `#061C31`
2. `#AEFA50`
3. `#F7F5EC`
4. `#70E7E6`

Las claves de módulos utilizan `#AEFA50` y el título `#70E7E6`. No “corrijas” esta selección para forzar seis colores: es una decisión de diseño explícita. Fastfetch admite colores HEX directamente en su configuración.

## 3. Alcance del repositorio `cambonos-packages`

Este repositorio es el objeto de planificación. Mantiene:

- PKGBUILDs y recursos de los paquetes CambonOS.
- Tests automatizados de paquetes y de la infraestructura.
- Herramientas Python para validar, construir, firmar y publicar.
- El pipeline CI/CD de los canales `testing` y `stable`.
- La documentación técnica y de operación del repositorio.

### 3.1 Repositorios relacionados y límites

| Repositorio | Función | Tratamiento al planificar `cambonos-packages` |
|---|---|---|
| `CambonOS/cambonos-packages` | Paquetes propios, validación, construcción, firma y mirror. | **Alcance principal.** |
| `CambonOS/cambonos-web` | Sitio oficial bilingüe basado en Hugo; `cambonos.org`; despliegue propio de GitHub Pages. | Repositorio independiente. Coordinar documentación/enlaces si procede, pero no mezclar sus workflows con el pipeline de paquetes. |
| `CambonOS/installer` | Instalador de la distribución actualmente operativa. | Fuera del alcance de auditoría/desarrollo futuro de esta línea. Solo referencia histórica para conocer paquetes y configuraciones necesarias. |
| `CambonOS/iso` | Perfil y construcción de la ISO actualmente operativa. | Fuera del alcance de auditoría/desarrollo futuro de esta línea. Solo referencia histórica. |
| `Cambon18/xfce` | Instalador/configuración de la experiencia XFCE actual. | Fuera del alcance de auditoría/desarrollo futuro de esta línea. Solo referencia histórica. |
| `Cambon18/qtile` | Instalador/configuración de la experiencia Qtile actual. | Fuera del alcance de auditoría/desarrollo futuro de esta línea. Solo referencia histórica. |

La web y el mirror tienen ciclos y workflows independientes:

- `cambonos.org`: sitio institucional, páginas informativas/descargas y contenido bilingüe.
- `mirror.cambonos.org`: publicación de paquetes y metadatos firmados.

El pipeline de `cambonos-packages` no debe compilar/desplegar Hugo ni depender de la compilación de la web. La web puede enlazar el mirror y mostrar información, pero el mirror y sus manifiestos son la fuente de verdad de los paquetes publicados.

### 3.2 Fuera de alcance actual

No convertir la planificación de paquetes en una planificación general de la nueva ISO o del instalador. La visión futura contempla herramientas Python y un instalador Python con **Textual** como TUI; una GUI GTK4 se ha mencionado como posibilidad, pero no es prioritaria. No se está realizando ahora una planificación a largo plazo de esa línea.

Los repositorios antiguos de instalador/ISO/escritorios pueden consultarse solo para extraer hechos técnicos de la instalación actual. No proponer cambios en ellos como parte de un plan de `cambonos-packages`.

## 4. Arquitectura de paquetes: modelo híbrido

La arquitectura elegida es **híbrida, modular y basada en responsabilidades explícitas**:

1. Cada componente funcional tiene su propio paquete con una función clara.
2. Los paquetes de componentes contienen sus propios recursos, configuración, hooks e integración cuando corresponda.
3. Los metapaquetes futuros agruparán dependencias para instalar conjuntos coherentes, pero no absorberán la propiedad de los archivos ni la lógica de los componentes.
4. Se respetan los archivos de configuración por defecto y las modificaciones del administrador/usuario.
5. No se debe crear un paquete monolítico que mezcle branding, shell, escritorio, release, repositorios y herramientas.

### 4.1 Metapaquetes previstos

- `cambonos-base`: metapaquete futuro que agrupará los elementos esenciales de la distribución (configuración de pacman/repositorios, keyring, release, shell Zsh y demás componentes básicos). Su estado de planificación fue marcado como **old/aplazado**: no implementarlo ni reabrir su diseño sin una decisión explícita nueva.
- `cambonos-desktop-xfce`: metapaquete futuro que agrupará paquetes de temas GTK, branding de escritorio, configuración XFCE, Thunar, LightDM y otros componentes necesarios.
- El futuro escritorio seguirá el mismo modelo híbrido: paquetes especializados más un metapaquete de integración.

Los metapaquetes solo deben expresar dependencias y agrupación; evitar scripts o archivos que dupliquen la responsabilidad de los paquetes componentes.

## 5. Catálogo actual de paquetes

La instantánea de referencia inspeccionada contiene estos siete paquetes. Consulta siempre los README y PKGBUILD actuales antes de proponer cambios.

| Paquete | Responsabilidad conocida | Consideraciones de planificación |
|---|---|---|
| `cambonos-branding` | Recursos gráficos genéricos de CambonOS: SVG/PNG, fuente `CambonOS-Symbols.ttf`, integración Fontconfig y licencia. | Mantener recursos canónicos y sus rutas; comprobar dimensiones, estructura, fuente, Fontconfig, ciclo de actualización y retirada de recursos antiguos. No mezclar temas GTK o branding específico de escritorios. |
| `cambonos-fastfetch` | Configuración de Fastfetch e integración automática con shells interactivas. | JSONC; paleta simplificada de cuatro colores para el logo ASCII; preservar integración idempotente y no sobrescribir configuración personal. |
| `cambonos-shell-prompt` | Configuración de Starship e integración en Zsh, Bash y Fish. | Mantener responsabilidades de integración por shell; los cambios deben probar shells reales y no solo parsear TOML. `right_format` se conserva actualmente. |
| `cambonos-zsh` | Configuración global de Zsh y punto de entrada/cargador de fragmentos. | Proporciona `/usr/share/cambonos/zsh/conf.d/`; no modificar directamente `/etc/zsh/zshrc` desde paquetes consumidores. |
| `cambonos-keyring` | Raíz pública de confianza para los repositorios CambonOS en pacman. | Crítico para la cadena de confianza. Cualquier rotación requiere transición y pruebas de bootstrap/actualización/recuperación. |
| `cambonos-release` | Identidad de distribución y metadatos release/LSB. | Preservar cambios del administrador cuando corresponda; revisar instalación, actualización y desinstalación, incluida la restauración conservadora de metadatos. |
| `cambonos-repo` | Configuración e integración de repositorios CambonOS en pacman. | Depende de `cambonos-keyring`; configuración de repositorios y habilitación de canales; comprobar backup de `/etc/pacman.d/cambonos.conf` y bootstrap. |

### 5.1 Integración entre paquetes

- `cambonos-zsh` ofrece el cargador global de fragmentos Zsh en `/usr/share/cambonos/zsh/conf.d/`.
- `cambonos-shell-prompt` y `cambonos-fastfetch` colocan sus fragmentos Zsh en ese directorio, sin editar `/etc/zsh/zshrc`.
- Para bloques de Bash, los componentes utilizan marcadores independientes y el bloqueo compartido `/run/lock/cambonos-shell-integration.lock`.
- Las integraciones deben ser idempotentes, no duplicar bloques en cada actualización y retirar únicamente los bloques/recursos que sean propiedad del paquete.
- No modificar configuraciones personales ni borrar contenido ajeno.

### 5.2 Starship y `right_format`

La configuración actual mantiene `right_format` para `$status$jobs$cmd_duration`; no se debe eliminar ni migrar automáticamente a `$fill` sin decisión y pruebas posteriores. La línea de entrada conserva `$character` en la segunda línea de `format`.

Bash no proporciona por sí mismo un mecanismo de prompt derecho equivalente al de Zsh/Fish. En la conversación se identificaron Ble.sh y Flyline como mecanismos de compatibilidad para Bash (Ble.sh >= 0.4 o Flyline >= 1.7.1, según documentación consultada). Se comentó que sus paquetes Arch se encontraban en AUR; verificar el estado actual antes de convertirlos en dependencias o tomar decisiones de empaquetado. No introducirlos como dependencias obligatorias de todos los usuarios/shells sin una decisión explícita. La integración visual en Bash y otras shells sigue pendiente de pruebas reales.

## 6. Política de configuración y propiedad de archivos

No existe una política universal de gestión de configuración. **Cada paquete debe declarar explícitamente su política**, según el componente:

- `backup` de pacman para archivos de configuración bajo `/etc` cuando proceda.
- Plantillas o configuración inicial para valores por defecto, sin sobrescribir personalizaciones.
- Bloques administrados delimitados, idempotentes y con marcadores propios para integraciones compartidas.
- Recursos estáticos instalados directamente cuando son propiedad del paquete.
- No editar directamente archivos personales de `$HOME` ni reemplazar configuraciones del usuario.

Para cada archivo instalado, el plan debe aclarar:

1. Quién es su propietario.
2. Si es configuración editable o recurso estático.
3. Qué ocurre al instalar, actualizar, retirar o reinstalar el paquete.
4. Cómo se preservan modificaciones del administrador/usuario.
5. Cómo se revierte una integración sin tocar contenido ajeno.
6. Qué tests automatizados y manuales cubren el ciclo de vida.

Los hooks ALPM deben ser pequeños, idempotentes y limitarse a la responsabilidad del paquete. La política elegida debe aparecer en el README del paquete y en la checklist/tests correspondientes.

## 7. Canales, publicación y pipeline

### 7.1 Canales

| Rama fuente | Canal pacman | Configuración |
|---|---|---|
| `main` | `stable` (`[cambonos]`) | Canal estable. |
| `dev` | `testing` (`[cambonos-testing]`) | Canal de desarrollo/pruebas; deshabilitado por defecto en la configuración distribuida. |

Los canales se validan, construyen y publican de forma independiente a partir de snapshots Git fijados al inicio del workflow. Es válido que un paquete tenga versiones distintas en `stable` y `testing`.

### 7.2 Flujo de CI/CD

`.github/workflows/package-pipeline.yml` contiene cuatro fases principales:

1. **validate:** fija los SHA de `dev` y `main`, ejecuta tests, comprueba los keyrings públicos entre ramas y valida cada snapshot frente al manifiesto publicado de su propio canal.
2. **build:** construye `testing` y `stable` en matrices independientes, en contenedores Arch Linux desechables y sin secretos de firma.
3. **signing:** valida artefactos, importa la subclave operativa, firma paquetes y bases de datos, genera índices/manifiestos y ensambla el sitio completo. Solo este job accede al entorno protegido `package-signing`.
4. **publish:** despliega el sitio completo del mirror en GitHub Pages.

Los paquetes se construyen individualmente en contenedores Arch Linux. La imagen base se fija por digest para `linux/amd64`, pero el sistema se actualiza desde los repositorios rolling de Arch en cada ejecución. `makedepends` y, si existe `check()`, `checkdepends` se instalan; `depends` no se instala automáticamente en el entorno de construcción.

### 7.3 Rolling-release y reproducibilidad

La política acordada **no exige reproducibilidad bit a bit**. En cada publicación se reconstruyen los paquetes con las versiones disponibles en ese momento en los repositorios rolling de Arch. Se prioriza mantener los paquetes actualizados y alineados con el modelo rolling-release.

El riesgo de que el mismo código fuente produzca binarios diferentes por cambios del entorno es conocido y aceptado. No planificar un sistema de congelación del entorno ni reproducibilidad bit a bit como requisito, salvo que aparezca un problema grave y se reabra explícitamente la decisión.

Se mantiene trazabilidad, aislamiento, hashes y firmas. `SOURCE_DATE_EPOCH` deriva del último commit que modificó el directorio del paquete; normaliza marcas temporales, pero no garantiza reproducibilidad bit a bit.

## 8. Versionado: regla obligatoria

> **Cualquier cambio en cualquier archivo que forme parte de un paquete debe incluir un incremento de `pkgrel` o `pkgver` en su PKGBUILD. Sin ese incremento, el pipeline rechaza el cambio.**

Esto incluye cambios en:

- PKGBUILD y scripts `.install`.
- Recursos de `files/`.
- Configuraciones, hooks, plantillas, fuentes, imágenes y licencias incluidas en el paquete.
- Cualquier otro archivo que cambie el contenido/fuente empaquetada.

No confundir con cambios exclusivos de tests/documentación del repositorio que no forman parte del paquete. Si el cambio afecta al comportamiento o contrato del paquete, normalmente también debe actualizarse su documentación y sus tests aunque esos archivos no estén dentro del paquete.

Reglas implementadas:

- Cambio de fuente sin incremento de versión: rechazado.
- Retroceso de versión según `vercmp`: rechazado.
- Paquete nuevo o eliminado: permitido conforme al manifiesto/pipeline.
- Reconstrucción de la misma fuente y versión con SHA256 binario diferente: permitida por el entorno rolling.
- `source_hash` controla la política de versionado; `package_hash` identifica/verifica el artefacto publicado.
- `stable` y `testing` se comparan por separado.

**Toda planificación que cambie un paquete debe incluir explícitamente:** versión actual, incremento propuesto de `pkgrel`/`pkgver`, archivos que lo requieren y motivo.

## 9. Firma, confianza y recuperación

### 9.1 Decisiones acordadas

- Se utiliza **una única clave de firma** para `stable` y `testing`.
- La clave primaria se conserva offline.
- La subclave operativa se usa en GitHub Actions desde el entorno protegido `package-signing`.
- Los jobs de construcción no reciben secretos de firma.
- El entorno `package-signing` está limitado a las ramas `dev` y `main`, mantenidas por tres contribuidores de máxima confianza.
- Los archivos públicos del keyring (`cambonos.gpg`, `cambonos-trusted`, `cambonos-revoked`) deben ser idénticos entre `dev` y `main`; el pipeline comprueba esa igualdad byte a byte.
- Esta igualdad del keyring es intencionada: si cambian las claves, el material actualizado debe distribuirse desde el primer momento en ambos canales.
- No almacenar claves privadas en Git.

No asumir que existen reglas adicionales de protección de ramas en GitHub: la información confirmada es la restricción del entorno `package-signing` y el control de los tres contribuidores. Verificar la configuración real antes de afirmar algo más.

### 9.2 Rotación

- **Rotación periódica:** añadir las nuevas claves al paquete `cambonos-keyring`, firmado por la clave anterior.
- **Compromiso de la subclave de firma:** publicar una actualización con una nueva clave y revocar la antigua. Detener la publicación y seguir el procedimiento de recuperación documentado.
- **Compromiso de la clave primaria:** establecer una nueva cadena de confianza. Se publicará `cambonos-keyring` con la nueva cadena y una ISO nueva que la incorpore. Se acepta que algunos equipos no podrán validar automáticamente la transición; el usuario tendrá que actualizar manualmente la confianza.

No diseñar una rotación como si el keyring pudiera actualizarse desde un repositorio cuya firma ya no es confiable. El bootstrap y la recuperación fuera de banda son parte del problema.

### 9.3 Bootstrap de instalación

Como el repositorio remoto exige `SigLevel = Required TrustedOnly`, la instalación nueva debe establecer primero la confianza local:

1. Inicializar el keyring de pacman.
2. Instalar `cambonos-keyring` desde un medio local confiable.
3. Ejecutar `pacman-key --populate cambonos`.
4. Instalar `cambonos-repo`.
5. Habilitar/sincronizar el repositorio remoto.

No descargar el primer `cambonos-keyring` desde el mismo repositorio cuya firma depende de esa clave.

## 10. Estado de versiones publicadas conocido (6 de noviembre de 2026)

Los siguientes datos se extrajeron de `cambonos.db`, `cambonos-testing.db` y sus `.sig` facilitados en la conversación. Son una **instantánea histórica**, no una consulta en vivo. Volver a descargar/consultar las bases antes de tomar decisiones de promoción.

| Paquete | `stable` publicado | `testing` publicado |
|---|---:|---:|
| `cambonos-branding` | `0.1.0-3` | `0.1.1-3` |
| `cambonos-fastfetch` | `0.1.0-10` | `0.1.0-14` |
| `cambonos-keyring` | `0.1.0-2` | `0.1.0-3` |
| `cambonos-release` | `0.1.0-4` | `0.1.0-8` |
| `cambonos-repo` | `0.1.0-2` | `0.1.0-2` |
| `cambonos-shell-prompt` | No publicado | `0.1.0-4` |
| `cambonos-zsh` | No publicado | `0.1.0-1` |

Observaciones de esa instantánea:

- `testing` contenía los siete paquetes y sus versiones coincidían con los PKGBUILD de la instantánea de código inspeccionada.
- `stable` contenía cinco paquetes; sus versiones eran anteriores para branding, fastfetch, keyring y release, y no incluía `cambonos-shell-prompt` ni `cambonos-zsh`.
- Las fechas de construcción en metadatos de `stable` eran del 4 de noviembre; `testing` incluía construcciones del 5 y 6 de noviembre.
- Los archivos `.sig` estaban presentes y señalaban la huella `3D25435E6225B152D1C67935A317EFDA327F34A2`.
- En el entorno de análisis de esa conversación GPG no pudo verificar criptográficamente las firmas porque no estaba importada la clave pública (`NO_PUBKEY`). Esto no prueba que las firmas sean inválidas; solo que la verificación quedó pendiente.
- Los metadatos mostraban `Unknown Packager`; revisar si es un valor esperado de la herramienta de construcción o un detalle de empaquetado que convenga corregir.

No inferir que `stable` está atrasado por error: puede ser una promoción deliberadamente pendiente. La política de promoción debe confirmarse con el responsable.

## 11. Documentación, tests y criterios de aceptación

**Todo cambio de paquete debe incluir la actualización de la documentación y los tests que sean necesarios.** No considerar terminado un cambio que solo modifica el PKGBUILD o el recurso sin actualizar el contrato documentado.

Cada paquete debe mantener un README que explique, al menos:

- Propósito y límites de responsabilidad.
- Contenido instalado y rutas.
- Dependencias y dependencias opcionales.
- Política de configuración/propiedad de archivos.
- Comportamiento en instalación, actualización, eliminación y reinstalación.
- Integración con otros paquetes.
- Comprobaciones manuales y automatizadas.
- Limitaciones conocidas y estado de validación.

La checklist global `docs/PACKAGE-TEST-CHECKLIST.md` debe cubrir pruebas específicas por paquete. Añadir o adaptar tests para cambios de comportamiento, rutas, archivos, hooks, dependencias, compatibilidad, actualizaciones y desinstalación.

### 11.1 Matriz mínima de validación al planificar

Para cada cambio, decidir cuáles aplican y añadir casos explícitos:

- Construcción real con `makepkg` en entorno Arch limpio.
- Validación de PKGBUILD y dependencias (`namcap` cuando proceda).
- Instalación limpia y comprobación de archivos (`pacman -Qkk`, listado del paquete).
- Actualización desde la versión publicada anterior.
- Preservación de cambios del administrador y tratamiento de `.pacnew`/`.pacsave`.
- Reinstalación, eliminación y limpieza de recursos propios sin borrar datos ajenos.
- Idempotencia de scripts/hooks e integración de shells.
- Compatibilidad con shells/terminales relevantes y sesiones SSH cuando proceda.
- Validación de sintaxis y formato de configuraciones (JSONC, TOML, XML, shell, etc.).
- Pruebas de firma, keyring y bootstrap cuando se afecte a repositorios/confianza.
- Actualización del README del paquete, documentación general y checklist.
- Suite completa de tests y validación del pipeline.

Los tests unitarios/estáticos no sustituyen pruebas reales en Arch ni validación a largo plazo.

## 12. Estado técnico de referencia y notas conocidas

La última instantánea de `cambonos-packages` inspeccionada en este hilo era `dev`, commit `150cb46` (`style(packages): refresh mirror pages`), con worktree limpio en el archivo exportado. Las versiones de sus siete PKGBUILD eran:

| Paquete | Versión fuente en esa instantánea |
|---|---:|
| `cambonos-branding` | `0.1.1-3` |
| `cambonos-fastfetch` | `0.1.0-14` |
| `cambonos-keyring` | `0.1.0-3` |
| `cambonos-release` | `0.1.0-8` |
| `cambonos-repo` | `0.1.0-2` |
| `cambonos-shell-prompt` | `0.1.0-4` |
| `cambonos-zsh` | `0.1.0-1` |

Notas que deben tratarse como contexto histórico y revalidarse contra HEAD actual:

- Fastfetch usa JSONC. Se detectó una coma final en el objeto `display`; se consideró no crítica y estaba previsto corregirla en una versión posterior. No confundir ese detalle conocido con un error de JSON estricto: validar con parser JSONC o test apropiado.
- La paleta del logo Fastfetch es de cuatro colores por legibilidad; no forzar los seis colores.
- Starship mantiene `right_format` por decisión explícita. En Bash necesita un mecanismo adicional (Ble.sh o Flyline) para renderizar prompt derecho; no cambiar a `$fill` sin pruebas y decisión nueva.
- La compatibilidad visual del prompt en distintas shells, tamaños de terminal, SSH y edición de línea requiere pruebas reales.
- El branding ha añadido recursos PNG junto a SVG; dimensiones revisadas: icono 1024×1024 y wordmark 3792×1024. Los recursos deben documentarse y probarse juntos.
- La restauración de `/etc/lsb-release` en `cambonos-release` se diseñó de forma conservadora para no pisar cambios ajenos; conservar pruebas de instalación/actualización/eliminación.

## 13. Reglas operativas para el agente planificador

Al recibir una solicitud de cambio:

1. **Inspeccionar primero:** rama/HEAD/worktree, archivos relevantes, README del paquete, PKGBUILD, scripts/hooks, tests, checklist, documentación y pipeline. No basarse únicamente en este resumen.
2. **Delimitar alcance:** identificar paquete(s), recursos, scripts, dependencias, consumidores y repositorios afectados. Mantener separados web, mirror, instalador e ISO.
3. **Respetar decisiones confirmadas:** no reabrir por iniciativa propia el modelo híbrido, la clave única, la igualdad de keyrings, el enfoque rolling, la paleta Fastfetch simplificada ni el `right_format` actual.
4. **Declarar incertidumbres:** distinguir hechos del repositorio, decisiones del propietario, inferencias y puntos que necesitan confirmación. No inventar estado de publicación ni capacidades de herramientas.
5. **Versionado obligatorio:** incluir incremento de `pkgrel`/`pkgver` en todo paquete cuyo contenido cambie. Recordar que sin ello falla el pipeline.
6. **Plan de archivos:** listar cada archivo que se modificará y el motivo. Incluir README, tests y checklist necesarios.
7. **Plan de pruebas:** indicar pruebas unitarias, estáticas, construcción, instalación, actualización, eliminación y validaciones de largo plazo aplicables. Diferenciar las ejecutadas de las pendientes.
8. **Seguridad:** cualquier cambio de firma, keyring, repositorios, pipeline o workflow protegido requiere análisis explícito de amenazas, bootstrap y recuperación.
9. **Compatibilidad:** preservar configuraciones del administrador/usuario; documentar claramente cualquier cambio incompatible o migración.
10. **No implementar sin autorización:** el rol de este archivo es orientar la planificación. No asumir que una petición de planificar autoriza editar, publicar, firmar o desplegar.

### Formato recomendado para cada plan

- **Objetivo y motivación**
- **Estado actual comprobado** (rama/commit/archivos/paquetes)
- **Decisiones del proyecto aplicables**
- **Alcance y no-alcance**
- **Diseño propuesto y alternativas**
- **Archivos afectados**
- **Impacto en dependencias e integración**
- **Incremento `pkgver`/`pkgrel` por paquete**
- **Cambios de README/documentación/checklist**
- **Tests y validaciones** (automatizadas y manuales)
- **Riesgos, compatibilidad, rollback y cuestiones abiertas**
- **Criterios de aceptación**

---

**Principio rector:** Arch Linux permanece como base; CambonOS aporta una capa modular de personalización y facilitación. Cada paquete debe hacer bien una cosa, respetar la propiedad de las configuraciones y demostrar su comportamiento mediante documentación y pruebas. El sistema debe seguir siendo mantenible, transparente y coherente con el modelo rolling-release.
