# CambonOS Packages

Repositorio de los paquetes propios de **CambonOS**, una distribución basada en Arch Linux. Aquí se mantienen los paquetes que aportan identidad visual, configuración de escritorio, integración del sistema y acceso a los repositorios de CambonOS.

## Paquetes

| Paquete | Función |
|---|---|
| [cambonos-base](packages/cambonos-base/README.md) | Metapaquete que agrupa los componentes generales de CambonOS y permite instalarlos conjuntamente. |
| [cambonos-branding](packages/cambonos-branding/README.md) | Recursos gráficos y tipografía de CambonOS. |
| [cambonos-fastfetch](packages/cambonos-fastfetch/README.md) | Identidad CambonOS e información del sistema en Fastfetch. |
| [cambonos-shell-prompt](packages/cambonos-shell-prompt/README.md) | Prompt Starship de CambonOS para Bash, Zsh y Fish. |
| [cambonos-zsh](packages/cambonos-zsh/README.md) | Configuración e integraciones predeterminadas de Zsh. |
| [cambonos-release](packages/cambonos-release/README.md) | Identidad y metadatos de la distribución. |
| [cambonos-pacman](packages/cambonos-pacman/README.md) | Configuración de los repositorios y de Pacman. |
| [cambonos-grub](packages/cambonos-grub/README.md) | Configuración y tema de GRUB. |
| [cambonos-plymouth](packages/cambonos-plymouth/README.md) | Tema de arranque e integración de Plymouth. |
| [cambonos-keyring](packages/cambonos-keyring/README.md) | Claves públicas para verificar los paquetes CambonOS. |

Los paquetes del instalador y de creación de imágenes se mantienen en sus propios repositorios: [CambonOS/installer](https://github.com/CambonOS/installer) y [CambonOS/iso](https://github.com/CambonOS/iso).

## Organización

- `packages/`: fuentes, recursos y archivos de construcción de cada paquete.
- `tests/`: comprobaciones automáticas del contenido de los paquetes y de las herramientas del repositorio.
- `scripts/`: herramientas de validación, construcción y publicación.
- `docs/`: documentación operativa y checklist funcional.
- `.github/workflows/`: automatización de integración y publicación.

## Canales

El repositorio mantiene dos ramas y canales:

- `dev` genera el canal `testing`, destinado a probar cambios antes de su integración estable.
- `main` genera el canal `stable`, destinado a los usuarios.

Los canales se construyen de forma independiente.

## Desarrollo

Para ejecutar toda la suite localmente se necesita Python, Bash, Zsh y Fish. La validación de scripts Zsh y Fish se omite si sus intérpretes no están instalados:

```bash
python3 -m unittest discover -s tests -v
```

La ayuda de las herramientas está disponible mediante:

```bash
python3 scripts/cambonos.py --help
```

Antes de fusionar `dev` en `main`, deben estar verificadas en un entorno real todas las funciones que formen parte del alcance soportado de esa versión. Las pruebas excluidas del alcance por limitaciones documentadas y expresamente aceptadas pueden permanecer pendientes; deben seguir identificadas como no verificadas en la [checklist funcional](docs/PACKAGE-TEST-CHECKLIST.md).

## Documentación

- [Despliegue automatizado](docs/DEPLOYMENT.md)
- [Gestión de claves GPG](docs/GPG-SETUP.md)
- [Checklist funcional de paquetes](docs/PACKAGE-TEST-CHECKLIST.md)

## Licencia

Consulta `LICENSE` y las licencias incluidas en cada paquete.
