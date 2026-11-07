
"""
Pruebas unitarias del analizador léxico MILPA.
"""

import unittest

from src.frontend.lexer import Lexer


class TestLexer(unittest.TestCase):

    # Comprueba el reconocimiento de palabras reservadas
    def test_palabras_reservadas(self):
        lexer = Lexer("entero decimal texto booleano")
        tokens = lexer.analizar()

        tipos = [token.tipo for token in tokens]

        self.assertEqual(
            tipos,
            [
                "TIPO_ENTERO",
                "TIPO_DECIMAL",
                "TIPO_TEXTO",
                "TIPO_BOOLEANO",
                "EOF"
            ]
        )

    # Comprueba el reconocimiento de identificadores
    def test_identificadores(self):
        lexer = Lexer("humedad temperatura")
        tokens = lexer.analizar()

        self.assertEqual(tokens[0].tipo, "ID")
        self.assertEqual(tokens[1].tipo, "ID")

    # Comprueba números enteros y decimales
    def test_numeros(self):
        lexer = Lexer("25 35.5")
        tokens = lexer.analizar()

        self.assertEqual(tokens[0].tipo, "ENTERO")
        self.assertEqual(tokens[1].tipo, "DECIMAL")

    # Comprueba los operadores
    def test_operadores(self):
        lexer = Lexer("+ - * / == != >= <")
        tokens = lexer.analizar()

        tipos = [token.tipo for token in tokens]

        self.assertEqual(
            tipos,
            [
                "SUMA",
                "RESTA",
                "MULTIPLICACION",
                "DIVISION",
                "IGUAL",
                "DIFERENTE",
                "MAYOR_IGUAL",
                "MENOR",
                "EOF"
            ]
        )

    # Comprueba el reconocimiento de textos
    def test_textos(self):
        lexer = Lexer('"Hola MILPA"')
        tokens = lexer.analizar()

        self.assertEqual(tokens[0].tipo, "TEXTO")
        self.assertEqual(tokens[0].valor, "Hola MILPA")

    # Comprueba el registro de caracteres inválidos
    def test_caracter_invalido(self):
        lexer = Lexer("@")
        lexer.analizar()

        self.assertTrue(lexer.errores.hay_errores())

    # Comprueba la posición de los tokens
    def test_posicion(self):
        lexer = Lexer("entero edad")
        tokens = lexer.analizar()

        self.assertEqual(tokens[0].linea, 1)
        self.assertEqual(tokens[0].columna, 1)

        self.assertEqual(tokens[1].linea, 1)
        self.assertEqual(tokens[1].columna, 8)


if __name__ == "__main__":
    unittest.main()
