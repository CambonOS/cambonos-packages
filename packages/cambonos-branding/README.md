# cambonos-branding

Recursos visuales oficiales de CambonOS para aplicaciones, instaladores y componentes del escritorio.

## Funciones

- Iconos y logotipos en SVG y PNG, incluido el icono de 1024x1024 y los recursos usados por Plymouth.
- Fondo 4K y recursos gráficos de la barra de progreso de Plymouth.
- Paleta ANSI de CambonOS aplicada a las consolas virtuales.
- Tema global de CambonOS para `dialog` en `/etc/dialogrc`.
- Predeterminado global de colores para Xfce Terminal cuando está instalado.

La integración de Xfce Terminal modifica solo los valores globales de paleta,
fondo y texto en `/etc/xdg/xfce4/terminal/terminalrc`. Conserva las demás
opciones y las configuraciones de usuario; al desinstalar `xfce4-terminal`
restaura los valores globales anteriores.

## Dependencias

`bash`, `coreutils`, `gawk`, `kbd`.
