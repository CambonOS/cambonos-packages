# cambonos-lightdm

Configuración predeterminada de LightDM y Slick Greeter para CambonOS.

## Responsabilidades

- Selecciona `lightdm-slick-greeter` como greeter de LightDM.
- Muestra los usuarios disponibles y desactiva el acceso manual y las sesiones de invitado.
- Configura el fondo de CambonOS.
- Activa NumLock y la detección automática de HiDPI.
- Selecciona `CambonOS-dark` como tema GTK de Slick Greeter.
- Habilita `lightdm.service` durante la instalación únicamente cuando todavía no existe un `display-manager.service` seleccionado.

El paquete no instala un entorno de escritorio ni selecciona una sesión de usuario. La dependencia `cambonos-gtk-theme` garantiza que el tema `CambonOS-dark` esté instalado para Slick Greeter; esta selección solo afecta a la pantalla de inicio de sesión. XFCE, Qtile y otros escritorios deben proporcionar sus propios ajustes de tema GTK e iconos para la sesión del usuario.

## Dependencias

- `lightdm`
- `lightdm-slick-greeter`
- `numlockx` (necesario para la función `activate-numlock` configurada aquí)
- `cambonos-gtk-theme` (proporciona el tema GTK `CambonOS-dark` seleccionado por Slick Greeter)

## Archivos instalados

| Archivo | Destino |
|---|---|
| `files/lightdm/50-cambonos.conf` | `/etc/lightdm/lightdm.conf.d/50-cambonos.conf` |
| `files/slick-greeter/slick-greeter.conf` | `/etc/lightdm/slick-greeter.conf` |
| `files/branding/background.png` | `/usr/share/cambonos/lightdm/background.png` |

Los dos archivos de configuración de `/etc` están declarados en `backup` en el PKGBUILD. Pacman preservará las modificaciones locales y utilizará `.pacnew`/`.pacsave` según corresponda.

## Activación de LightDM

En la primera instalación, el scriptlet intenta habilitar `lightdm.service` usando `systemctl --root=/ enable lightdm.service`, sin iniciar ni reiniciar el servicio. Si ya existe `/etc/systemd/system/display-manager.service` y no apunta a LightDM, el paquete conserva el enlace existente y muestra un aviso. Para cambiar de gestor, deshabilita primero el gestor anterior y después ejecuta:

```bash
sudo systemctl enable lightdm.service
```

Las actualizaciones no vuelven a habilitar el servicio. La retirada del paquete tampoco lo deshabilita ni elimina manualmente el enlace `display-manager.service`; el administrador debe seleccionar otro gestor antes de reiniciar si retira LightDM.

## Recursos gráficos

El recurso gráfico incluido procede del worktree de CambonOS:

- `background.png`: fondo de pantalla PNG RGB de 3840 × 2160 píxeles.

Se instalan sin conversión en `/usr/share/cambonos/lightdm/`. La configuración de Slick Greeter referencia directamente esos destinos.

## Licencia

El paquete incluye el texto de la licencia GPL-3.0-only en `files/LICENSE`. La inclusión de ese archivo no determina por sí sola la licencia ni los derechos de redistribución de los recursos gráficos; estos deben estar autorizados por sus respectivos titulares.
