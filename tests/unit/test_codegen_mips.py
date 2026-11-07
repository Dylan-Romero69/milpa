
import unittest

from src.intermediate import Cuadruplo
from src.codegen_mips import GeneradorMIPS


class TestGeneradorMIPS(unittest.TestCase):

    def test_generar_aritmetica(self):
        codigo = [
            Cuadruplo("+", "5", "3", "t1"),
            Cuadruplo("RET")
        ]

        generador = GeneradorMIPS(codigo)
        resultado = generador.generar()

        self.assertIn("li $k0, 5", resultado)
        self.assertIn("li $k1, 3", resultado)
        self.assertIn("add $k0, $k0, $k1", resultado)

    def test_generar_asignacion(self):
        codigo = [
            Cuadruplo("=", "50", "", "humedad"),
            Cuadruplo("RET")
        ]

        resultado = GeneradorMIPS(codigo).generar()

        self.assertIn("var_humedad: .word 0", resultado)
        self.assertIn("li $k0, 50", resultado)
        self.assertIn("sw $k0, var_humedad", resultado)

    def test_generar_salto(self):
        codigo = [
            Cuadruplo("JUMP", "", "", "(3)"),
            Cuadruplo("RET"),
            Cuadruplo("RET")
        ]

        resultado = GeneradorMIPS(codigo).generar()

        self.assertIn("j L3", resultado)
        self.assertIn("L3:", resultado)

    def test_generar_comparacion(self):
        codigo = [
            Cuadruplo("<", "10", "20", "t1"),
            Cuadruplo("RET")
        ]

        resultado = GeneradorMIPS(codigo).generar()

        self.assertIn("slt $k0, $k0, $k1", resultado)

    def test_generar_condicional(self):
        codigo = [
            Cuadruplo(
                "JUMP_IF_FALSE",
                "t1",
                "",
                "(3)"
            ),
            Cuadruplo("RET"),
            Cuadruplo("RET")
        ]

        resultado = GeneradorMIPS(codigo).generar()

        self.assertIn("beq $k0, $zero, L3", resultado)


if __name__ == "__main__":
    unittest.main()
