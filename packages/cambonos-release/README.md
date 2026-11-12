# cambonos-release

Metadatos que identifican el sistema como CambonOS y conservan su base Arch Linux.

## Funcionalidad

- Proporciona la identidad de distribución mediante `os-release` y los metadatos LSB.
- Restaura los archivos de identidad administrados cuando otras transacciones del
  sistema los sustituyen.
- Conserva la identidad previa al retirar el paquete cuando corresponde.

La integración LSB completa requiere que esté instalado el componente que proporciona el
comando `lsb_release`.

## Dependencias

Obligatorias: `bash` y `coreutils`.

Opcionales:
- `lsb-release`: proporciona el comando `lsb_release` con los metadatos de CambonOS.
- `cambonos-fastfetch`: añade el perfil visual y el logotipo de Fastfetch.
