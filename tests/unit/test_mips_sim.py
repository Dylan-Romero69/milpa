
import unittest
from pathlib import Path

from src.compilacion import compilar_a_mips
from src.huerto import parcelas_desde_estado
from src.intermediate import Cuadruplo
from src.mips_sim import ErrorMIPS, SimuladorMIPS, extraer_estado, formato_flotante
from src.optimizer import Optimizador

RAIZ = Path(__file__).resolve().parents[2]


def ejecutar(codigo, entradas=()):
    """Compila un programa MILPA, ejecuta el MIPS generado y devuelve el simulador."""
    asm, errores = compilar_a_mips(codigo)
    assert asm is not None, [str(e) for e in errores]
    valores = iter(entradas)
    return SimuladorMIPS(asm, lambda tipo, pregunta: next(valores, 0)).ejecutar()


class TestGeneracionEjecutable(unittest.TestCase):

    def test_factorial(self):
        codigo = (RAIZ / "tests/execution/factorial.milpa").read_text(encoding="utf-8")
        sim = ejecutar(codigo)
        self.assertIsNone(sim.error)
        self.assertEqual(sim.texto_salida(), "Factorial de 5 = 120\n")

    def test_fibonacci(self):
        codigo = (RAIZ / "tests/execution/fibonacci.milpa").read_text(encoding="utf-8")
        sim = ejecutar(codigo)
        self.assertEqual(sim.texto_salida().split(), "0 1 1 2 3 5 8 13 21 34".split())

    def test_riego_con_zonas_sensores_y_decimales(self):
        codigo = (RAIZ / "tests/execution/riego_completo.milpa").read_text(encoding="utf-8")
        # norte: humedad 30, no llueve -> riega 12 min (30 + 12 * 2.5 = 60)
        # sur: humedad 50 (>= 35) -> sin riego
        sim = ejecutar(codigo, [30.0, 0, 50.0])
        salida = sim.texto_salida()
        self.assertEqual(salida.count("Regando huerto_norte durante 1 min"), 12)
        self.assertIn("Zona huerto_sur sin riego", salida)
        self.assertIn("Litros totales: 18.0", salida)

    def test_registrar_variable_y_varios_argumentos(self):
        sim = ejecutar('entero a = 7\ndecimal d = 2.5\nbooleano b = a > 3\nregistrar("a=", a, " d=", d, " ", b)')
        self.assertEqual(sim.texto_salida(), "a=7 d=2.5 verdadero\n")

    def test_division_entera_y_decimal(self):
        sim = ejecutar('entero a = 7\nentero b = 2\ndecimal x = a / b\ndecimal z = 7.0 / 2\nregistrar(a / b, " ", x, " ", z, " ", a % b)')
        self.assertEqual(sim.texto_salida(), "3 3.0 3.5 1\n")

    def test_no_hay_etiquetas_invalidas(self):
        codigo = (RAIZ / "tests/execution/riego_completo.milpa").read_text(encoding="utf-8")
        asm, _ = compilar_a_mips(codigo)
        for linea in asm.splitlines():
            if ":" in linea and not linea.lstrip().startswith("#"):
                etiqueta = linea.split(":")[0].strip()
                if '"' not in etiqueta:
                    self.assertRegex(etiqueta, r"^[A-Za-z_][A-Za-z0-9_]*$")


class TestOptimizadorCorregido(unittest.TestCase):

    def test_y_no_se_pliega_con_variables(self):
        codigo = [
            Cuadruplo("y", "t1", "t2", "t3"),
            Cuadruplo("JUMP_IF_FALSE", "t3", "", "(3)"),
            Cuadruplo("RET"),
        ]
        resultado = Optimizador().optimizar(codigo)
        self.assertEqual(resultado[0].operador, "y")

    def test_division_entera_al_plegar(self):
        codigo = [Cuadruplo("/", "7", "2", "t1"), Cuadruplo("=", "t1", "", "x"), Cuadruplo("RET")]
        resultado = Optimizador().optimizar(codigo)
        self.assertEqual(resultado[-2].argumento1, "3")


class TestLectorASM(unittest.TestCase):

    def test_extraer_zonas_y_variables(self):
        sim = ejecutar(
            'zona parcela_2_3 { cultivo: "fresa", humedad_min: 40, riego_max: 4 }\n'
            "entero humedad_actual_2_3 = 25\n"
        )
        estado = extraer_estado(sim)
        self.assertEqual(estado["zonas"], [{
            "nombre": "parcela_2_3", "cultivo": "fresa",
            "humedad_min": 40.0, "riego_max": 4, "fila": 0, "columna": 0,
        }])
        self.assertEqual(estado["variables"]["humedad_actual_2_3"], ("entero", 25))

    def test_huerto_desde_estado(self):
        estado = {
            "zonas": [
                {"nombre": "parcela_2_3", "cultivo": "fresa", "humedad_min": 40.0, "riego_max": 4},
                {"nombre": "norte", "cultivo": "maiz", "humedad_min": 30.0, "riego_max": 5},
            ],
            "variables": {"humedad_actual_2_3": ("entero", 25)},
        }
        parcelas, omitidas = parcelas_desde_estado(estado, 4, 6)
        self.assertEqual(omitidas, [])
        self.assertEqual(parcelas[(1, 2)]["cultivo"], "fresa")
        self.assertEqual(parcelas[(1, 2)]["estado"], "seca")
        self.assertEqual(parcelas[(0, 0)]["cultivo"], "maiz")
        self.assertEqual(sum(p["tierra"] for p in parcelas.values()), 2)

    def test_asm_escrito_a_mano(self):
        asm = """
        .data
        msg: .asciiz "suma="
        .text
        main:
            li $t0, 20
            addi $t1, $t0, 22
            la $a0, msg
            li $v0, 4
            syscall
            move $a0, $t1
            li $v0, 1
            syscall
            li $v0, 10
            syscall
        """
        self.assertEqual(SimuladorMIPS(asm).ejecutar().texto_salida(), "suma=42")

    def test_errores_de_ensamblado(self):
        with self.assertRaises(ErrorMIPS):
            SimuladorMIPS(".text\nmain:\n  addq $t0, $t1, $t2\n")
        with self.assertRaises(ErrorMIPS):
            SimuladorMIPS(".text\nmain:\n  j no_existe\n")

    def test_formato_flotante_como_mars(self):
        self.assertEqual(formato_flotante(18.0), "18.0")
        self.assertEqual(formato_flotante(0.1), "0.1")
        self.assertEqual(formato_flotante(2.5), "2.5")


if __name__ == "__main__":
    unittest.main()
