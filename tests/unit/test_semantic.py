
import unittest

from src.frontend.lexer import Lexer
from src.parser import Parser
from src.frontend.semantic import AnalizadorSemantico
from src.core.errors import ErrorLog


def analizar_codigo(codigo):
    errores = ErrorLog()

    lexer = Lexer(codigo, errores)
    tokens = lexer.analizar()

    if errores.hay_errores():
        return errores

    parser = Parser(tokens, errores)
    arbol = parser.analizar()

    if arbol is None or errores.hay_errores():
        return errores

    semantico = AnalizadorSemantico(errores)
    semantico.analizar(arbol)

    return errores


class TestAnalisisSemantico(unittest.TestCase):

    def test_programa_correcto(self):
        codigo = """
entero humedad = 50
decimal temperatura = 25.5
humedad = 60
"""
        errores = analizar_codigo(codigo)

        self.assertFalse(errores.hay_errores())

    def test_variable_no_declarada(self):
        codigo = """
entero humedad = 50
temperatura = 25
"""
        errores = analizar_codigo(codigo)

        self.assertTrue(errores.hay_errores())
        self.assertTrue(
            any(e.codigo == "E-SEM-05"
                for e in errores.obtener_errores())
        )

    def test_variable_duplicada(self):
        codigo = """
entero humedad = 50
entero humedad = 60
"""
        errores = analizar_codigo(codigo)

        self.assertTrue(errores.hay_errores())
        self.assertTrue(
            any(e.codigo == "E-SEM-01"
                for e in errores.obtener_errores())
        )

    def test_tipo_incompatible(self):
        codigo = """
entero humedad = 50
texto mensaje = "Hola"
humedad = mensaje
"""
        errores = analizar_codigo(codigo)

        self.assertTrue(errores.hay_errores())
        self.assertTrue(
            any(e.codigo == "E-SEM-03"
                for e in errores.obtener_errores())
        )

    def test_condicion_incompatible(self):
        codigo = """
entero humedad = 50

si (humedad) {
    registrar("Regando")
}
"""
        errores = analizar_codigo(codigo)

        self.assertTrue(errores.hay_errores())
        self.assertTrue(
            any(e.codigo == "E-SEM-07"
                for e in errores.obtener_errores())
        )


if __name__ == "__main__":
    unittest.main()
