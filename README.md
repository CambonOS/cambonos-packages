# CambonOS Packages

Repositorio de paquetes propios de **CambonOS**, una distribución basada en Arch Linux.
Aquí se mantienen los componentes que aportan identidad visual, configuración del
sistema y del escritorio, e integración con los repositorios CambonOS.

## Paquetes

| Paquete | Función |
|---|---|
| [cambonos-base](packages/cambonos-base/README.md) | Metapaquete de la experiencia base de CambonOS. |
| [cambonos-branding](packages/cambonos-branding/README.md) | Recursos gráficos y paletas del sistema. |
| [cambonos-gtk-theme](packages/cambonos-gtk-theme/README.md) | Temas GTK 3/4 y Xfwm4 con tres perfiles. |
| [cambonos-fastfetch](packages/cambonos-fastfetch/README.md) | Perfil visual e integración de Fastfetch. |
| [cambonos-shell-prompt](packages/cambonos-shell-prompt/README.md) | Prompt Starship para Bash, Zsh y Fish. |
| [cambonos-zsh](packages/cambonos-zsh/README.md) | Configuración global e integraciones de Zsh. |
| [cambonos-release](packages/cambonos-release/README.md) | Identidad y metadatos de la distribución. |
| [cambonos-pacman](packages/cambonos-pacman/README.md) | Configuración de Pacman y repositorios CambonOS. |
| [cambonos-grub](packages/cambonos-grub/README.md) | Configuración y tema de GRUB. |
| [cambonos-plymouth](packages/cambonos-plymouth/README.md) | Tema de arranque e integración con mkinitcpio. |
| [cambonos-lightdm](packages/cambonos-lightdm/README.md) | Configuración de LightDM y Slick Greeter. |
| [cambonos-graphical-base](packages/cambonos-graphical-base/README.md) | Infraestructura y aplicaciones comunes para escritorios Xorg. |
| [cambonos-xfce-conf](packages/cambonos-xfce-conf/README.md) | Sesión, configuración global y personalización de XFCE. |
| [cambonos-xfce](packages/cambonos-xfce/README.md) | Metapaquete de escritorio XFCE y aplicaciones generales. |
| [cambonos-keyring](packages/cambonos-keyring/README.md) | Material público de confianza para Pacman. |

Los paquetes del instalador y de creación de imágenes se mantienen en sus propios
repositorios: [cambonos-installer](https://github.com/CambonOS/cambonos-installer) y
[cambonos-mkiso](https://github.com/CambonOS/cambonos-mkiso).

## Organización

- `packages/`: fuentes, recursos y recetas de construcción.
- `scripts/`: herramientas de validación, planificación, compilación, recuperación y
  publicación.
- `tests/`: pruebas de contratos y comprobaciones transversales.
- `docs/`: documentación técnica y operativa.
- `.github/workflows/`: automatización de build y publicación.

## Canales

- `dev` genera `testing`, destinado a validar cambios.
- `main` genera `stable`, destinado a distribución estable.

Los canales se construyen de forma independiente y aplican la misma política CPV. El
canal no se codifica en `pkgver` ni en `pkgrel`.

## Desarrollo

Requisitos locales: Python 3, Bash y PyYAML. Las comprobaciones Zsh y Fish se ejecutan
cuando los intérpretes están instalados; CI instala ambos para que no se omitan.

```bash
python3 -m unittest discover -s tests -v
```

Consulta [TESTING.md](docs/TESTING.md) para conocer el alcance y las obligaciones de
mantenimiento de la suite. La ayuda de las herramientas está disponible mediante:

```bash
python3 scripts/cambonos.py --help
```

Antes de fusionar `dev` en `main`, deben estar verificadas en un sistema real las
funciones incluidas en el alcance soportado de esa versión. El estado se registra en
[PACKAGE-TEST-CHECKLIST.md](docs/PACKAGE-TEST-CHECKLIST.md).

## Documentación

- [Despliegue automatizado](docs/DEPLOYMENT.md): triggers, jobs, firma y publicación.
- [Planificación y compilación](docs/BUILD.md): fingerprints, recuperación y compilación
  selectiva.
- [Gestión de claves GPG](docs/GPG-SETUP.md): creación, custodia y configuración de
  claves.
- [Versionado CPV](docs/VERSIONING.md): clasificación de cambios e inmutabilidad.
- [Pruebas automatizadas](docs/TESTING.md): alcance y mantenimiento de la suite.
- [Checklist funcional](docs/PACKAGE-TEST-CHECKLIST.md): validación en sistemas reales.
- [Integración de la migración XFCE](docs/XFCE-MIGRATION-INTEGRATION.md): contratos pendientes para installer y mkiso.

## Licencia

Consulta `LICENSE` y las licencias incluidas en cada paquete.
