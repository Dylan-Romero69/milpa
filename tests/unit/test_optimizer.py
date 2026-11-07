
import unittest

from src.intermediate import Cuadruplo
from src.optimizer import Optimizador


class TestOptimizador(unittest.TestCase):

    def crear_optimizador(self, codigo):
        optimizador = Optimizador()
        optimizador.cuadruplos = codigo
        return optimizador

    def test_optimizacion_local(self):
        codigo = [
            Cuadruplo("+", "5", "3", "t1"),
            Cuadruplo("=", "t1", "", "resultado"),
            Cuadruplo("RET")
        ]

        optimizador = self.crear_optimizador(codigo)
        optimizador.optimizar_local()

        self.assertEqual(codigo[0].operador, "=")
        self.assertEqual(codigo[0].argumento1, "8")
        self.assertEqual(codigo[1].argumento1, "8")

    def test_optimizacion_global(self):
        codigo = [
            Cuadruplo("+", "5", "3", "t1"),
            Cuadruplo("=", "10", "", "resultado"),
            Cuadruplo("RET")
        ]

        optimizador = self.crear_optimizador(codigo)
        optimizador.optimizar_global()

        self.assertEqual(codigo[0].operador, "NOP")
        self.assertEqual(optimizador.metricas["globales"], 1)

    def test_optimizacion_mirilla(self):
        codigo = [
            Cuadruplo("+", "humedad", "0", "t1"),
            Cuadruplo("=", "t1", "", "resultado"),
            Cuadruplo("RET")
        ]

        optimizador = self.crear_optimizador(codigo)
        optimizador.optimizar_mirilla()

        self.assertEqual(codigo[0].operador, "=")
        self.assertEqual(codigo[0].argumento1, "humedad")

    def test_optimizacion_ciclos(self):
        codigo = [
            Cuadruplo("=", "2", "", "humedad"),
            Cuadruplo("+", "humedad", "5", "t1"),
            Cuadruplo("+", "humedad", "5", "t2"),
            Cuadruplo("JUMP", "", "", "(2)"),
            Cuadruplo("RET")
        ]

        optimizador = self.crear_optimizador(codigo)
        optimizador.optimizar_ciclos()

        self.assertEqual(codigo[2].operador, "=")
        self.assertEqual(codigo[2].argumento1, "t1")
        self.assertEqual(optimizador.metricas["ciclos"], 1)


if __name__ == "__main__":
    unittest.main()
