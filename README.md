# CambonOS Packages

Repositorio de los paquetes propios de **CambonOS**, una distribución basada en Arch Linux. Aquí se mantienen los paquetes que aportan identidad visual, configuración de escritorio, integración del sistema y acceso a los repositorios de CambonOS.

## Paquetes

| Paquete | Función |
|---|---|
| [cambonos-base](packages/cambonos-base/README.md) | Metapaquete que agrupa los componentes generales de CambonOS y permite instalarlos conjuntamente. |
| [cambonos-branding](packages/cambonos-branding/README.md) | Recursos gráficos y tipografía de CambonOS. |
| [cambonos-gtk-theme](packages/cambonos-gtk-theme/README.md) | Tema oscuro único para GTK 3, GTK 4 y decoraciones de ventanas Xfwm4. |
| [cambonos-fastfetch](packages/cambonos-fastfetch/README.md) | Identidad CambonOS e información del sistema en Fastfetch. |
| [cambonos-shell-prompt](packages/cambonos-shell-prompt/README.md) | Prompt Starship de CambonOS para Bash, Zsh y Fish. |
| [cambonos-zsh](packages/cambonos-zsh/README.md) | Configuración e integraciones predeterminadas de Zsh. |
| [cambonos-release](packages/cambonos-release/README.md) | Identidad y metadatos de la distribución. |
| [cambonos-pacman](packages/cambonos-pacman/README.md) | Configuración de los repositorios y de Pacman. |
| [cambonos-grub](packages/cambonos-grub/README.md) | Configuración y tema de GRUB. |
| [cambonos-plymouth](packages/cambonos-plymouth/README.md) | Tema de arranque e integración de Plymouth. |
| [cambonos-lightdm](packages/cambonos-lightdm/README.md) | Configuración de LightDM y Slick Greeter. |
| [cambonos-keyring](packages/cambonos-keyring/README.md) | Claves públicas para verificar los paquetes CambonOS. |

Los paquetes del instalador y de creación de imágenes se mantienen en sus propios repositorios: [CambonOS/cambonos-installer](https://github.com/CambonOS/cambonos-installer) y [CambonOS/cambonos-mkiso](https://github.com/CambonOS/cambonos-mkiso).

## Organización

- `packages/`: fuentes, recursos y archivos de construcción de cada paquete.
- `tests/`: contratos funcionales esenciales por paquete y comprobaciones transversales de sintaxis e integridad de la pipeline.
- `scripts/`: herramientas de validación, construcción y publicación.
- `docs/`: documentación operativa y checklist funcional.
- `.github/workflows/`: automatización de integración y publicación.

## Canales

El repositorio mantiene dos ramas y canales:

- `dev` genera el canal `testing`, destinado a probar cambios antes de su integración estable.
- `main` genera el canal `stable`, destinado a los usuarios.

Los canales se construyen de forma independiente. Ambos utilizan la misma política
de versiones CPV; el canal no se codifica en `pkgver` ni en `pkgrel`.

## Desarrollo

Para ejecutar la suite localmente se necesita Python, Bash y PyYAML. Las comprobaciones de fragmentos Zsh y Fish se ejecutan cuando sus intérpretes están instalados; en CI ambos intérpretes se instalan expresamente:

```bash
python3 -m unittest discover -s tests -v
```

La filosofía, el alcance y las obligaciones de mantenimiento de las pruebas están definidos en [docs/TESTING.md](docs/TESTING.md).

La ayuda de las herramientas está disponible mediante:

```bash
python3 scripts/cambonos.py --help
```

Antes de fusionar `dev` en `main`, deben estar verificadas en un entorno real todas las funciones que formen parte del alcance soportado de esa versión. Las pruebas excluidas del alcance por limitaciones documentadas y expresamente aceptadas pueden permanecer pendientes; deben seguir identificadas como no verificadas en la [checklist funcional](docs/PACKAGE-TEST-CHECKLIST.md).

## Documentación

- [Versionado de paquetes CPV](docs/VERSIONING.md)
- [Despliegue automatizado](docs/DEPLOYMENT.md)
- [Gestión de claves GPG](docs/GPG-SETUP.md)
- [Checklist funcional de paquetes](docs/PACKAGE-TEST-CHECKLIST.md)

## Licencia

Consulta `LICENSE` y las licencias incluidas en cada paquete.
