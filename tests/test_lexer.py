"""Pruebas del analizador léxico. Ejecutar desde la raíz del proyecto:
    python -m unittest tests.test_lexer -v
"""
import re
import unittest
from pathlib import Path

from src.core.errors import ErrorLog
from old.lexer import tokenizar

RAIZ = Path(__file__).resolve().parent


def lex(texto):
    log = ErrorLog()
    return tokenizar(texto, log), log


def tipos_lexemas(texto):
    tokens, _ = lex(texto)
    return [(t.tipo, t.lexema) for t in tokens if t.tipo != "EOF"]


class TestTokens(unittest.TestCase):
    def test_declaracion(self):
        self.assertEqual(
            tipos_lexemas("decimal litros = 5 * 1.5"),
            [("PALABRA_RESERVADA", "decimal"), ("ID", "litros"), ("OPERADOR", "="),
             ("ENTERO", "5"), ("OPERADOR", "*"), ("DECIMAL", "1.5")])

    def test_operadores_dobles(self):
        ops = [l for t, l in tipos_lexemas("<= >= == != < > =")]
        self.assertEqual(ops, ["<=", ">=", "==", "!=", "<", ">", "="])

    def test_acceso_a_campo(self):
        self.assertEqual(
            tipos_lexemas("z.humedad_min"),
            [("ID", "z"), ("DELIMITADOR", "."), ("ID", "humedad_min")])

    def test_si_no_es_una_palabra(self):
        self.assertEqual(tipos_lexemas("si_no"), [("PALABRA_RESERVADA", "si_no")])

    def test_funciones_predefinidas_son_id(self):
        for nombre in ["leer", "lloviendo", "regar", "registrar", "a_entero"]:
            self.assertEqual(tipos_lexemas(nombre), [("ID", nombre)])

    def test_texto_sin_comillas_en_lexema(self):
        self.assertEqual(tipos_lexemas('"Zona "'), [("TEXTO", "Zona ")])

    def test_comentarios_y_espacios(self):
        self.assertEqual(tipos_lexemas("// nada\n   \t entero"), [("PALABRA_RESERVADA", "entero")])

    def test_posiciones(self):
        tokens, _ = lex("entero x\n  y")
        pos = [(t.lexema, t.linea, t.col) for t in tokens if t.tipo != "EOF"]
        self.assertEqual(pos, [("entero", 1, 1), ("x", 1, 8), ("y", 2, 3)])

    def test_termina_en_eof(self):
        tokens, _ = lex("x")
        self.assertEqual(tokens[-1].tipo, "EOF")


class TestErrores(unittest.TestCase):
    def codigos(self, texto):
        _, log = lex(texto)
        return [(e.codigo, e.linea, e.col) for e in log.errores]

    def test_caracter_invalido(self):
        self.assertEqual(self.codigos("entero x = 5 @"), [("E-LEX-01", 1, 14)])

    def test_signo_de_exclamacion_solo(self):
        self.assertEqual(self.codigos("a ! b")[0][0], "E-LEX-01")

    def test_texto_sin_cerrar(self):
        self.assertEqual(self.codigos('registrar("hola)'), [("E-LEX-02", 1, 11)])

    def test_texto_sin_cerrar_no_se_come_la_linea_siguiente(self):
        self.assertEqual(self.codigos('"abc\nentero x @'),
                         [("E-LEX-02", 1, 1), ("E-LEX-01", 2, 10)])

    def test_numeros_mal_formados(self):
        for malo in ["3.", "1.2.3", "12abc", "5.x"]:
            self.assertEqual([c for c, _, _ in self.codigos(malo)], ["E-LEX-03"], malo)

    def test_acumula_varios_errores(self):
        self.assertEqual(len(self.codigos("@ # $")), 3)


class TestArchivosDePrueba(unittest.TestCase):
    """Cada .milpa de tests/ declara en su primera línea el error esperado (o no declara ninguno)."""

    def test_archivos(self):
        archivos = sorted(RAIZ.glob("*/*.milpa"))
        self.assertGreater(len(archivos), 10)
        for ruta in archivos:
            with self.subTest(archivo=f"{ruta.parent.name}/{ruta.name}"):
                texto = ruta.read_text(encoding="utf-8")
                m = re.search(r"ESPERADO:\s*(E-[A-Z]+-\d+)", texto.splitlines()[0])
                esperado = m.group(1) if m else None
                _, log = lex(texto)
                codigos = [e.codigo for e in log.errores]
                if esperado and esperado.startswith("E-LEX"):
                    self.assertIn(esperado, codigos)
                else:
                    self.assertEqual(codigos, [], "no debería tener errores léxicos")


if __name__ == "__main__":
    unittest.main()
