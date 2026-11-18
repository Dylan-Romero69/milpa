"""Pruebas del análisis semántico. Ejecutar desde la raíz del proyecto:
    python -m unittest tests.test_semantic -v
"""
import re
import unittest
from pathlib import Path

from tests.ayudas import analizar

RAIZ = Path(__file__).resolve().parent
ZONA = 'zona z { cultivo: "maiz", humedad_min: 40.0, riego_max: 15 }\n'


def codigos(texto):
    return [e.codigo for e in analizar(texto)[2].errores]


def valor(texto_expr, preludio=""):
    """Tipo, valor constante y códigos de error de una expresión (evaluada como `decimal r = ...`)."""
    ast, _, log = analizar(f"{preludio}decimal r = {texto_expr}")
    nodo = ast.instrucciones[-1].valor
    return nodo.tipo_sem, nodo.val_const, [e.codigo for e in log.errores]


class TestTiposYConversiones(unittest.TestCase):
    def test_entero_a_decimal_es_implicito(self):
        self.assertEqual(codigos("decimal d = 5"), [])
        self.assertEqual(codigos("decimal d = 1 + 2"), [])

    def test_decimal_a_entero_es_error(self):
        self.assertEqual(codigos("entero a = 2.5"), ["E-SEM-03"])
        self.assertEqual(codigos("entero a = 1 + 2.5"), ["E-SEM-03"])

    def test_a_entero_es_la_conversion_explicita(self):
        self.assertEqual(codigos("entero a = a_entero(2.7)"), [])
        self.assertEqual(codigos("entero a = a_entero(3)"), [])

    def test_tipo_del_resultado(self):
        self.assertEqual(valor("1 + 2")[0], "entero")
        self.assertEqual(valor("1 + 2.0")[0], "decimal")
        ast, _, _ = analizar("booleano b = 1 < 2.5")
        self.assertEqual(ast.instrucciones[0].valor.tipo_sem, "booleano")

    def test_tipos_que_no_se_mezclan(self):
        self.assertEqual(codigos('entero a = 1 + "x"'), ["E-SEM-03"])
        self.assertEqual(codigos("entero a = verdadero + 1"), ["E-SEM-03"])
        self.assertEqual(codigos("texto t = 5"), ["E-SEM-03"])
        self.assertEqual(codigos("booleano b = 1"), ["E-SEM-03"])

    def test_modulo_solo_entre_enteros(self):
        self.assertEqual(codigos("entero a = 7 % 2"), [])
        self.assertEqual(codigos("decimal a = 7.0 % 2"), ["E-SEM-03"])

    def test_operadores_logicos(self):
        self.assertEqual(codigos("booleano b = verdadero y no falso"), [])
        self.assertEqual(codigos("booleano b = 1 y 2"), ["E-SEM-03"])
        self.assertEqual(codigos("booleano b = no 3"), ["E-SEM-03"])

    def test_condicion_debe_ser_booleana(self):
        self.assertEqual(codigos("entero x = 1\nsi (x) { x = 2 }"), ["E-SEM-07"])
        self.assertEqual(codigos("entero x = 1\nmientras (x + 1) { x = 2 }"), ["E-SEM-07"])
        self.assertEqual(codigos("entero x = 1\nsi (x < 2) { x = 2 }"), [])


class TestConstantes(unittest.TestCase):
    def test_plegado_de_constantes(self):
        self.assertEqual(valor("2 * 3 + 1")[1], 7)
        self.assertEqual(valor("5 * 1.5")[1], 7.5)
        self.assertEqual(valor("-(2 + 3)")[1], -5)

    def test_division_entera_trunca_hacia_cero(self):
        self.assertEqual(valor("7 / 2")[1], 3)
        self.assertEqual(valor("-7 / 2")[1], -3)
        self.assertEqual(valor("-7 % 3")[1], -1)

    def test_division_entre_cero(self):
        self.assertEqual(valor("1 / 0")[2], ["E-SEM-09"])
        self.assertEqual(valor("5 % 0")[2], ["E-SEM-09"])

    def test_una_variable_no_es_constante(self):
        self.assertIsNone(valor("a + 1", "entero a = 3\n")[1])

    def test_una_constante_si(self):
        self.assertEqual(valor("K * 2", "constante entero K = 4\n")[1], 8)

    def test_constante_necesita_valor_conocido(self):
        self.assertEqual(codigos("entero a = 1\nconstante entero K = a"), ["E-SEM-10"])

    def test_no_se_puede_asignar_a_una_constante(self):
        self.assertEqual(codigos("constante entero K = 1\nK = 2"), ["E-SEM-06"])


class TestAmbitos(unittest.TestCase):
    def test_variable_no_declarada(self):
        self.assertEqual(codigos("entero a = b"), ["E-SEM-01"])
        self.assertEqual(codigos("b = 1"), ["E-SEM-01"])

    def test_no_se_puede_usar_su_propio_valor_al_declararse(self):
        self.assertEqual(codigos("entero a = a + 1"), ["E-SEM-01"])

    def test_variable_de_bloque_no_existe_fuera(self):
        self.assertEqual(codigos("entero k = 1\nsi (k > 0) { entero t = 1 }\nk = t"), ["E-SEM-01"])

    def test_variable_global_se_ve_en_el_bloque(self):
        self.assertEqual(codigos("entero k = 1\nsi (k > 0) { k = 2 }"), [])

    def test_redeclaracion_en_el_mismo_ambito(self):
        self.assertEqual(codigos("entero a = 1\nentero a = 2"), ["E-SEM-02"])

    def test_no_se_permite_ocultar_una_variable_externa(self):
        self.assertEqual(codigos("entero a = 1\nsi (a > 0) { entero a = 2 }"), ["E-SEM-02"])

    def test_mismo_nombre_en_bloques_hermanos_si_vale(self):
        self.assertEqual(codigos("entero k = 1\nsi (k > 0) { entero t = 1 }\nsi (k > 0) { entero t = 2 }"), [])

    def test_nombres_prohibidos(self):
        self.assertEqual(codigos("entero leer = 1"), ["E-SEM-02"])
        self.assertEqual(codigos("entero y = 1"), ["E-SEM-02"])
        self.assertEqual(codigos("entero no = 1"), ["E-SEM-02"])

    def test_tabla_de_direcciones(self):
        ast, sem, _ = analizar("entero k = 1\nsi (k > 0) { entero t = 1 }\nsi (k > 0) { entero t = 2 }")
        simbolos = sem.tabla.obtener_todos()
        # Todos los símbolos quedan registrados aunque su ámbito ya se haya cerrado.
        self.assertEqual([s.nombre for s in simbolos], ["k", "t", "t"])
        self.assertEqual([s.ambito for s in simbolos], [0, 1, 1])
        self.assertEqual([s.direccion for s in simbolos], ["var_k", "var_t", "var_t"])


class TestFunciones(unittest.TestCase):
    def test_funcion_no_definida(self):
        self.assertEqual(codigos(ZONA + "abrir(z)"), ["E-SEM-04"])

    def test_cantidad_de_argumentos(self):
        self.assertEqual(codigos(ZONA + "regar(z)"), ["E-SEM-05"])
        self.assertEqual(codigos("booleano b = lloviendo(1)"), ["E-SEM-05"])

    def test_tipo_de_argumentos(self):
        self.assertEqual(codigos(ZONA + "regar(z, 2.5)"), ["E-SEM-05"])
        self.assertEqual(codigos('decimal h = leer(5, "humedad")'), ["E-SEM-05"])
        self.assertEqual(codigos('entero a = a_entero("x")'), ["E-SEM-05"])

    def test_funcion_sin_valor_no_se_puede_usar_en_expresion(self):
        self.assertEqual(codigos(ZONA + "entero a = regar(z, 1)"), ["E-SEM-03"])

    def test_registrar_acepta_varios_argumentos(self):
        self.assertEqual(codigos(ZONA + 'registrar("a", 1, 2.5, verdadero, z.nombre)'), [])
        self.assertEqual(codigos("registrar()"), ["E-SEM-05"])
        self.assertEqual(codigos(ZONA + "registrar(z)"), ["E-SEM-05"])


class TestZonas(unittest.TestCase):
    def test_zona_valida_y_direccion(self):
        _, sem, log = analizar(ZONA)
        self.assertFalse(log.hay_errores())
        z = sem.tabla.buscar("z")
        self.assertEqual((z.tipo, z.direccion, z.tamano), ("zona", "zona_z", 16))
        self.assertEqual(z.valor["riego_max"], 15)

    def test_riego_max_por_defecto(self):
        _, sem, _ = analizar('zona z { cultivo: "a", humedad_min: 40 }')
        self.assertEqual(sem.tabla.buscar("z").valor["riego_max"], 30)
        self.assertEqual(sem.tabla.buscar("z").valor["humedad_min"], 40.0)

    def test_riego_max_solo_acepta_enteros_positivos(self):
        self.assertEqual(codigos('zona z { cultivo: "a", humedad_min: 1.0, riego_max: "hola" }'), ["E-SEM-03"])
        self.assertEqual(codigos('zona z { cultivo: "a", humedad_min: 1.0, riego_max: 2.5 }'), ["E-SEM-03"])
        self.assertEqual(codigos('zona z { cultivo: "a", humedad_min: 1.0, riego_max: verdadero }'), ["E-SEM-03"])
        self.assertEqual(codigos('zona z { cultivo: "a", humedad_min: 1.0, riego_max: 0 }'), ["E-DOM-02"])
        self.assertEqual(codigos('zona z { cultivo: "a", humedad_min: 1.0, riego_max: -5 }'), ["E-DOM-02"])

    def test_campos(self):
        self.assertEqual(codigos('zona z { cultivo: "a" }'), ["E-SEM-08"])
        self.assertEqual(codigos('zona z { cultivo: "a", humedad_min: 1.0, color: "r" }'), ["E-SEM-08"])
        self.assertEqual(codigos('zona z { cultivo: "a", cultivo: "b", humedad_min: 1.0 }'), ["E-SEM-08"])
        self.assertEqual(codigos("zona z { cultivo: 5, humedad_min: 1.0 }"), ["E-SEM-03"])

    def test_zona_solo_en_el_ambito_global(self):
        self.assertEqual(codigos("entero k = 1\nsi (k > 0) {\n" + ZONA + "}"), ["E-SEM-08"])

    def test_acceso_a_campos(self):
        self.assertEqual(codigos(ZONA + "decimal h = z.humedad_min\ntexto t = z.cultivo\nentero r = z.riego_max"), [])
        self.assertEqual(codigos(ZONA + "decimal h = z.color"), ["E-SEM-08"])
        self.assertEqual(codigos("entero a = 1\nentero b = a.x"), ["E-SEM-03"])

    def test_una_zona_no_es_un_numero(self):
        self.assertEqual(codigos(ZONA + "entero a = z + 1"), ["E-SEM-03"])
        self.assertEqual(codigos(ZONA + "z = 1"), ["E-SEM-03"])


class TestParaCada(unittest.TestCase):
    DOS = ZONA + 'zona w { cultivo: "b", humedad_min: 30.0, riego_max: 5 }\n'

    def test_alias_vale_dentro_del_bloque(self):
        self.assertEqual(codigos(self.DOS + "para_cada zona q en [z, w] { decimal h = q.humedad_min }"), [])

    def test_alias_no_existe_fuera(self):
        self.assertEqual(codigos(self.DOS + "para_cada zona q en [z, w] { }\nregar(q, 1)"), ["E-SEM-01"])

    def test_zona_inexistente_o_que_no_es_zona(self):
        self.assertEqual(codigos("para_cada zona q en [nada] { }"), ["E-SEM-01"])
        self.assertEqual(codigos("entero a = 1\npara_cada zona q en [a] { }"), ["E-SEM-03"])

    def test_riego_se_valida_contra_cada_zona_de_la_lista(self):
        # regar(q, 10) cabe en z (15) pero no en w (5)
        errores = analizar(self.DOS + "para_cada zona q en [z, w] { regar(q, 10) }")[2].errores
        self.assertEqual([e.codigo for e in errores], ["E-DOM-02"])
        self.assertIn("'w'", errores[0].mensaje)


class TestDominio(unittest.TestCase):
    def test_v1_sensores(self):
        self.assertEqual(codigos(ZONA + 'decimal h = leer(z, "humedad")\ndecimal t = leer(z, "temperatura")'), [])
        self.assertEqual(codigos(ZONA + 'decimal v = leer(z, "viento")'), ["E-DOM-01"])
        self.assertEqual(codigos(ZONA + 'texto s = "humedad"\ndecimal v = leer(z, s)'), ["E-DOM-01"])
        self.assertEqual(codigos(ZONA + 'constante texto S = "humedad"\ndecimal v = leer(z, S)'), [])

    def test_v2_riego_maximo(self):
        self.assertEqual(codigos(ZONA + "regar(z, 15)"), [])
        self.assertEqual(codigos(ZONA + "regar(z, 16)"), ["E-DOM-02"])
        self.assertEqual(codigos(ZONA + "regar(z, 0)"), ["E-DOM-02"])
        self.assertEqual(codigos('zona w { cultivo: "a", humedad_min: 1.0 }\nregar(w, 31)'), ["E-DOM-02"])
        self.assertEqual(codigos(ZONA + "entero m = 3\nregar(z, m)"), [])   # variable: no se puede validar

    def test_v3_humedad_fuera_de_rango(self):
        self.assertEqual(codigos('zona w { cultivo: "a", humedad_min: 140.0 }'), ["E-DOM-03"])
        self.assertEqual(codigos('zona w { cultivo: "a", humedad_min: -5.0 }'), ["E-DOM-03"])
        self.assertEqual(codigos(ZONA + 'decimal h = leer(z, "humedad")\nbooleano b = h < 140.0'), ["E-DOM-03"])
        self.assertEqual(codigos(ZONA + 'decimal h = leer(z, "humedad")\nbooleano b = h < 60.0'), [])
        self.assertEqual(codigos(ZONA + 'decimal t = leer(z, "temperatura")\nbooleano b = t < 140.0'), [])
        self.assertEqual(codigos(ZONA + "booleano b = z.humedad_min > 101"), ["E-DOM-03"])


class TestVariosErrores(unittest.TestCase):
    def test_acumula_errores_y_no_se_cascadea(self):
        self.assertEqual(codigos("entero a = x\nentero b = 2.5\nentero c = a + b"),
                         ["E-SEM-01", "E-SEM-03"])

    def test_posicion_del_error_de_tipos(self):
        e = analizar("entero m = 2.5 * 2")[2].errores[0]
        self.assertEqual((e.codigo, e.linea, e.col), ("E-SEM-03", 1, 12))


class TestArchivosDePrueba(unittest.TestCase):
    def test_archivos(self):
        archivos = sorted(RAIZ.glob("*/*.milpa"))
        self.assertGreater(len(archivos), 10)
        for ruta in archivos:
            with self.subTest(archivo=f"{ruta.parent.name}/{ruta.name}"):
                texto = ruta.read_text(encoding="utf-8")
                m = re.search(r"ESPERADO:\s*(E-[A-Z]+-\d+)", texto.splitlines()[0])
                esperado = m.group(1) if m else None
                if esperado and esperado.startswith(("E-LEX", "E-SIN")):
                    continue  # los cubren test_lexer y test_parser
                self.assertEqual(codigos(texto), [esperado] if esperado else [])


if __name__ == "__main__":
    unittest.main()
