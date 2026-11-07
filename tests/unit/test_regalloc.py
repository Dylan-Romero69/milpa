
import unittest

from src.intermediate import Cuadruplo
from src.regalloc import AsignadorRegistros


class TestAsignadorRegistros(unittest.TestCase):

    def setUp(self):
        self.codigo = [
            Cuadruplo("+", "5", "3", "t1"),
            Cuadruplo("*", "t1", "2", "t2"),
            Cuadruplo("-", "t2", "1", "t3"),
            Cuadruplo("=", "t3", "", "resultado"),
            Cuadruplo("RET")
        ]

        self.asignador = AsignadorRegistros(self.codigo)

    def test_calcular_intervalos(self):
        intervalos = self.asignador.calcular_intervalos()

        self.assertEqual(len(intervalos), 3)

    def test_asignar_registros(self):
        ubicaciones = self.asignador.asignar()

        self.assertIn("t1", ubicaciones)
        self.assertIn("t2", ubicaciones)
        self.assertIn("t3", ubicaciones)

    def test_registros_validos(self):
        ubicaciones = self.asignador.asignar()

        for ubicacion in ubicaciones.values():
            if ubicacion.startswith("$"):
                self.assertIn(
                    ubicacion,
                    self.asignador.REGISTROS_DISPONIBLES
                )

    def test_derramas(self):
        codigo = [
            Cuadruplo("+", "1", "2", "t1"),
            Cuadruplo("+", "3", "4", "t2"),
            Cuadruplo("+", "5", "6", "t3"),
            Cuadruplo("+", "7", "8", "t4"),
            Cuadruplo("+", "t1", "t2", "t5"),
            Cuadruplo("+", "t3", "t4", "t6"),
            Cuadruplo("+", "t5", "t6", "t7"),
            Cuadruplo("RET")
        ]

        asignador = AsignadorRegistros(
            codigo,
            registros=["$t0", "$t1"]
        )

        ubicaciones = asignador.asignar()

        self.assertGreater(len(asignador.derramas), 0)

        for temporal in asignador.derramas:
            self.assertIn(temporal, ubicaciones)


if __name__ == "__main__":
    unittest.main()
