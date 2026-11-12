# cambonos-plymouth

Tema gráfico de arranque de CambonOS e integración con `mkinitcpio`.

## Funcionalidad

- Proporciona el tema Plymouth con identidad y recursos gráficos de CambonOS.
- Integra Plymouth en las imágenes initramfs mediante la configuración de `mkinitcpio`.
- Mantiene la selección del tema y actualiza los presets existentes cuando corresponde.

El fondo se adapta a la resolución sin deformarse; el grupo del logotipo y la barra
conserva su proporción y centrado. El paquete instala los recursos gráficos junto
al tema Plymouth.

## Dependencias

`plymouth` y `mkinitcpio>=36`.
