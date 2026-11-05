"""Punto de entrada (CLI) del compilador Milpa. Responsable: C."""
import argparse
import sys


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
    print(f"Leído {args.fuente} ({len(codigo)} caracteres). El pipeline aún no está conectado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
