# cambonos-branding

Recursos visuales y paletas oficiales de CambonOS para el sistema y sus aplicaciones.

## Funcionalidad

- Logotipos e iconos en SVG y PNG, fondos y recursos gráficos utilizados por otros
  componentes.
- Paleta ANSI de CambonOS para las consolas virtuales.
- Tema global de `dialog` mediante `/etc/dialogrc`.
- Colores predeterminados de Xfce Terminal cuando está instalado.

La integración de Xfce Terminal modifica únicamente los valores globales de paleta,
fondo y texto en `/etc/xdg/xfce4/terminal/terminalrc`. Conserva el resto de opciones y
las preferencias de usuario. Al retirar `xfce4-terminal` o `cambonos-branding`, restaura
los valores globales anteriores que administra.

## Dependencias

`bash`, `coreutils`, `gawk` y `kbd`.
