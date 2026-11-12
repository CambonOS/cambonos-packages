# Pruebas automatizadas

La suite de `tests/` protege los contratos esenciales de CambonOS Packages y detecta
regresiones que puedan afectar a los paquetes, las herramientas y la automatización.
Comprueba el comportamiento observable, no detalles privados de implementación.

## Alcance

La suite cubre tres áreas:

- **Paquetes:** identidad, metadatos, archivos imprescindibles, configuración e
  integraciones cuyo fallo supondría una regresión.
- **Herramientas y pipeline:** comandos, políticas de publicación, sintaxis ejecutable y
  contratos esenciales de los workflows.
- **Recursos:** validez de datos estructurados, enlaces simbólicos y coherencia de
  archivos utilizados por los paquetes.

Las pruebas pueden comprobar estructura cuando esta protege un requisito real, por
ejemplo que un metapaquete no instale archivos o que Pacman exija firmas. Deben evitar
imponer una secuencia de comandos, nombre de función auxiliar, hook o estructura interna cuando
varias implementaciones pueden satisfacer el mismo contrato.

## Límites

Las pruebas automatizadas no sustituyen la validación funcional en un sistema Arch real.
La instalación, actualización, retirada, arranque, sesión gráfica y comportamiento
visual se registran en [PACKAGE-TEST-CHECKLIST.md](PACKAGE-TEST-CHECKLIST.md).

No debe marcarse una capacidad como verificada solo porque sus archivos existan o su
sintaxis sea correcta. Si una comprobación requiere Arch, Pacman, systemd, una sesión
gráfica o un arranque real, debe realizarse en un entorno de integración apropiado o
quedar pendiente en la checklist.

La suite debe ser determinista, no necesitar red, no modificar el sistema anfitrión y no
requerir privilegios.

## Mantenimiento de las pruebas

Todo cambio en un paquete, sus dependencias, hooks, scripts, recursos ejecutables o
configuración requiere revisar las pruebas afectadas. La revisión puede concluir que no
hace falta modificarlas, pero esa conclusión debe ser deliberada.

Los cambios en `scripts/`, dependencias de construcción, workflows, configuración de CI
o publicación requieren revisar también las pruebas transversales y los contratos del
pipeline.

En particular:

- Añade una prueba automatizada para las nuevas funciones que puedan verificarse sin un
  sistema completo.
- Añade o adapta una prueba que reproduzca el comportamiento incorrecto cuando se
  corrige un bug y sea viable automatizarlo.
- Añade a la checklist las funciones nuevas que necesiten validación real.
- Justifica la eliminación o sustitución de una prueba indicando cómo queda cubierto el
  contrato o por qué deja de formar parte del alcance.
- No cambies pruebas para ocultar un incumplimiento funcional.

## Ejecución local

Desde la raíz del repositorio:

```bash
python3 -m unittest discover -s tests -v
```

Requisitos mínimos: Python 3, Bash y PyYAML. Las comprobaciones de Zsh y Fish se
ejecutan si sus intérpretes están instalados. El workflow de CI instala ambos para que
esas comprobaciones no se omitan.
