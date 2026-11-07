
import unittest

from src.frontend.lexer import Lexer
from src.parser import Parser
from src.intermediate import GeneradorIntermedio


def generar_codigo(codigo):
    lexer = Lexer(codigo)
    tokens = lexer.analizar()

    parser = Parser(tokens)
    arbol = parser.analizar()

    generador = GeneradorIntermedio()
    cuadruplos = generador.generar(arbol)

    return cuadruplos


class TestGeneradorIntermedio(unittest.TestCase):

    def test_declaracion_variable(self):
        codigo = "entero humedad = 50"

        cuadruplos = generar_codigo(codigo)

        self.assertEqual(len(cuadruplos), 2)
        self.assertEqual(cuadruplos[0].operador, "=")
        self.assertEqual(cuadruplos[0].resultado, "humedad")
        self.assertEqual(cuadruplos[-1].operador, "RET")

    def test_operacion_aritmetica(self):
        codigo = """
entero humedad = 50
humedad = humedad + 5
"""

        cuadruplos = generar_codigo(codigo)

        self.assertEqual(len(cuadruplos), 4)
        self.assertEqual(cuadruplos[1].operador, "+")
        self.assertEqual(cuadruplos[1].resultado, "t1")
        self.assertEqual(cuadruplos[-1].operador, "RET")

    def test_condicional(self):
        codigo = """
entero humedad = 50

si (humedad > 30) {
    humedad = 60
}
"""

        cuadruplos = generar_codigo(codigo)

        operadores = [c.operador for c in cuadruplos]

        self.assertIn("JUMP_IF_FALSE", operadores)
        self.assertIn("RET", operadores)

        salto = next(
            c for c in cuadruplos
            if c.operador == "JUMP_IF_FALSE"
        )

        self.assertTrue(salto.resultado.startswith("("))
        self.assertTrue(salto.resultado.endswith(")"))

    def test_ciclo_mientras(self):
        codigo = """
entero humedad = 50

mientras (humedad < 80) {
    humedad = humedad + 5
}
"""

        cuadruplos = generar_codigo(codigo)

        operadores = [c.operador for c in cuadruplos]

        self.assertIn("JUMP", operadores)
        self.assertIn("JUMP_IF_FALSE", operadores)
        self.assertEqual(cuadruplos[-1].operador, "RET")


if __name__ == "__main__":
    unittest.main()
