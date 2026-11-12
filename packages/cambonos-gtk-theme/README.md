# cambonos-gtk-theme

Temas oscuros de CambonOS para GTK 3, GTK 4 y decoraciones de ventanas Xfwm4. El paquete
genera tres perfiles seleccionables desde una paleta y una plantilla comunes.

## Variantes

| Tema | Opacidad de ventana | Perfil |
|---|---:|---|
| `CambonOS-dark` | 98 % | Conservador y predeterminado. |
| `CambonOS-dark-balanced` | 88 % | Equilibrado. |
| `CambonOS-dark-transparent` | 78 % | Mayor transparencia. |

Las tres variantes comparten colores RGB, geometría, widgets e imágenes Xfwm4. Cambia la
política de transparencia de las superficies; textos e indicadores conservan el
contraste previsto. En Xfwm4, las ventanas activas utilizan el turquesa `#019FA7` y las
inactivas el tono atenuado `#397B82`.

## Fuente y generación

`files/src/palette.json` contiene la paleta canónica y `files/themes/CambonOS-dark/` es
la plantilla. Esta última no es una cuarta variante ni se instala directamente.

El `PKGBUILD` ejecuta `files/tools/build-theme.py` y `files/tools/validate-theme.py`;
después instala únicamente las tres variantes generadas en `/usr/share/themes/`.

Para generar y validar manualmente desde `packages/cambonos-gtk-theme/files/`:

```bash
python tools/build-theme.py
python tools/validate-theme.py
```

La política de opacidad y las reglas para modificar la paleta están documentadas en
[OPACITY-POLICY.md](files/OPACITY-POLICY.md). El historial de cambios se conserva en
[CHANGELOG.md](files/CHANGELOG.md).

## Activación en XFCE

Selecciona la misma variante de forma independiente en **Apariencia → Estilo** (GTK) y
**Gestor de ventanas → Estilo** (Xfwm4). Por ejemplo:

```bash
xfconf-query -c xsettings -p /Net/ThemeName -s CambonOS-dark-balanced
xfconf-query -c xfwm4 -p /general/theme -s CambonOS-dark-balanced
```

Sustituye el nombre por `CambonOS-dark` o `CambonOS-dark-transparent` para elegir otro
perfil.

## Compatibilidad y límites

- Incluye estilos y recursos para GTK 3, GTK 4 y Xfwm4.
- GTK 2 no está soportado.
- Algunas aplicaciones basadas en libadwaita pueden imponer su propia apariencia y no
  respetar completamente temas GTK externos.
- La transparencia hacia el escritorio depende del compositor y de su soporte RGBA.
- Iconos, cursores, Qt y otros componentes del escritorio quedan fuera del alcance del
  paquete.

La validación automática comprueba la estructura y los recursos generados, pero no
sustituye las pruebas visuales en una sesión XFCE real. En Xfwm4, selecciona el tema en
**Configuración → Gestor de ventanas → Estilo** y la variante GTK correspondiente en
**Apariencia → Estilo**. Los recursos XPM utilizan la paleta de CambonOS; la validación
estructural no sustituye la comprobación visual en la versión de XFCE/Xfwm4 utilizada.
La [checklist funcional](../../docs/PACKAGE-TEST-CHECKLIST.md) recoge las comprobaciones
pendientes.

## Dependencias de construcción

`python` (utilizado por el generador y el validador del tema).

## Historial reciente

- **0.9.7:** ampliada la cobertura de los selectores de selección por arrastre en XFCE,
  Thunar y GTK; unificados los estilos GTK 3/4 y reforzada su validación.
- **0.9.6:** restaurado el comportamiento de estado y animación de `GtkSpinner` en GTK 3.
- **0.9.5:** mejorada la visibilidad de la selección de iconos en Thunar.
- **0.9.4–0.9.1:** ajustes progresivos de contraste, color y visibilidad del selector
  de arrastre y del resaltado de menús.
- **0.8.0:** introducidos los tres perfiles de opacidad generados desde una paleta y
  plantilla comunes.
