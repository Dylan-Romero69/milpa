"""Ayudas para las pruebas: ejecutan las fases del compilador dentro de Python."""
import sys

from src.core.errors import ErrorLog
from src.frontend.lexer import Lexer
from src.frontend.semantic import AnalizadorSemantico
from src.parser import Parser

sys.setrecursionlimit(10000)   # igual que milpa.py


def parsear(codigo):
    """Léxico + sintáctico. Devuelve (ast, log); ast es None si hubo error."""
    log = ErrorLog()
    tokens = Lexer(codigo, log).analizar()
    if log.hay_errores():
        return None, log
    ast = Parser(tokens, log).analizar()
    if log.hay_errores():
        return None, log
    return ast, log


def analizar(codigo):
    """Léxico + sintáctico + semántico. Devuelve (ast, analizador, log)."""
    ast, log = parsear(codigo)
    assert ast is not None, [str(e) for e in log.errores]
    semantico = AnalizadorSemantico(log)
    semantico.analizar(ast)
    return ast, semantico, log


def compilar(codigo):
    """Todas las fases hasta generar el .asm. Devuelve ('ok'|'error', códigos de error)."""
    from src.codegen_mips import GeneradorMIPS
    from src.intermediate import GeneradorIntermedio
    from src.optimizer import Optimizador
    from src.regalloc import AsignadorRegistros
    import os, tempfile

    ast, log = parsear(codigo)
    if ast is not None:
        AnalizadorSemantico(log).analizar(ast)
    if log.hay_errores():
        return "error", [e.codigo for e in log.errores]
    cuadruplos = Optimizador().optimizar(GeneradorIntermedio().generar(ast))
    asignador = AsignadorRegistros(cuadruplos)
    asignador.asignar()
    with tempfile.TemporaryDirectory() as carpeta:
        GeneradorMIPS(cuadruplos, asignador).guardar(os.path.join(carpeta, "t.asm"))
    return "ok", []
