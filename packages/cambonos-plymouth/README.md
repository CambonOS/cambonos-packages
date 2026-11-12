# cambonos-plymouth

Tema gráfico de arranque de CambonOS e integración con mkinitcpio.

## Funciones

- Tema Plymouth con logo, fondo y recursos de barra proporcionados por `cambonos-branding`.
- El icono fuente de 1024x1024 se representa a 512 px en `1920x1080` y escala proporcionalmente hasta 1024 px en `3840x2160`.
- El logo y la barra forman un grupo centrado verticalmente, con una separación de 56 px en `1920x1080`.
- El tamaño y la posición vertical escalan solo según la altura; la posición horizontal permanece centrada.
- El fondo se escala para cubrir la pantalla sin deformarse y se recorta desde el centro cuando cambia la relación de aspecto.
- Integración con las imágenes initramfs.
- Selección del tema y actualización de presets existentes.

## Dependencias

`plymouth`, `mkinitcpio>=36`, `cambonos-branding`.
