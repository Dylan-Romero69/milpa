
import unittest

from src.compilacion import compilar_a_mips
from src.huerto_codigo import (
    aplicar_huerto_al_codigo,
    analizar_codigo,
    parcelas_desde_codigo,
)

FILAS, COLUMNAS = 4, 6

CODIGO = '''// Mi huerto
zona norte {
    cultivo: "maiz",
    humedad_min: 30,
    riego_max: 5,
    fila: 2,
    columna: 4
}
zona parcela_1_1 { cultivo: "tomate", humedad_min: 35, riego_max: 6 }
entero humedad_actual_1_1 = 60

entero total = 0
mientras (total < 3) {
    total = total + 1
}
registrar("listo")
'''


def huerto(codigo):
    parcelas, avisos = parcelas_desde_codigo(analizar_codigo(codigo), FILAS, COLUMNAS)
    return parcelas, avisos


class TestCodigoAHuerto(unittest.TestCase):

    def test_ubicacion_por_fila_columna_y_por_nombre(self):
        parcelas, avisos = huerto(CODIGO)
        self.assertEqual(avisos, [])
        self.assertEqual(parcelas[(1, 3)]["zona"], "norte")
        self.assertEqual(parcelas[(0, 0)]["cultivo"], "tomate")
        self.assertEqual(parcelas[(0, 0)]["humedad"], 60)
        self.assertEqual(sum(p["tierra"] for p in parcelas.values()), 2)

    def test_editor_vacio_vacia_el_huerto(self):
        parcelas, _ = huerto("")
        self.assertFalse(any(p["tierra"] for p in parcelas.values()))

    def test_conflictos_y_fuera_de_rango(self):
        parcelas, avisos = huerto(
            'zona a { cultivo: "x", humedad_min: 3, fila: 1, columna: 1 }\n'
            'zona b { cultivo: "y", humedad_min: 3, fila: 1, columna: 1 }\n'
            'zona c { cultivo: "z", humedad_min: 3, fila: 9, columna: 1 }\n'
        )
        self.assertEqual(parcelas[(0, 0)]["zona"], "a")
        self.assertEqual(len(avisos), 2)

    def test_codigo_a_medio_escribir(self):
        modelo = analizar_codigo('zona a { cultivo: "x", humedad_min: 3 }\nzona b { cultivo: "y", hum')
        self.assertEqual([z.nombre for z in modelo.zonas], ["a"])


class TestHuertoACodigo(unittest.TestCase):

    def test_sin_cambios_es_idempotente(self):
        parcelas, _ = huerto(CODIGO)
        primero = aplicar_huerto_al_codigo(CODIGO, parcelas, FILAS, COLUMNAS)
        parcelas, _ = huerto(primero)
        self.assertEqual(aplicar_huerto_al_codigo(primero, parcelas, FILAS, COLUMNAS), primero)

    def test_cambios_del_huerto_conservan_el_resto(self):
        parcelas, _ = huerto(CODIGO)
        parcelas[(0, 0)]["humedad"] = 20
        parcelas[(0, 0)]["estado"] = "seca"
        parcelas[(1, 3)].update(tierra=False, estado="vacía")
        parcelas[(2, 2)].update(
            tierra=True, cultivo="fresa", humedad_min=40, riego_max=4,
            humedad=55, estado="saludable",
        )

        nuevo = aplicar_huerto_al_codigo(CODIGO, parcelas, FILAS, COLUMNAS)

        self.assertNotIn("zona norte", nuevo)
        self.assertIn("entero humedad_actual_1_1 = 20", nuevo)
        self.assertIn("zona parcela_3_3", nuevo)
        self.assertIn("fila: 3", nuevo)
        self.assertIn("mientras (total < 3) {", nuevo)
        self.assertIn('registrar("listo")', nuevo)
        self.assertTrue(nuevo.startswith("// Mi huerto"))
        self.assertEqual(compilar_a_mips(nuevo)[1], [])

        reconstruido, _ = huerto(nuevo)
        self.assertEqual(reconstruido[(2, 2)]["cultivo"], "fresa")
        self.assertFalse(reconstruido[(1, 3)]["tierra"])


class TestCamposFilaColumna(unittest.TestCase):

    def errores(self, codigo):
        return [error.codigo for error in compilar_a_mips(codigo)[1]]

    def test_validos(self):
        self.assertEqual(self.errores('zona a { cultivo: "x", humedad_min: 3, fila: 2, columna: 3 }'), [])

    def test_misma_parcela(self):
        self.assertEqual(self.errores(
            'zona a { cultivo: "x", humedad_min: 3, fila: 1, columna: 1 }\n'
            'zona b { cultivo: "y", humedad_min: 3, fila: 1, columna: 1 }'
        ), ["E-SEM-08"])

    def test_fila_sin_columna(self):
        self.assertEqual(self.errores('zona a { cultivo: "x", humedad_min: 3, fila: 1 }'), ["E-SEM-08"])

    def test_fila_cero(self):
        self.assertEqual(self.errores('zona a { cultivo: "x", humedad_min: 3, fila: 0, columna: 1 }'), ["E-SEM-08"])


if __name__ == "__main__":
    unittest.main()
