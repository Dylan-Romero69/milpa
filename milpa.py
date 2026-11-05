"""Punto de entrada (CLI) del compilador Milpa. Responsable: C."""
import argparse
import sys

from src.errors import ErrorLog
from src.lexer import tokenizar


def main():
    ap = argparse.ArgumentParser(prog="milpa", description="Compilador Milpa")
    ap.add_argument("fuente", nargs="?", help="programa .milpa")
    ap.add_argument("-o", "--salida", help="archivo .asm de salida")
    ap.add_argument("--tokens", action="store_true", help="mostrar tokens")
    ap.add_argument("--ast", action="store_true", help="mostrar AST")
    ap.add_argument("--simbolos", action="store_true", help="mostrar tabla de símbolos y direcciones")
    ap.add_argument("--cuadruplos", action="store_true", help="mostrar cuádruplos")
    ap.add_argument("--opt", action="store_true", help="aplicar optimización")
    ap.add_argument("--metricas", action="store_true", help="comparar antes y después de optimizar")
    ap.add_argument("--notacion", metavar="EXPR", help="convertir una expresión a postfija y prefija")
    args = ap.parse_args()

    if args.notacion:
        print("Pendiente: src/notation.py")
        return 0
    if not args.fuente:
        ap.print_help()
        return 1

    with open(args.fuente, encoding="utf-8") as f:
        codigo = f.read()

    log = ErrorLog()
    tokens = tokenizar(codigo, log)
    if args.tokens:
        for t in tokens:
            print(f"{t.linea}:{t.col}\t{t.tipo}\t{t.lexema}")
    if log.hay_errores():
        log.imprimir()
        return 1

    print(f"Análisis léxico correcto ({len(tokens) - 1} tokens). "
          "Las demás fases aún no están conectadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
