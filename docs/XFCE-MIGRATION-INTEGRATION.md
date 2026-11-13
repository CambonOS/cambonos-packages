# Integración externa de la migración XFCE

Este cambio implementa la arquitectura de paquetes en `cambonos-packages`. No modifica
`cambonos-installer` ni `cambonos-mkiso`: sus repositorios no forman parte del snapshot
Git adjunto a esta tarea. La integración externa debe hacerse con sus propios snapshots
actuales y parches separados, sin inferir commits ni editar copias parciales.

## Contrato del instalador

1. Cuando el usuario seleccione XFCE, instalar `cambonos-xfce` desde el repositorio
   CambonOS del canal correspondiente.
2. En instalaciones nuevas, seleccionar la sesión `cambonos-xfce` como sesión por
   defecto de LightDM. No forzar la sesión por defecto en sistemas ya instalados.
3. No instalar paquetes de escritorio individualmente con `yay -Sy` ni ejecutar
   `archie.sh`; la resolución debe realizarse mediante la transacción normal de Pacman.
4. Mantener la ruta Qtile actual sin cambios en esta migración.

## Contrato de mkiso

1. Garantizar que el repositorio CambonOS del canal de la ISO contiene `cambonos-xfce`,
   `cambonos-xfce-conf` y las dependencias CambonOS necesarias antes de instalar XFCE.
2. Eliminar el clonado/copiado de `Cambon18/xfce` y la ejecución de su `archie.sh` sólo
   cuando la instalación mediante `cambonos-xfce` haya superado la validación de ISO.
3. No retirar todavía la integración heredada del ISO hasta completar pruebas de
   instalación limpia, actualización y selección de sesión.

## Migración y límites

- `cambonos-xfce` compone `cambonos-base`, `cambonos-xfce-conf` y las aplicaciones
  generales seleccionadas.
- `cambonos-graphical-base` contiene la infraestructura común Xorg, Thunar, GVFS,
  audio, red, Bluetooth, portales, credenciales y utilidades compartidas.
- `cambonos-xfce-conf` proporciona los valores XDG globales y la sesión dedicada.
  `~/.config` sigue prevaleciendo; no hay migración automática de perfiles existentes.
- Los repositorios externos no deben eliminarse hasta que las pruebas de ISO limpia,
  upgrade desde XFCE heredado y recuperación de fallos estén completadas.
- La posible coexistencia de agentes Polkit en XFCE queda como validación funcional;
  esta implementación no desactiva entradas de autoinicio de XFCE preventivamente.

La checklist funcional de `PACKAGE-TEST-CHECKLIST.md` contiene los puntos que deben
verificarse en una ISO real antes de promover el cambio a `main`.
