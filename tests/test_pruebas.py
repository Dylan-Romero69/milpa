"""Pruebas de programas con errores o entradas inusuales.

Cada caso de tests/casos_prueba.py dice si el programa debe compilar ('ok'), debe rechazarse
con un error ('error') o puede hacer cualquiera de las dos cosas pero sin que el compilador
se caiga ('sin_caida'). Un error de Python dentro del compilador SIEMPRE es una falla.

Ejecutar desde la raíz del proyecto:
    python -m unittest tests.test_pruebas -v
"""
import io
import contextlib
import unittest

from tests.ayudas import compilar
from tests.casos_prueba import CASOS, fases_validas


class TestProgramasDePrueba(unittest.TestCase):

    def test_casos(self):
        self.assertGreater(len(CASOS), 200)
        for nombre, programa, esperado in CASOS:
            with self.subTest(caso=nombre):
                with contextlib.redirect_stdout(io.StringIO()):
                    veredicto, codigos = compilar(programa)
                if esperado == "sin_caida":
                    return_ok = True
                else:
                    return_ok = veredicto == esperado
                self.assertTrue(
                    return_ok,
                    f"se esperaba '{esperado}' pero el compilador dio '{veredicto}' {codigos}",
                )
                if esperado == "error":
                    fases = fases_validas(nombre)
                    if fases:
                        self.assertTrue(
                            codigos[0].startswith(fases),
                            f"debía rechazarse en la fase {fases} pero el primer error fue {codigos}",
                        )


if __name__ == "__main__":
    unittest.main()
