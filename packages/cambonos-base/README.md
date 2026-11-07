# cambonos-base

Metapaquete que agrupa los componentes generales de CambonOS y proporciona una
única entrada para instalar su experiencia base.

## Componentes

- `cambonos-keyring`: material público de confianza para los repositorios CambonOS.
- `cambonos-pacman`: configuración e integración de los repositorios CambonOS.
- `cambonos-release`: identidad y metadatos de la distribución.
- `cambonos-branding`: recursos gráficos y tipografía de CambonOS.
- `cambonos-fastfetch`: configuración e integración de Fastfetch.
- `cambonos-shell-prompt`: configuración de Starship e integración con shells.
- `cambonos-zsh`: configuración global y experiencia Zsh de CambonOS.

Zsh forma parte obligatoria de la experiencia base y es la shell recomendada
por CambonOS. La selección de la shell de inicio de sesión para usuarios nuevos
corresponde al instalador; instalar este metapaquete no modifica la shell de
inicio de sesión de las cuentas existentes.

## Componentes independientes

`cambonos-grub` y `cambonos-plymouth` no forman parte de este metapaquete. Su
instalación depende de las decisiones específicas de arranque y configuración
del sistema.

## Dependencias

Las dependencias directas son los siete paquetes CambonOS enumerados en la
sección de componentes. Cada componente conserva su propio paquete, ciclo de
versionado, configuración y responsabilidad. Este metapaquete no instala
archivos, no proporciona hooks ALPM y no ejecuta scripts de instalación.
