# Filosofía y mantenimiento de las pruebas

La suite de `tests/` protege **el comportamiento esencial y los contratos del
proyecto**, no la forma concreta en que se implementan. Su objetivo es detectar
regresiones funcionales y errores que puedan romper la validación, construcción,
firma o publicación de CambonOS Packages.

## Principios

1. **Probar resultados, no detalles internos.** Una prueba debe describir qué
   capacidad ofrece un paquete o qué garantía proporciona una herramienta.
   No debe exigir nombres privados de funciones, marcadores internos,
   secuencias exactas de comandos, nombres de hooks o una estructura de
   implementación si existen varias formas válidas de cumplir el contrato.
2. **Contratos esenciales por paquete.** Cada paquete debe tener pruebas que
   representen su propósito: recursos imprescindibles, identidad, configuración
   o integración crítica. No se pretende enumerar todos sus archivos ni
   duplicar el contenido del PKGBUILD.
3. **Pruebas transversales.** La suite comprueba sintaxis Python, Bash/PKGBUILD,
   scripts de instalación y fragmentos Zsh/Fish cuando los intérpretes están
   disponibles; también valida recursos JSON, enlaces simbólicos y la
   estructura esencial del workflow.
4. **La pipeline es una interfaz pública del repositorio.** Las pruebas deben
   detectar errores de sintaxis y fallos de cableado que impidan ejecutar los
   trabajos esenciales, sin congelar nombres de pasos, orden incidental o
   detalles de implementación que puedan cambiar sin alterar el comportamiento.
5. **Las pruebas automatizadas no sustituyen las pruebas reales.** La
   instalación, actualización, retirada, arranque, escritorio y comportamiento
   visual se registran en [PACKAGE-TEST-CHECKLIST.md](PACKAGE-TEST-CHECKLIST.md).
6. **Evitar afirmaciones no demostradas.** Si una capacidad no puede probarse
   en el entorno automatizado, debe quedar documentada como validación manual
   pendiente; nunca debe marcarse como cubierta por una prueba estática.

## Qué debe probarse

- **Por paquete:** identidad y metadatos mínimos, entregables que materializan
  su función y garantías de alto nivel que serían una regresión si desaparecen.
- **Transversalmente:** sintaxis de fuentes ejecutables, validez de recursos
  estructurados, integridad básica de enlaces y coherencia mínima del workflow.
- **Herramientas del repositorio:** comportamiento observable de sus comandos
  y garantías de seguridad/publicación cuando sean relevantes. Las pruebas
  deben invocar interfaces públicas o comprobar resultados, no acoplarse a
  helpers privados.

## Qué debe evitarse

- Comprobar el texto literal de una implementación cuando basta con verificar
  el resultado.
- Exigir que exista o no exista una función, hook, archivo auxiliar o marcador
  por razones que no formen parte del contrato funcional.
- Replicar el PKGBUILD línea por línea en los tests.
- Convertir una decisión temporal de arquitectura en una regla permanente.
- Marcar como funcionalmente verificada una capacidad solo porque sus archivos
  existen o su sintaxis es correcta.

Una prueba estructural está justificada cuando protege un requisito real
(por ejemplo, que un metapaquete no instale archivos o que la configuración de
Pacman exija firmas). Debe explicar el requisito y no imponer más restricciones
de las necesarias.

## Obligación de actualizar las pruebas

**Todo cambio en un paquete, sus dependencias, hooks, scripts, recursos
ejecutables o archivos de configuración debe incluir una revisión explícita de
las pruebas afectadas.** La revisión puede concluir que no hace falta modificar
ninguna prueba, pero esa conclusión debe ser deliberada: se debe comprobar si
el cambio altera un contrato esencial o introduce un nuevo riesgo de sintaxis o
de pipeline.

**Todo cambio en `scripts/`, dependencias de construcción, workflows,
configuración de CI o proceso de publicación debe revisar las pruebas
transversales y los contratos de pipeline.**

En particular:

- Una funcionalidad nueva requiere un contrato automatizado cuando pueda
  verificarse sin un sistema completo; además, debe añadirse a la checklist
  funcional si necesita validación real.
- Una corrección de bug debe añadir o adaptar una prueba que reproduzca el
  comportamiento incorrecto cuando sea viable.
- La eliminación o sustitución de una prueba exige justificar que el contrato
  queda cubierto de otra manera o que ha dejado de formar parte del alcance.
- No se deben modificar tests únicamente para hacer pasar una implementación
  que incumple el comportamiento esperado.
- Los cambios de paquetes y pipeline deben revisar la suite en el mismo cambio
  Git; no se debe posponer esa revisión a un commit futuro.

## Ejecución local y CI

Ejecutar desde la raíz:

```bash
python3 -m unittest discover -s tests -v
```

Requisitos: Python 3, Bash y PyYAML. Las comprobaciones Zsh y Fish se ejecutan
si los intérpretes están instalados. El workflow instala ambos para que esas
comprobaciones no se omitan en CI.

La suite debe ser determinista, no necesitar red, no modificar el sistema
anfitrión y no requerir privilegios. Las pruebas que necesiten Arch Linux,
Pacman, una sesión gráfica, systemd o arranque real pertenecen a entornos de
integración separados o a la checklist funcional.
