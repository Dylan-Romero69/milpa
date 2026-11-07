
import unittest

from src.notation import a_postfija, a_prefija


class TestConversionExpresiones(unittest.TestCase):

    def test_postfija_aritmetica(self):
        resultado = a_postfija("5 + 3 * 2")
        self.assertEqual(resultado, "5 3 2 * +")

    def test_prefija_aritmetica(self):
        resultado = a_prefija("5 + 3 * 2")
        self.assertEqual(resultado, "+ 5 * 3 2")

    def test_parentesis(self):
        resultado = a_postfija("(5 + 3) * 2")
        self.assertEqual(resultado, "5 3 + 2 *")

    def test_relacionales(self):
        resultado = a_postfija("humedad >= limite")
        self.assertEqual(resultado, "humedad limite >=")

    def test_operadores_logicos(self):
        resultado = a_postfija("a y b o c")
        self.assertEqual(resultado, "a b y c o")

    def test_negativo(self):
        resultado = a_postfija("-5 + 3")
        self.assertEqual(resultado, "5 u- 3 +")

    def test_error_parentesis(self):
        with self.assertRaises(ValueError):
            a_postfija("(5 + 3")


if __name__ == "__main__":
    unittest.main()
