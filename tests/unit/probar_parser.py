
"""
Prueba integral del lexer y parser de MILPA.
"""

from pathlib import Path

from src.frontend.lexer import Lexer
from src.parser import Parser, ErrorSintactico
from src.frontend.ast_nodes import imprimir_ast
from src.core.errors import ErrorLog


# Obtiene la ruta del programa de ejemplo
raiz = Path(__file__).resolve().parents[2]
archivo = raiz / "examples" / "ejemplo_riego.milpa"

# Lee el código fuente
codigo = archivo.read_text(encoding="utf-8")

# Crea un registro compartido de errores
errores = ErrorLog()

# Primera etapa: análisis léxico
print("\n========== ANALISIS LEXICO ==========\n")

lexer = Lexer(codigo, errores)
tokens = lexer.analizar()

lexer.imprimir_tabla()

# Comprueba si existen errores léxicos
if errores.hay_errores():
    print("\nSe encontraron errores:")
    errores.imprimir()

else:
    # Segunda etapa: análisis sintáctico
    print("\n========== ANALISIS SINTACTICO ==========\n")

    parser = Parser(tokens, errores)
    arbol = parser.analizar()

    if arbol is not None:
        print("Análisis sintáctico correcto.")

        # Tercera etapa: impresión del AST
        print("\n========== ARBOL AST DE MILPA ==========\n")

        imprimir_ast(arbol)

    else:
        print("No fue posible construir el AST.")

    # Muestra los errores encontrados
    if errores.hay_errores():
        print("\n========== ERRORES ==========\n")
        errores.imprimir()
