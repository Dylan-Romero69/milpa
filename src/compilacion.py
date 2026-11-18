"""Compila un programa MILPA completo hasta MIPS sin imprimir nada."""

import contextlib
import io

from src.core.errors import ErrorLog
from src.frontend.lexer import Lexer
from src.frontend.semantic import AnalizadorSemantico
from src.parser import Parser
from src.intermediate import GeneradorIntermedio
from src.optimizer import Optimizador
from src.regalloc import AsignadorRegistros
from src.codegen_mips import GeneradorMIPS


def compilar_a_mips(codigo):
    """
    Ejecuta todas las fases. Devuelve (asm, errores): asm es None si hubo
    errores, y errores es la lista de errores registrados.
    """
    errores = ErrorLog()

    with contextlib.redirect_stdout(io.StringIO()):
        tokens = Lexer(codigo, errores).analizar()
        if errores.hay_errores():
            return None, errores.obtener_errores()

        arbol = Parser(tokens, errores).analizar()
        if arbol is None or errores.hay_errores():
            return None, errores.obtener_errores()

        AnalizadorSemantico(errores).analizar(arbol)
        if errores.hay_errores():
            return None, errores.obtener_errores()

        generador = GeneradorIntermedio()
        cuadruplos = Optimizador().optimizar(generador.generar(arbol))
        asignador = AsignadorRegistros(cuadruplos)
        asignador.asignar()
        asm = GeneradorMIPS(cuadruplos, asignador, generador.tipos).generar()

    return asm, []
