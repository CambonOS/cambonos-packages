# cambonos-plymouth

Tema gráfico de arranque de CambonOS e integración con mkinitcpio.

## Funciones

- Tema Plymouth con logo, fondo y recursos de barra proporcionados por `cambonos-branding`.
- El icono fuente de 1024x1024 se representa a 512 px en `1920x1080` y escala proporcionalmente hasta 1024 px en `3840x2160`.
- La barra escala proporcionalmente a la resolución, tomando `1920x1080` como referencia.
- Integración con las imágenes initramfs.
- Selección del tema y actualización de presets existentes.

## Dependencias

`plymouth`, `mkinitcpio>=36`, `cambonos-branding`.
