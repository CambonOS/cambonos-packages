# cambonos-pacman

Configuración de Pacman y de los repositorios de paquetes CambonOS.

## Funcionalidad

- Configura los canales `stable` y `testing`.
- Exige la verificación de firmas para los repositorios CambonOS.
- Integra las opciones y los repositorios mediante archivos administrados incluidos
  desde `/etc/pacman.conf`.
- Conserva la configuración local ajena a los bloques que administra el paquete.
- Mantiene la transición desde el paquete anterior `cambonos-repo`.

El canal que se configura depende del paquete construido para cada snapshot: `dev`
corresponde a `testing` y `main` a `stable`. El material de confianza lo proporciona
`cambonos-keyring`.

## Dependencias

`bash`, `coreutils`, `diffutils`, `gawk` y `cambonos-keyring`.
