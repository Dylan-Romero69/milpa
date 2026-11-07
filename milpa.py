
import argparse
import sys
from pathlib import Path

from src.core.errors import ErrorLog
from src.frontend.lexer import Lexer
from src.frontend.ast_nodes import imprimir_ast
from src.parser import Parser
from src.frontend.semantic import AnalizadorSemantico
from src.intermediate import GeneradorIntermedio
from src.optimizer import Optimizador
from src.regalloc import AsignadorRegistros
from src.codegen_mips import GeneradorMIPS
from src.notation import a_postfija, a_prefija


def convertir_notacion(expresion):
    """Muestra las conversiones de una expresión."""

    print("\n========== CONVERSION DE EXPRESIONES ==========")
    print(f"Infija:   {expresion}")
    print(f"Postfija: {a_postfija(expresion)}")
    print(f"Prefija:  {a_prefija(expresion)}")
    print("=" * 50)


def main():

    ap = argparse.ArgumentParser(
        prog="milpa",
        description="Compilador MILPA para monitoreo y riego de cultivos"
    )

    ap.add_argument("fuente", nargs="?", help="Archivo fuente .milpa")
    ap.add_argument("-o", "--salida", help="Archivo ASM de salida")

    ap.add_argument("--tokens", action="store_true", help="Mostrar tokens")
    ap.add_argument("--ast", action="store_true", help="Mostrar AST")
    ap.add_argument("--simbolos", action="store_true", help="Mostrar tabla de símbolos")
    ap.add_argument("--cuadruplos", action="store_true", help="Mostrar código intermedio")
    ap.add_argument("--opt", action="store_true", help="Optimizar código intermedio")
    ap.add_argument("--metricas", action="store_true", help="Mostrar métricas de optimización")
    ap.add_argument("--registros", action="store_true", help="Mostrar asignación de registros")
    ap.add_argument("--notacion", metavar="EXPR", help="Convertir expresión infija a postfija y prefija")

    args = ap.parse_args()

    # Conversión de expresiones
    if args.notacion:
        try:
            convertir_notacion(args.notacion)
            return 0
        except ValueError as error:
            print(f"Error: {error}")
            return 1

    if not args.fuente:
        ap.print_help()
        return 1

    ruta = Path(args.fuente)

    if not ruta.exists():
        print(f"Error: no existe el archivo {ruta}")
        return 1

    if ruta.suffix != ".milpa":
        print("Error: el archivo fuente debe tener extensión .milpa")
        return 1

    codigo = ruta.read_text(encoding="utf-8")

    # Fase 1: análisis léxico
    log = ErrorLog()
    lexer = Lexer(codigo, log)
    tokens = lexer.analizar()

    if args.tokens:
        print("\n========== TOKENS ==========")
        lexer.imprimir_tabla()

    if log.hay_errores():
        log.imprimir()
        return 1

    # Fase 2: análisis sintáctico
    parser = Parser(tokens, log)
    ast = parser.analizar()

    if ast is None or log.hay_errores():
        log.imprimir()
        return 1

    if args.ast:
        print("\n========== ARBOL SINTACTICO ==========")
        imprimir_ast(ast)

    # Fase 3: análisis semántico
    semantico = AnalizadorSemantico(log)
    semantico.analizar(ast)

    if log.hay_errores():
        log.imprimir()
        return 1

    # Fase 4: generación de código intermedio
    generador = GeneradorIntermedio()
    cuadruplos = generador.generar(ast)

    if args.cuadruplos:
        print("\n========== CODIGO INTERMEDIO ORIGINAL ==========")
        generador.imprimir()

    # Fase 5: optimización
    if args.opt or args.metricas:
        optimizador = Optimizador()
        cuadruplos = optimizador.optimizar(cuadruplos)

        if args.opt:
            optimizador.imprimir()

        if args.metricas:
            optimizador.imprimir_metricas()

    # Fase 6: asignación de registros
    asignador = AsignadorRegistros(cuadruplos)
    asignador.asignar()

    if args.registros:
        asignador.imprimir()

    # Fase 7: generación MIPS
    generador_mips = GeneradorMIPS(cuadruplos, asignador)

    salida = args.salida or str(ruta.with_suffix(".asm"))

    generador_mips.guardar(salida)

    print("\n========== COMPILACION EXITOSA ==========")
    print(f"Archivo fuente: {ruta}")
    print(f"Archivo MIPS:   {salida}")
    print("MILPA finalizó la generación de código.")
    print("=" * 45)

    return 0


if __name__ == "__main__":
    sys.exit(main())
