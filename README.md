# CambonOS Packages

Repositorio oficial de paquetes de CambonOS y de la infraestructura utilizada para validarlos, construirlos, firmarlos y publicarlos.

CambonOS está basado en **Arch Linux** y sigue su modelo **rolling-release**. Arch proporciona la base del sistema; CambonOS añade paquetes, configuraciones, integración y herramientas propias para facilitar su instalación y administración.

## Ramas y canales

La documentación describe el comportamiento implementado en los archivos versionados del repositorio. Para conocer el estado operativo de una publicación concreta, consulta la ejecución correspondiente de GitHub Actions y el manifiesto publicado.

### Canales

| Rama de origen | Canal pacman | Uso | Estado en la configuración incluida |
|---|---|---|---|
| `main` | `stable` (`[cambonos]`) | Publicación estable | Habilitado |
| `dev` | `testing` (`[cambonos-testing]`) | Desarrollo y pruebas internas | Deshabilitado por defecto |

Ambos canales se construyen de forma independiente desde snapshots Git fijados al comienzo del workflow. Cada publicación reconstruye el conjunto de paquetes de ambos canales y genera el sitio completo. No se conserva el histórico de binarios dentro de cada canal.

El proceso utiliza los repositorios rolling de Arch durante la construcción. Por diseño, no se persigue reproducibilidad bit a bit frente a un entorno congelado: se prioriza reconstruir con las versiones actuales disponibles, conservando trazabilidad, aislamiento, hashes y firmas.

## Catálogo de paquetes

| Paquete | Responsabilidad |
|---|---|
| [`cambonos-branding`](packages/cambonos-branding/README.md) | Recursos gráficos genéricos de CambonOS. |
| [`cambonos-grub`](packages/cambonos-grub/README.md) | Configuración GRUB, multiboot y tema CambonOS derivado de Vimix. |
| [`cambonos-plymouth`](packages/cambonos-plymouth/README.md) | Tema de arranque Plymouth e integración con mkinitcpio. |
| [`cambonos-fastfetch`](packages/cambonos-fastfetch/README.md) | Perfil de Fastfetch e integración automática con shells. |
| [`cambonos-shell-prompt`](packages/cambonos-shell-prompt/README.md) | Configuración e integración de Starship en Zsh, Bash y Fish. |
| [`cambonos-zsh`](packages/cambonos-zsh/README.md) | Configuración global de Zsh y punto de entrada para integraciones. |
| [`cambonos-keyring`](packages/cambonos-keyring/README.md) | Raíz pública de confianza para los repositorios CambonOS en pacman. |
| [`cambonos-release`](packages/cambonos-release/README.md) | Identidad de distribución y metadatos release/LSB. |
| [`cambonos-pacman`](packages/cambonos-pacman/README.md) | Repositorios CambonOS y personalizaciones diferenciales de pacman. |
| `cambonos-installer` | Instalador del entorno live; su fuente y PKGBUILD se mantienen en el repositorio independiente `CambonOS/installer`. |
| `cambonos-mkiso` | Builder y perfil ArchISO; su fuente y PKGBUILD se mantienen en el repositorio independiente `CambonOS/iso`. |

Cada paquete tiene una responsabilidad independiente. `cambonos-zsh` proporciona el cargador global de fragmentos Zsh en `/usr/share/cambonos/zsh/conf.d/`; `cambonos-shell-prompt` y `cambonos-fastfetch` instalan ahí sus fragmentos sin modificar `/etc/zsh/zshrc`. Para bloques de Bash, los componentes utilizan marcadores independientes y el bloqueo compartido `/run/lock/cambonos-shell-integration.lock`. Los metapaquetes futuros, cuando existan, deberán agrupar dependencias; no asumirán la propiedad ni la configuración de los componentes que agrupen.

## Arquitectura del repositorio

```text
cambonos-packages/
├── .github/workflows/
│   └── package-pipeline.yml
├── packages/
│   ├── cambonos-branding/
│   ├── cambonos-grub/
│   ├── cambonos-plymouth/
│   ├── cambonos-fastfetch/
│   ├── cambonos-shell-prompt/
│   ├── cambonos-zsh/
│   ├── cambonos-keyring/
│   ├── cambonos-release/
│   └── cambonos-pacman/
├── scripts/
│   ├── cambonos.py
│   └── cambonos_lib/
├── tests/
├── docs/
│   ├── GPG-SETUP.md
│   ├── IMPLEMENTATION.md
│   └── PACKAGE-TEST-CHECKLIST.md
└── README.md
```

- `packages/`: un directorio por paquete, con `PKGBUILD`, recursos y, cuando corresponda, script `.install`.
- `cambonos-installer` y `cambonos-mkiso` se mantienen en sus repositorios fuente independientes y se incorporan a cada build como snapshots Git temporales.
- `scripts/`: gestor Python para validar, construir, firmar y generar la publicación.
- `tests/`: pruebas automatizadas del gestor y de la integración de repositorio.
- `docs/`: procedimientos y documentación técnica.
- `.github/workflows/`: pipeline CI/CD.

## Construcción y publicación

El workflow `.github/workflows/package-pipeline.yml` se ejecuta en `push` a `dev` o `main` y contiene cuatro jobs:

1. **validate**: fija los SHA de ambas ramas y de los repos externos, ejecuta las pruebas y valida ambos snapshots frente al manifiesto publicado.
2. **build**: construye `testing` y `stable` en matrices independientes, sin secretos de firma.
3. **signing**: valida artefactos, importa la subclave operativa, firma paquetes y bases de datos y ensambla el sitio.
4. **publish**: despliega el artefacto completo en GitHub Pages.

Los paquetes se construyen en contenedores Arch Linux desechables. La imagen base está fijada por digest para `linux/amd64`, pero el sistema del contenedor se actualiza desde los repositorios rolling de Arch en cada ejecución. `depends` no se instala automáticamente en el entorno de construcción; `makedepends` y, si existe `check()`, `checkdepends` sí se instalan.

Las dependencias internas de construcción se ordenan topológicamente. Cada paquete se construye en su propio contenedor.

### Versionado e inmutabilidad

Cualquier cambio en los archivos de un paquete debe incrementar `pkgrel` o `pkgver`.

- Cambio de fuente sin incremento de versión: rechazado.
- Retroceso de versión según `vercmp`: rechazado.
- Paquete nuevo o eliminado: permitido.
- Reconstrucción de la misma fuente y versión con un SHA256 binario diferente: permitida. El entorno rolling puede producir artefactos distintos sin que haya cambiado el contenido fuente.
- `source_hash` determina la política de versionado; `package_hash` verifica la integridad y permite identificar el artefacto concreto publicado.

`stable` y `testing` se comparan de forma independiente. Es válido que un paquete tenga versiones distintas en ambos canales.

Para los dos paquetes externos, el workflow fija `main` para `stable`; para `testing` usa `dev` si existe y, si aún no existe esa rama en el repo fuente, cae a `main`. Reutiliza esos SHA completos durante validación y construcción. El staging rechaza un checkout con otro origen, otro SHA, cambios locales o symlinks que escapen del repo; registra repositorio/commit en el manifiesto de build. El contenido staged entra en `source_hash`, por lo que un cambio upstream sin aumentar `pkgrel`/`pkgver` bloquea la publicación. Los repositorios no se clonan dentro de `packages/` ni se mantienen copias sincronizadas manualmente.

`SOURCE_DATE_EPOCH` se deriva del último commit que modificó el directorio del paquete. Esto normaliza marcas temporales, pero **no pretende garantizar reproducibilidad bit a bit** ante cambios del entorno rolling.

## Firma y confianza

La política utiliza una única clave de firma para `stable` y `testing`.

- La clave primaria se conserva offline.
- La subclave de firma se utiliza en GitHub Actions mediante el entorno protegido `package-signing`.
- Solo los jobs de firma reciben los secretos; los jobs de construcción no.
- El entorno `package-signing` está limitado a `dev` y `main`, ramas mantenidas por tres contribuidores de confianza.
- Los tres archivos públicos del keyring (`cambonos.gpg`, `cambonos-trusted`, `cambonos-revoked`) deben ser idénticos entre `dev` y `main`; el job `validate` comprueba esa igualdad byte a byte antes de construir.
- Cada snapshot se valida contra el manifiesto anterior de su propio canal. La igualdad del keyring público entre ramas es una comprobación adicional y explícita; no implica que los demás paquetes o sus versiones deban coincidir.
- Nunca se deben almacenar claves privadas en Git.

La firma demuestra que el artefacto fue firmado por la clave de CambonOS; no demuestra por sí sola que el código sea benigno. La revisión del código y la protección de las ramas siguen siendo controles necesarios.

Consulta [`docs/GPG-SETUP.md`](docs/GPG-SETUP.md) para la preparación de claves y secretos.

### Rotación y recuperación

- **Rotación ordinaria:** distribuir el nuevo material de clave en un paquete `cambonos-keyring` firmado por la clave anterior, manteniendo la transición verificable por los clientes existentes.
- **Compromiso de la subclave:** detener publicaciones, preparar una nueva clave de firma y revocar la anterior. Si todavía es seguro confiar en la anterior, utilizarla para autenticar la transición. Si no lo es, se requiere un canal de recuperación externo.
- **Compromiso de la clave primaria:** establecer una nueva cadena de confianza. Los equipos que no puedan autenticarla deberán actualizar manualmente su confianza; se publicará también una ISO nueva con la cadena actualizada.

## Bootstrap en una instalación nueva

El repositorio remoto exige firmas (`SigLevel = Required TrustedOnly`). Por ello, el instalador/ISO debe establecer primero la confianza local:

1. Inicializar el keyring de pacman.
2. Instalar `cambonos-keyring` desde el medio local confiable.
3. Ejecutar `pacman-key --populate cambonos`.
4. Instalar `cambonos-pacman`.
5. Habilitar y sincronizar el repositorio remoto.

No se debe intentar descargar el primer `cambonos-keyring` desde el repositorio que depende de ese mismo keyring para ser verificado.

## Política de configuración

Cada paquete define explícitamente cómo gestiona sus archivos. No existe una política universal obligatoria.

| Tipo de contenido | Política posible |
|---|---|
| Recursos estáticos propiedad del paquete | Instalación directa en ubicaciones de recursos compartidos. |
| Configuración editable en `/etc` | `backup` de pacman y resolución mediante `.pacnew`, cuando proceda. |
| Configuración compartida con el administrador | Bloques delimitados y gestión idempotente, sin modificar contenido ajeno. |
| Valores iniciales de usuario | Plantillas o primera ejecución, sin sobrescribir configuraciones personales. |
| Archivos personales | No modificarlos directamente. |

La elección debe documentarse en el README del paquete y reflejarse en sus pruebas. Los hooks ALPM deben ser pequeños, idempotentes y limitarse a la responsabilidad del paquete.

## Uso local

Requisitos generales: Python 3.10+, Bash y GPG para validación estática; Docker para construcción; herramientas Arch/pacman para las comprobaciones específicas.

```bash
# Pruebas automatizadas del gestor
python3 -m unittest discover -s tests -v

# Ayuda del CLI
python3 scripts/cambonos.py --help

# Validar snapshot testing
python3 scripts/cambonos.py validate \
  --source-root . \
  --channel testing \
  --branch dev

# Construir snapshot testing
python3 scripts/cambonos.py build \
  --source-root . \
  --channel testing \
  --branch dev \
  --commit "$(git rev-parse HEAD)" \
  --output ./build-testing
```

La firma y el ensamblado final se realizan en el job protegido de GitHub Actions. No se recomienda exportar la clave privada al equipo local de construcción.

## Pruebas de paquetes

La checklist de validación manual y de integración está en [`docs/PACKAGE-TEST-CHECKLIST.md`](docs/PACKAGE-TEST-CHECKLIST.md). Incluye construcción, instalación, actualización, configuración, hooks, eliminación y comprobaciones de regresión por paquete.

## Alcance y validación operativa

La suite automatizada valida el tooling del repositorio y sus políticas, pero no sustituye la construcción real con `makepkg`, la instalación en una máquina Arch ni las pruebas de integración de cada paquete. La validación de una publicación debe apoyarse en los logs de GitHub Actions, los artefactos generados y el manifiesto firmado.

El pipeline usa una imagen Arch fijada por digest, pero actualiza el entorno dentro del contenedor desde los repositorios rolling. Por tanto, no garantiza reproducibilidad binaria entre fechas distintas.

La recuperación tras el compromiso de la clave primaria requiere establecer una nueva raíz de confianza. Los clientes que no puedan autenticar esa transición necesitarán intervención mediante un canal externo confiable.

La política de configuración se define por paquete y debe documentarse junto a sus pruebas. El equipo responsable del diseño mantiene y valida visualmente los recursos de identidad; este repositorio se ocupa de distribuir los recursos aprobados y verificar su empaquetado e integración en las rutas declaradas.

## Licencia

Consulta [`LICENSE`](LICENSE) y las licencias incluidas por cada paquete.
