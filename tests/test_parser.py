"""Pruebas del analizador sintáctico (y el AST). Ejecutar desde la raíz del proyecto:
    python -m unittest tests.test_parser -v
"""
import re
import unittest
from pathlib import Path

from src.frontend import ast_nodes as A
from tests.ayudas import parsear

RAIZ = Path(__file__).resolve().parent


def forma(n):
    """Convierte una expresión del AST en tuplas simples para compararla en las pruebas."""
    if isinstance(n, A.Literal):
        return n.valor
    if isinstance(n, A.Identificador):
        return n.nombre
    if isinstance(n, A.AccesoCampo):
        return f"{n.zona}.{n.campo}"
    if isinstance(n, A.OperacionBinaria):
        return (n.operador, forma(n.izquierda), forma(n.derecha))
    if isinstance(n, A.OperacionUnaria):
        return ("neg" if n.operador == "-" else n.operador, forma(n.operando))
    if isinstance(n, A.LlamadaFuncion):
        return (n.nombre, [forma(a) for a in n.argumentos])
    raise AssertionError(f"nodo inesperado {n}")


def expr(texto):
    ast, log = parsear(f"entero r = {texto}")
    assert not log.hay_errores(), [str(e) for e in log.errores]
    return forma(ast.instrucciones[0].valor)


class TestExpresiones(unittest.TestCase):
    def test_precedencia_aritmetica(self):
        self.assertEqual(expr("1 + 2 * 3"), ("+", 1, ("*", 2, 3)))

    def test_parentesis(self):
        self.assertEqual(expr("(1 + 2) * 3"), ("*", ("+", 1, 2), 3))

    def test_asociatividad_izquierda(self):
        self.assertEqual(expr("10 - 3 - 2"), ("-", ("-", 10, 3), 2))
        self.assertEqual(expr("8 / 4 / 2"), ("/", ("/", 8, 4), 2))

    def test_menos_unario(self):
        self.assertEqual(expr("-a * b"), ("*", ("neg", "a"), "b"))

    def test_no_se_aplica_a_la_comparacion(self):
        self.assertEqual(expr("no a < b"), ("no", ("<", "a", "b")))

    def test_y_tiene_mas_precedencia_que_o(self):
        self.assertEqual(expr("a o b y c"), ("o", "a", ("y", "b", "c")))

    def test_comparaciones_unidas_por_y(self):
        self.assertEqual(expr("a < 60.0 y m < 15"),
                         ("y", ("<", "a", 60.0), ("<", "m", 15)))

    def test_acceso_a_campo_y_llamadas(self):
        self.assertEqual(expr("z.humedad_min"), "z.humedad_min")
        self.assertEqual(expr('leer(z, "humedad")'), ("leer", ["z", "humedad"]))
        self.assertEqual(expr("lloviendo()"), ("lloviendo", []))

    def test_literales(self):
        self.assertEqual(expr("verdadero"), True)
        self.assertEqual(expr("falso"), False)
        self.assertEqual(expr("2.5"), 2.5)
        self.assertEqual(expr('"hola"'), "hola")

    def test_los_operadores_tienen_posicion(self):
        ast, _ = parsear("entero r = 1 +\n   2 * 3")
        suma = ast.instrucciones[0].valor
        self.assertEqual((suma.linea, suma.columna), (1, 14))
        self.assertEqual((suma.derecha.linea, suma.derecha.columna), (2, 6))


class TestSentencias(unittest.TestCase):
    def sentencias(self, texto):
        ast, log = parsear(texto)
        self.assertFalse(log.hay_errores(), [str(e) for e in log.errores])
        return ast.instrucciones

    def test_declaraciones(self):
        s = self.sentencias('entero a = 1\nconstante decimal PI = 3.14\nzona z { cultivo: "maiz" }')
        self.assertIsInstance(s[0], A.DeclaracionVariable)
        self.assertEqual((s[0].tipo, s[0].nombre), ("entero", "a"))
        self.assertIsInstance(s[1], A.DeclaracionConstante)
        self.assertEqual(s[1].tipo, "decimal")
        self.assertIsInstance(s[2], A.DeclaracionZona)
        self.assertEqual([c.nombre for c in s[2].campos], ["cultivo"])

    def test_asignacion(self):
        s = self.sentencias("x = x + 1")[0]
        self.assertIsInstance(s, A.Asignacion)
        self.assertEqual(forma(s.valor), ("+", "x", 1))

    def test_si_con_y_sin_si_no(self):
        s = self.sentencias("si (a) { b = 1 }\nsi (a) { b = 1 } si_no { b = 2 }")
        self.assertEqual(s[0].bloque_si_no, [])
        self.assertEqual(len(s[1].bloque_si_no), 1)

    def test_mientras(self):
        s = self.sentencias("mientras (a < 3) { a = a + 1 }")[0]
        self.assertIsInstance(s, A.CicloMientras)

    def test_para_cada(self):
        s = self.sentencias("para_cada zona z en [a, b, c] { registrar(z.nombre) }")[0]
        self.assertEqual((s.variable, s.zonas), ("z", ["a", "b", "c"]))
        self.assertIsInstance(s.instrucciones[0], A.LlamadaFuncion)

    def test_llamada_como_sentencia(self):
        s = self.sentencias('registrar("Zona ", z.nombre, " sin riego")')[0]
        self.assertEqual(s.nombre, "registrar")
        self.assertEqual(len(s.argumentos), 3)

    def test_bloques_anidados_y_vacios(self):
        s = self.sentencias("mientras (a) { mientras (b) { } }")[0]
        self.assertEqual(s.instrucciones[0].instrucciones, [])

    def test_posiciones(self):
        s = self.sentencias("entero a = 1\n  a = 2")
        self.assertEqual((s[0].linea, s[0].columna), (1, 1))
        self.assertEqual((s[1].linea, s[1].columna), (2, 3))


class TestErroresSintacticos(unittest.TestCase):
    def error(self, texto):
        ast, log = parsear(texto)
        self.assertIsNone(ast)
        self.assertTrue(log.hay_errores())
        self.assertEqual(log.errores[0].codigo, "E-SIN-01")
        return log.errores[0]

    def test_falta_llave_de_cierre(self):
        self.error("si (a) {\n  b = 1\n")

    def test_falta_nombre_de_variable(self):
        self.error("entero = 5")

    def test_falta_parentesis(self):
        self.error("si a > 0 { b = 1 }")

    def test_coma_sobrante_en_zona(self):
        self.error('zona z { cultivo: "a", }')

    def test_expresion_incompleta(self):
        self.error("entero a = 1 +")

    def test_llave_suelta(self):
        self.error("}")

    def test_si_no_sin_si(self):
        self.error("si_no { a = 1 }")

    def test_id_solo(self):
        self.error("hola")

    def test_no_se_puede_asignar_a_un_campo(self):
        self.error("z.humedad_min = 5")

    def test_posicion_del_error(self):
        e = self.error("entero a = 1\nentero = 5")
        self.assertEqual(e.linea, 2)


class TestArchivosDePrueba(unittest.TestCase):
    """Los .milpa de tests/ declaran en su primera línea el error esperado (o ninguno)."""

    def test_archivos(self):
        archivos = sorted(RAIZ.glob("*/*.milpa"))
        self.assertGreater(len(archivos), 10)
        for ruta in archivos:
            with self.subTest(archivo=f"{ruta.parent.name}/{ruta.name}"):
                texto = ruta.read_text(encoding="utf-8")
                m = re.search(r"ESPERADO:\s*(E-[A-Z]+-\d+)", texto.splitlines()[0])
                esperado = m.group(1) if m else None
                if esperado and esperado.startswith("E-LEX"):
                    continue
                ast, log = parsear(texto)
                codigos = [e.codigo for e in log.errores]
                if esperado == "E-SIN-01":
                    self.assertEqual(codigos[:1], ["E-SIN-01"])
                else:
                    self.assertEqual(codigos, [], "debería ser sintácticamente válido")
                    self.assertIsInstance(ast, A.Programa)


if __name__ == "__main__":
    unittest.main()
