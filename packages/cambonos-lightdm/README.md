# cambonos-lightdm

Configuración de LightDM y Slick Greeter para la pantalla de inicio de sesión de
CambonOS.

## Funcionalidad

- Selecciona `lightdm-slick-greeter` como greeter.
- Muestra los usuarios disponibles y desactiva el acceso manual y las sesiones de
  invitado.
- Configura el fondo, NumLock y la detección automática de HiDPI.
- Selecciona `CambonOS-dark` para Slick Greeter mediante `cambonos-gtk-theme`.

El paquete no instala un entorno de escritorio ni selecciona la sesión del usuario. El
tema GTK configurado aquí afecta únicamente al greeter.

## Activación del servicio

Durante la primera instalación, el scriptlet intenta habilitar `lightdm.service` sin
iniciarlo ni reiniciarlo. Solo lo hace si no existe un `display-manager.service`
seleccionado. Si ya hay otro gestor configurado, conserva esa selección.

Cuando el paquete habilita LightDM automáticamente, registra esa acción en
`/var/lib/cambonos-lightdm/auto-enabled`. Al retirar el paquete, `post_remove`
deshabilita LightDM únicamente si existe ese registro y `display-manager.service` sigue
apuntando a `lightdm.service`. Si el administrador ha seleccionado otro gestor o ha
cambiado el enlace, el paquete no deshabilita el servicio.

Las actualizaciones no vuelven a habilitar el servicio. Para seleccionar LightDM
manualmente, deshabilita primero el gestor actual y ejecuta:

```bash
sudo systemctl enable lightdm.service
```

## Configuración y recursos

Los archivos `/etc/lightdm/lightdm.conf.d/50-cambonos.conf` y
`/etc/lightdm/slick-greeter.conf` están declarados en `backup` en el `PKGBUILD`, por lo
que Pacman conserva las modificaciones locales y utiliza `.pacnew` o `.pacsave` cuando
corresponde. El fondo se instala en `/usr/share/cambonos/lightdm/background.png`.

## Dependencias

`lightdm`, `lightdm-slick-greeter`, `numlockx` y `cambonos-gtk-theme`.

## Licencia

El paquete incluye la licencia GPL-3.0-only. La inclusión de ese archivo no determina
por sí sola la licencia ni los derechos de redistribución del fondo gráfico; estos deben
estar autorizados por sus respectivos titulares.
