# cambonos-base

Metapaquete que instala conjuntamente los componentes generales de la experiencia
CambonOS. No contiene archivos ni ejecuta scripts: su función es agrupar dependencias.

## Componentes

- `cambonos-keyring`: material público de confianza para Pacman.
- `cambonos-pacman`: configuración e integración de los repositorios CambonOS.
- `cambonos-release`: identidad y metadatos de la distribución.
- `cambonos-branding`: recursos gráficos, tipografía y paletas.
- `cambonos-fastfetch`: perfil e integración de Fastfetch.
- `cambonos-shell-prompt`: configuración de Starship.
- `cambonos-zsh`: configuración global y experiencia interactiva de Zsh.

Zsh forma parte de la experiencia base. El instalador decide la shell de inicio de
sesión para las cuentas nuevas; instalar o retirar este metapaquete no cambia la shell
de usuarios existentes.

## Componentes independientes

`cambonos-grub` y `cambonos-plymouth` se instalan por separado porque dependen de las
decisiones de arranque del sistema.

## Dependencias

Las dependencias directas son los siete componentes enumerados arriba. Cada uno conserva
su propio paquete, versión y responsabilidad.
