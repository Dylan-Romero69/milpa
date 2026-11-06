
import unittest

from src.core.errors import ErrorLog


class TestErrorLog(unittest.TestCase):

    def setUp(self):
        self.errores = ErrorLog()

    def test_agregar_error(self):
        self.errores.agregar(
            "semántico", "E-SEM-01", 5, 10,
            "Variable 'humedad' no declarada"
        )

        self.assertTrue(self.errores.hay_errores())
        self.assertEqual(len(self.errores.obtener_errores()), 1)

    def test_multiple_errores(self):
        self.errores.agregar(
            "semántico", "E-SEM-01", 5, 10,
            "Variable no declarada"
        )

        self.errores.agregar(
            "semántico", "E-SEM-03", 8, 4,
            "Tipos incompatibles"
        )

        self.assertEqual(len(self.errores.obtener_errores()), 2)

    def test_sin_errores(self):
        self.assertFalse(self.errores.hay_errores())

    def test_limpiar_errores(self):
        self.errores.agregar(
            "semántico", "E-SEM-01", 5, 10,
            "Variable no declarada"
        )

        self.errores.limpiar()
        self.assertFalse(self.errores.hay_errores())

    def test_imprimir_errores(self):
        self.errores.agregar(
            "semántico", "E-SEM-01", 5, 10,
            "Variable 'humedad' no declarada"
        )

        self.errores.agregar(
            "semántico", "E-SEM-03", 8, 4,
            "Tipos incompatibles"
        )

        print("\n--- ERRORES REGISTRADOS EN MILPA ---")
        self.errores.imprimir()


if __name__ == "__main__":
    unittest.main()
