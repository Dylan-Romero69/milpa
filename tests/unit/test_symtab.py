
import unittest

from src.symtab import Simbolo, TablaSimbolos


class TestTablaSimbolos(unittest.TestCase):

    def setUp(self):
        self.tabla = TablaSimbolos()

    def test_declarar_variable(self):
        simbolo = Simbolo(
            "humedad", "entero", "variable", 50
        )

        resultado = self.tabla.declarar(simbolo)

        self.assertTrue(resultado)

    def test_buscar_variable(self):
        simbolo = Simbolo(
            "humedad", "entero", "variable", 50
        )

        self.tabla.declarar(simbolo)

        encontrado = self.tabla.buscar("humedad")

        self.assertIsNotNone(encontrado)
        assert encontrado is not None
        self.assertEqual(encontrado.tipo, "entero")

    def test_evitar_variables_duplicadas(self):
        primero = Simbolo(
            "humedad", "entero", "variable"
        )

        segundo = Simbolo(
            "humedad", "decimal", "variable"
        )

        self.assertTrue(self.tabla.declarar(primero))
        self.assertFalse(self.tabla.declarar(segundo))

    def test_ambitos(self):
        simbolo = Simbolo(
            "temperatura", "decimal", "variable"
        )

        self.tabla.entrar_ambito()
        self.assertTrue(self.tabla.declarar(simbolo))

        self.assertIsNotNone(
            self.tabla.buscar("temperatura")
        )

        self.tabla.salir_ambito()

        self.assertIsNone(
            self.tabla.buscar("temperatura")
        )

    def test_no_permitir_ocultamiento(self):
        primero = Simbolo(
            "humedad", "entero", "variable"
        )

        segundo = Simbolo(
            "humedad", "decimal", "variable"
        )

        self.tabla.declarar(primero)
        self.tabla.entrar_ambito()

        self.assertFalse(self.tabla.declarar(segundo))


if __name__ == "__main__":
    unittest.main()
