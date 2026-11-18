# Milpa

Compilador de un lenguaje en español para describir reglas de riego de un huerto.
Proyecto integrador de Autómatas II (ITO). Entrega: 16 de noviembre de 2026.

Flujo: `.milpa` -> léxico -> sintáctico -> semántico -> cuádruplos -> optimizador -> `.asm` (MIPS) -> MARS.

## Requisitos
- Python 3.10 o superior (solo biblioteca estándar)
- Java y MARS (`tools/Mars4_5.jar`; cada quien lo descarga)

## Uso
```
python milpa.py programa.milpa                  # genera programa.asm
python milpa.py programa.milpa -o salida.asm
python milpa.py programa.milpa --tokens --ast --simbolos
python milpa.py programa.milpa --cuadruplos --opt --metricas
python milpa.py --notacion "a + b * c"
```
Para ejecutar el resultado: `java -jar tools/Mars4_5.jar programa.asm`
(o sin ventana: `java -jar tools/Mars4_5.jar nc programa.asm`).

El MIPS generado usa la FPU para los `decimal`, guarda cada zona como un registro
de 4 palabras en `.data` y pide por consola las lecturas de `leer()` y `lloviendo()`.

## Interfaz gráfica
```
python -m gui.app
```
**Abrir** acepta `.milpa` y `.asm`. Un `.asm` se ensambla y ejecuta con el simulador
MIPS integrado (`src/mips_sim.py`); las zonas y variables de la memoria final se
convierten en el huerto, y el editor muestra el código MILPA equivalente.

## Reparto
| Responsable | Archivos |
|---|---|
| A (frontend) | src/lexer.py, parser.py, ast_nodes.py, symtab.py, semantic.py, errors.py |
| B (medio) | src/notation.py, intermediate.py, optimizer.py |
| C (backend) | src/regalloc.py, codegen_mips.py, milpa.py, tools/ |

Los formatos que comparten los módulos están en `docs/FORMATOS.md`.
Cambiar un formato requiere avisar a los tres.

## Ramas
`main` siempre funciona. Cada quien trabaja en su rama (`frontend`, `intermedio`, `backend`) y la une a `main` cuando esté probada.
