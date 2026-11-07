"""Pruebas del analizador sintáctico. Ejecutar desde la raíz del proyecto:
    python -m unittest tests.test_parser -v
"""
import re
import unittest
from pathlib import Path

from old import ast_nodes as A
from src.core.errors import ErrorLog
from old.lexer import tokenizar
from src.parser import parsear

RAIZ = Path(__file__).resolve().parent


def parse(texto):
    log = ErrorLog()
    ast = parsear(tokenizar(texto, log), log)
    return ast, log


def forma(n):
    """Convierte una expresión del AST en tuplas simples para compararla en las pruebas."""
    if isinstance(n, A.Literal):
        return n.valor
    if isinstance(n, A.Var):
        return n.nombre
    if isinstance(n, A.AccesoCampo):
        return f"{n.objeto}.{n.campo}"
    if isinstance(n, A.BinOp):
        return (n.op, forma(n.izq), forma(n.der))
    if isinstance(n, A.UnOp):
        return (n.op, forma(n.operando))
    if isinstance(n, A.Llamada):
        return (n.nombre, [forma(a) for a in n.args])
    raise AssertionError(f"nodo inesperado {n}")


def expr(texto):
    ast, log = parse(f"entero r = {texto}")
    assert not log.hay_errores(), [str(e) for e in log.errores]
    return forma(ast.sentencias[0].valor)


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
        self.assertEqual(expr("leer(z, \"humedad\")"), ("leer", [("z"), "humedad"]))
        self.assertEqual(expr("lloviendo()"), ("lloviendo", []))

    def test_literales(self):
        self.assertEqual(expr("verdadero"), True)
        self.assertEqual(expr("falso"), False)
        self.assertEqual(expr("2.5"), 2.5)
        self.assertEqual(expr('"hola"'), "hola")


class TestSentencias(unittest.TestCase):
    def sentencias(self, texto):
        ast, log = parse(texto)
        self.assertFalse(log.hay_errores(), [str(e) for e in log.errores])
        return ast.sentencias

    def test_declaraciones(self):
        s = self.sentencias('entero a = 1\nconstante decimal PI = 3.14\nzona z { cultivo: "maiz" }')
        self.assertIsInstance(s[0], A.DeclVar)
        self.assertEqual((s[0].tipo_decl, s[0].nombre), ("entero", "a"))
        self.assertIsInstance(s[1], A.DeclConst)
        self.assertEqual(s[1].tipo_decl, "decimal")
        self.assertIsInstance(s[2], A.DeclZona)
        self.assertEqual([c.nombre for c in s[2].campos], ["cultivo"])

    def test_asignacion(self):
        s = self.sentencias("x = x + 1")[0]
        self.assertIsInstance(s, A.Asig)
        self.assertEqual(forma(s.valor), ("+", "x", 1))

    def test_si_con_y_sin_si_no(self):
        s = self.sentencias("si (a) { b = 1 }\nsi (a) { b = 1 } si_no { b = 2 }")
        self.assertIsNone(s[0].sino)
        self.assertEqual(len(s[1].sino), 1)

    def test_bucles(self):
        s = self.sentencias("mientras (a < 3) { a = a + 1 }\nrepetir { a = a + 1 } mientras (a < 3)")
        self.assertIsInstance(s[0], A.Mientras)
        self.assertIsInstance(s[1], A.Repetir)

    def test_para_cada(self):
        s = self.sentencias("para_cada zona z en [a, b, c] { registrar(z.nombre) }")[0]
        self.assertEqual((s.var, s.zonas), ("z", ["a", "b", "c"]))
        self.assertIsInstance(s.cuerpo[0], A.Llamada)

    def test_llamada_como_sentencia(self):
        s = self.sentencias('registrar("Zona ", z.nombre, " sin riego")')[0]
        self.assertEqual(s.nombre, "registrar")
        self.assertEqual(len(s.args), 3)

    def test_bloques_anidados_y_vacios(self):
        s = self.sentencias("mientras (a) { mientras (b) { } }")[0]
        self.assertEqual(s.cuerpo[0].cuerpo, [])

    def test_posiciones(self):
        s = self.sentencias("entero a = 1\n  a = 2")
        self.assertEqual((s[0].linea, s[0].col), (1, 1))
        self.assertEqual((s[1].linea, s[1].col), (2, 3))


class TestErrores(unittest.TestCase):
    def error(self, texto):
        ast, log = parse(texto)
        self.assertIsNone(ast)
        self.assertEqual(len(log.errores), 1)
        e = log.errores[0]
        self.assertEqual(e.codigo, "E-SIN-01")
        return e

    def test_falta_llave_de_cierre(self):
        e = self.error("si (a) {\n  b = 1\n")
        self.assertIn("'}'", e.mensaje)

    def test_falta_nombre_de_variable(self):
        self.assertIn("nombre de variable", self.error("entero = 5").mensaje)

    def test_falta_parentesis(self):
        self.assertIn("'('", self.error("si a > 0 { b = 1 }").mensaje)

    def test_coma_sobrante_en_zona(self):
        self.assertIn("nombre de campo", self.error('zona z { cultivo: "a", }').mensaje)

    def test_expresion_incompleta(self):
        self.assertIn("expresión", self.error("entero a = 1 +").mensaje)

    def test_llave_suelta(self):
        self.assertIn("'}'", self.error("}").mensaje)

    def test_si_no_sin_si(self):
        self.assertIn("si_no", self.error("si_no { a = 1 }").mensaje)

    def test_id_solo(self):
        self.assertIn("'=' o '('", self.error("hola").mensaje)

    def test_no_se_puede_asignar_a_un_campo(self):
        self.error("z.humedad_min = 5")

    def test_posicion_del_error(self):
        e = self.error("entero a = 1\nentero = 5")
        self.assertEqual((e.linea, e.col), (2, 8))


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
                    continue  # lo cubre test_lexer
                ast, log = parse(texto)
                codigos = [e.codigo for e in log.errores]
                if esperado == "E-SIN-01":
                    self.assertEqual(codigos, ["E-SIN-01"])
                else:
                    self.assertEqual(codigos, [], "debería ser sintácticamente válido")
                    self.assertIsInstance(ast, A.Programa)


if __name__ == "__main__":
    unittest.main()
