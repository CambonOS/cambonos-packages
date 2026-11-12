# cambonos-gtk-theme

Tema oscuro de CambonOS para GTK 3, GTK 4 y decoraciones de ventanas Xfwm4.
El paquete genera tres variantes seleccionables a partir de una única paleta y
una única plantilla visual. Las variantes comparten RGB, geometría, widgets,
iconografía y recursos Xfwm4; únicamente cambia la política de transparencia
aplicada a los tokens de color.

**Versión del paquete Arch:** `0.8.0-1`.

## Variantes distribuidas

| Tema | Opacidad de ventanas | Multiplicador | Uso previsto |
|---|---:|---:|---|
| `CambonOS-dark-Conservative` | 98 % | 1 | Ventanas prácticamente opacas; transparencia ambiental discreta. |
| `CambonOS-dark-Balanced` | 88 % | 5 | Perfil equilibrado, equivalente al nivel de opacidad de ventana utilizado hasta ahora. |
| `CambonOS-dark-Transparent` | 78 % | 10 | Mayor transparencia del escritorio, manteniendo los textos y controles opacos. |

Cada variante se instala como un tema independiente y seleccionable desde XFCE.
Los nombres se mantienen diferenciados para GTK y Xfwm4, de modo que ambas
selecciones puedan configurarse con el mismo identificador.

## Fuente única y política de transparencia

La estructura de desarrollo es:

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
        └── CambonOS-dark/       # Plantilla canónica, no se instala directamente
            ├── index.theme
            ├── gtk-3.0/
            ├── gtk-4.0/
            └── xfwm4/
```

`src/palette.json` es la única fuente de colores. `themes/CambonOS-dark/` es
la plantilla visual común: contiene los estilos de widgets, los recursos GTK,
las decoraciones Xfwm4 y la estructura de los temas generados. No representa
una cuarta variante ni se instala directamente.

`tools/build-theme.py` genera los tres directorios finales:

- `themes/CambonOS-dark-Conservative/`
- `themes/CambonOS-dark-Balanced/`
- `themes/CambonOS-dark-Transparent/`

La política se define en `VARIANTS` dentro del builder:

```python
VARIANTS = {
    "Conservative": {"window_opacity": 0.98, "multiplier": 1},
    "Balanced": {"window_opacity": 0.88, "multiplier": 5},
    "Transparent": {"window_opacity": 0.78, "multiplier": 10},
}
```

Los valores `alpha` de `palette.json` representan una ponderación de
transparencia adicional respecto a la superficie de ventana, no un alfa CSS
final. `1.0` significa que el token sigue exactamente la opacidad de ventana;
los valores ligeramente inferiores introducen transparencia adicional en
bordes, popovers, tooltips y barras de desplazamiento.

Para cada token con alfa se aplica:

```text
alpha_generado = window_opacity - (1 - alpha_fuente) * multiplier
```

Así, la opacidad de las ventanas coincide exactamente con el 98 %, 88 % y
78 % fijado para cada perfil, mientras que los elementos flotantes mantienen
una transparencia mayor. La transformación se valida antes de generar los
archivos: ningún alfa puede quedar fuera del intervalo 0.0–1.0.

Los colores RGB, textos, acentos, indicadores, estados, geometría y estilos de
widgets no se escalan. Los textos e indicadores mantienen sus colores opacos
para preservar su contraste. No deben introducirse valores RGBA directamente
en `widgets.css`: toda transparencia debe proceder de `palette.json`.

GTK 3 y GTK 4 generan sus propios `colors-dark.css` a partir de la misma
paleta transformada. Las diferencias de selectores y widgets entre ambas
versiones se conservan en sus respectivas hojas `widgets.css`.

### Xfwm4

Las tres variantes reutilizan los mismos recursos gráficos y la misma
configuración `themerc`. La opacidad de las sombras de Xfwm4 es independiente
de los alfas CSS de GTK y no se escala con los multiplicadores. Esta separación
evita confundir la transparencia de superficies GTK con la composición de
sombras y decoraciones de ventana.

## Construcción e instalación

El directorio `files/` contiene el payload fuente consumido por el `PKGBUILD`.
Durante `build()`, se copia a un directorio de construcción, se generan las
tres variantes y se valida cada árbol GTK 3/GTK 4/Xfwm4. `package()` instala
únicamente los tres temas generados en `/usr/share/themes/` y la licencia en
`/usr/share/licenses/cambonos-gtk-theme/LICENSE`.

Para generar y validar manualmente desde `packages/cambonos-gtk-theme/files/`:

```bash
python tools/build-theme.py
python tools/validate-theme.py
```

El builder regenera los directorios de variantes. La plantilla
`themes/CambonOS-dark/` permanece intacta y no debe editarse como si fuera una
variante instalada. Los cambios visuales se realizan en la plantilla y los
cambios de color/transparencia en `src/palette.json`.

## Activación en XFCE

Selecciona el mismo nombre de variante en:

- **Apariencia → Estilo**, para GTK.
- **Gestor de ventanas → Estilo**, para Xfwm4.

También se puede seleccionar mediante `xfconf-query` (ejemplo Balanced):

```bash
xfconf-query -c xsettings -p /Net/ThemeName -s CambonOS-dark-Balanced
xfconf-query -c xfwm4 -p /general/theme -s CambonOS-dark-Balanced
```

Sustituye `Balanced` por `Conservative` o `Transparent` para utilizar otro
perfil. La selección GTK y Xfwm4 sigue siendo independiente.

## Compatibilidad y limitaciones

- **GTK 3 y GTK 4:** se incluyen hojas de estilo y recursos propios.
- **libadwaita:** algunas aplicaciones pueden imponer su propia apariencia y
  no respetar temas GTK externos. No se garantiza que adopten completamente
  los estilos de estas variantes.
- **GTK 2:** no está soportado; no se incluye `gtk-2.0/gtkrc`.
- **Xfwm4:** se incluyen `themerc` y recursos gráficos. La validación
  estructural no demuestra por sí sola su representación correcta; debe
  comprobarse en la versión de XFCE/Xfwm4 objetivo.
- **Compositor:** la transparencia real hacia el escritorio depende de que la
  sesión disponga de composición y soporte RGBA adecuados. Los alfas CSS no
  sustituyen la configuración del compositor.
- **Iconos, cursores, Qt y otros elementos del escritorio:** quedan fuera del
  alcance de este paquete y requieren componentes independientes.

## Validación visual

Las comprobaciones automatizadas no sustituyen las pruebas en una sesión XFCE
real. Para aceptar cambios visuales, comprueba como mínimo:

1. Seleccionar las tres variantes y verificar aplicaciones GTK 3.
2. Verificar por separado aplicaciones GTK 4 compatibles.
3. Revisar Thunar, Mousepad, XFCE Terminal, Ristretto, XFCE Settings, el panel
   y Whisker Menu cuando estén disponibles.
4. Comprobar foco, selección, estados deshabilitados, hover, pressed y backdrop.
5. Revisar contraste y legibilidad de texto, menús, tooltips, entradas y
   controles, especialmente en `CambonOS-dark-Transparent`.
6. En Xfwm4, comprobar ventanas activas/inactivas, botones, bordes, esquinas,
   título y redimensionado en las tres variantes.
7. Confirmar que el compositor está activo y registrar las versiones de
   CambonOS, GTK, XFCE y Xfwm4 utilizadas.

Las aplicaciones libadwaita deben evaluarse como una excepción conocida: que
no respeten el tema externo no implica necesariamente un defecto del paquete.
