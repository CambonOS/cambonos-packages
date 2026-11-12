# cambonos-keyring

Material público de confianza que permite a Pacman verificar paquetes y bases de datos
firmados por CambonOS.

## Funcionalidad

- Instala el certificado público, el ownertrust y la información de revocación en
  `/usr/share/pacman/keyrings/`.
- Ejecuta `pacman-key --populate cambonos` después de instalarse o actualizarse, cuando
  el keyring local de Pacman ya está inicializado.

La clave primaria privada y la subclave privada de firma no forman parte del paquete. El
material público debe mantenerse idéntico en los snapshots `dev` y `main`.

## Dependencias

`pacman`.
