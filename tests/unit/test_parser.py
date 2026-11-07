
"""
Pruebas unitarias del analizador sintáctico MILPA.
"""

import unittest

from src.frontend.lexer import Lexer
from src.parser import Parser
from src.core.errors import ErrorLog


class TestParser(unittest.TestCase):

    # Comprueba una declaración de variable
    def test_declaracion_variable(self):
        errores = ErrorLog()
        lexer = Lexer("entero edad = 21", errores)

        tokens = lexer.analizar()
        parser = Parser(tokens, errores)

        arbol = parser.analizar()

        self.assertIsNotNone(arbol)
        self.assertEqual(
            arbol.instrucciones[0].nombre,
            "edad"
        )

    # Comprueba una operación aritmética
    def test_operacion_aritmetica(self):
        errores = ErrorLog()
        lexer = Lexer("entero resultado = 5 + 3", errores)

        parser = Parser(lexer.analizar(), errores)
        arbol = parser.analizar()

        self.assertIsNotNone(arbol)
        self.assertEqual(
            arbol.instrucciones[0].valor.operador,
            "+"
        )

    # Comprueba una condición
    def test_condicional(self):
        errores = ErrorLog()
        codigo = 'si (verdadero) { registrar("Hola") }'

        lexer = Lexer(codigo, errores)
        parser = Parser(lexer.analizar(), errores)

        arbol = parser.analizar()

        self.assertIsNotNone(arbol)
        self.assertEqual(
            len(arbol.instrucciones),
            1
        )

    # Comprueba el registro de errores sintácticos
    def test_error_sintactico(self):
        errores = ErrorLog()
        codigo = "entero edad ="

        lexer = Lexer(codigo, errores)
        parser = Parser(lexer.analizar(), errores)

        arbol = parser.analizar()

        self.assertIsNone(arbol)
        self.assertTrue(errores.hay_errores())


if __name__ == "__main__":
    unittest.main()
