# cambonos-grub

Configuración y tema visual de GRUB para CambonOS.

## Funcionalidad

- Configuración predeterminada y tema gráfico de CambonOS.
- Iconos para sistemas operativos detectados por GRUB.
- Integración con `os-prober` para configuraciones multiboot.
- Regeneración del menú después de cambios de kernel mediante un hook de Pacman.

El paquete proporciona la configuración global en `/etc/default/grub.d/`. Las opciones
locales del administrador deben mantenerse al adaptar esa configuración.

## Dependencias

`bash`, `grub>=2:2.16` y `os-prober`.
