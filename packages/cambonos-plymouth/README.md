# cambonos-plymouth

Tema gráfico de arranque de CambonOS e integración con `mkinitcpio`.

## Funcionalidad

- Proporciona el tema Plymouth con identidad y recursos gráficos de CambonOS.
- Integra Plymouth en las imágenes initramfs mediante la configuración de `mkinitcpio`.
- Mantiene la selección del tema y actualiza los presets existentes cuando corresponde.

El fondo se adapta a la resolución sin deformarse; el grupo del logotipo y la barra
conserva su proporción y centrado. Los recursos de marca proceden de
`cambonos-branding`.

## Dependencias

`plymouth`, `mkinitcpio>=36` y `cambonos-branding`.
