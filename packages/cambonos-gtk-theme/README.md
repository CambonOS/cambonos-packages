# cambonos-gtk-theme

Tema oscuro de CambonOS para GTK 3, GTK 4 y decoraciones de ventanas Xfwm4.
Este documento reúne la documentación del paquete, su estructura, alcance,
limitaciones, construcción y validación. Los recursos de `files/` son el
contenido fuente del paquete; la documentación de desarrollo permanece en el
repositorio y no se instala en el sistema.

**Versión del paquete Arch:** `0.6.2-11`.

**Versión del tema:** `0.6.2`.

## Tema y contenido

El paquete distribuye una única variante seleccionable: `CambonOS-dark`.

Incluye:

- **GTK 3:** hojas de estilo y recursos en `gtk-3.0/`.
- **GTK 4:** hojas de estilo y recursos en `gtk-4.0/`.
- **Xfwm4:** decoraciones de ventanas y recursos XPM en `xfwm4/`.
- **Integración XFCE:** selectores GTK para componentes como el panel y
  Whisker Menu, sujetos a la compatibilidad de cada aplicación.

Los puntos de entrada `gtk.css` y `gtk-dark.css` de GTK 3 y GTK 4 utilizan la
misma paleta oscura. No se distribuye una variante clara ni una implementación
GTK 2.

### Estructura del paquete

```text
packages/cambonos-gtk-theme/
├── PKGBUILD
├── README.md
└── files/
    ├── CHANGELOG.md
    ├── LICENSE
    ├── src/
    │   └── palette.json
    ├── tools/
    │   ├── build-theme.py
    │   └── validate-theme.py
    └── themes/
        └── CambonOS-dark/
            ├── index.theme
            ├── gtk-3.0/
            ├── gtk-4.0/
            └── xfwm4/
```

`src/palette.json` es la paleta oscura canónica. El generador
`tools/build-theme.py` produce los archivos `colors-dark.css` para GTK 3 y
GTK 4 a partir de ella. No se deben editar manualmente esos archivos
generados: los cambios de color deben realizarse en la paleta y regenerarse
mediante la herramienta.

`tools/validate-theme.py` realiza comprobaciones estructurales de las hojas de
estilo y los recursos Xfwm4. Estas comprobaciones detectan problemas de
estructura, pero no sustituyen las pruebas visuales en una sesión real.

## Compatibilidad y limitaciones

- **GTK 3:** se incluyen hojas de estilo y recursos propios.
- **GTK 4:** se incluyen hojas de estilo y recursos propios para aplicaciones
  GTK 4 compatibles.
- **libadwaita:** algunas aplicaciones pueden imponer su propia apariencia y
  no respetar temas GTK externos. No se garantiza que adopten completamente
  los estilos de `CambonOS-dark`.
- **GTK 2:** no está soportado; no se incluye `gtk-2.0/gtkrc`.
- **Xfwm4:** se incluyen `themerc` y recursos gráficos. La validación
  estructural no demuestra por sí sola su representación correcta; debe
  comprobarse en la versión de XFCE/Xfwm4 objetivo.
- **Iconos y cursores:** son componentes independientes y requieren sus
  propios temas o paquetes.
- **Qt:** no está cubierto por este paquete; requiere una solución específica,
  por ejemplo un tema Qt o Kvantum.
- **Otros elementos del escritorio:** sonidos, fondos de pantalla, greeter,
  pantalla de bloqueo y recursos de inicio de sesión quedan fuera de su
  alcance.

La presencia de recursos GTK 3 y GTK 4 no implica que todas las aplicaciones
usen cada selector o estilo de la misma manera. El resultado depende también
de la versión de GTK, XFCE, Xfwm4 y de las decisiones visuales de cada
aplicación.

## Construcción e instalación

Este directorio es un paquete Arch gestionado por el repositorio CambonOS.
El directorio `files/` contiene el payload fuente consumido por el `PKGBUILD`;
no es un paquete independiente y no contiene otro `PKGBUILD` ni `.SRCINFO`.

Durante `build()`, el `PKGBUILD` copia el contenido de `files/` al directorio
de construcción, genera los CSS y ejecuta el validador. Las herramientas de
construcción se utilizan en ese proceso y no se instalan en el sistema.

`package()` instala únicamente el directorio `CambonOS-dark` en
`/usr/share/themes/` y la licencia en
`/usr/share/licenses/cambonos-gtk-theme/LICENSE`. El README, el changelog,
la paleta fuente y las herramientas de desarrollo permanecen en el
repositorio y no forman parte del paquete instalado.

## Activación en XFCE

El paquete no cambia la configuración global de GTK ni fuerza la selección
del tema. Para activarlo, selecciona `CambonOS-dark` en:

- **Apariencia → Estilo**, para el tema de aplicaciones GTK.
- **Gestor de ventanas → Estilo**, para las decoraciones Xfwm4.

También se puede seleccionar mediante `xfconf-query`:

```bash
xfconf-query -c xsettings -p /Net/ThemeName -s CambonOS-dark
xfconf-query -c xfwm4 -p /general/theme -s CambonOS-dark
```

La selección de GTK y la de Xfwm4 son independientes. El paquete conserva el
nombre `CambonOS-dark` para mantener la compatibilidad con configuraciones y
componentes existentes.

## Desarrollo y validación

Desde `packages/cambonos-gtk-theme/files/`, ejecuta:

```bash
python tools/build-theme.py
python tools/validate-theme.py
```

El generador actualiza los archivos CSS derivados de `src/palette.json`; el
validador comprueba la estructura de los recursos. Ejecuta ambos comandos
después de modificar la paleta o los recursos del tema.

### Comprobaciones en tiempo de ejecución

Las comprobaciones automatizadas no sustituyen la validación en una sesión
XFCE real. Para aceptar cambios visuales, comprueba como mínimo:

1. Seleccionar `CambonOS-dark` en Apariencia y verificar aplicaciones GTK 3.
2. Verificar por separado aplicaciones GTK 4 compatibles.
3. Revisar Thunar, Mousepad, XFCE Terminal, Ristretto, XFCE Settings, el panel
   y Whisker Menu cuando estén disponibles en el entorno de prueba.
4. Comprobar foco, selección, estados deshabilitados, hover, pressed y
   backdrop en controles relevantes.
5. Revisar contraste y legibilidad de texto, menús, tooltips, entradas y
   controles, incluidas las superficies translúcidas.
6. En Xfwm4, comprobar ventanas activas e inactivas y los estados de los
   botones de menú, minimizar, maximizar/restaurar, cerrar, sombrear y fijar.
7. Comprobar bordes, esquinas, título y redimensionado de ventanas.
8. Registrar la versión de CambonOS, GTK, XFCE y Xfwm4 utilizada en la
   validación.

Las aplicaciones libadwaita deben evaluarse como una excepción conocida: que
no respeten el tema externo no implica necesariamente un defecto del paquete.

## Criterio de alcance

Este paquete proporciona el tema GTK y las decoraciones Xfwm4 descritas
anteriormente. No pretende ser un paquete completo de personalización del
escritorio. Los temas de iconos, cursores, Qt, sonidos, fondos, greeter y
pantalla de bloqueo deben gestionarse mediante componentes independientes.
