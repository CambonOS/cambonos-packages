# Política de opacidad del tema GTK de CambonOS

El paquete genera tres perfiles GTK a partir de una única paleta y plantilla canónicas.

## Perfiles

| Tema | Opacidad de ventana | Multiplicador de transparencia |
|---|---:|---:|
| `CambonOS-dark` | 98 % | 1 |
| `CambonOS-dark-balanced` | 88 % | 5 |
| `CambonOS-dark-transparent` | 78 % | 10 |

`CambonOS-dark` es el perfil Conservador y conserva el nombre predeterminado histórico.
Los otros dos perfiles son variantes generadas.

## Política de superficies

- Las ventanas y las superficies principales de contenido y entrada utilizan la opacidad
  del perfil.
- Las superficies secundarias y flotantes utilizan los tokens semánticos de la paleta y
  se transforman con el multiplicador del perfil.
- El texto, los iconos, los acentos y los indicadores funcionales permanecen opacos,
  salvo que un token de diseño indique expresamente lo contrario.
- Los botones planos y los contenedores GTK estructurales permanecen transparentes
  cuando heredan la superficie visible de su elemento padre.
- Los popovers, menús y tooltips son superficies flotantes independientes.
- La opacidad de las sombras de Xfwm4 es independiente del alfa de los fondos GTK.

## Reglas de implementación

Los valores alfa se definen en `src/palette.json` y se transforman mediante
`tools/build-theme.py`. Las hojas de estilo GTK deben consumir los tokens generados; no
deben introducir colores RGBA ad hoc.

El generador aplica a cada token con alfa la transformación:

```text
alpha_generado = opacidad_ventana - (1 - alpha_fuente) * multiplicador
```

El validador comprueba la estructura generada, los perfiles y las excepciones de
transparencia documentadas. Un nodo GTK estructural transparente puede ser correcto si
hereda la superficie prevista de su padre; el árbol de widgets real depende del contexto
de cada aplicación.
