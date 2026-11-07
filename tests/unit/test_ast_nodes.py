
"""
Pruebas unitarias de los nodos AST de MILPA.
"""

import unittest

from src.frontend.ast_nodes import (
    Programa,
    DeclaracionVariable,
    DeclaracionConstante,
    Condicional,
    CicloMientras,
    LlamadaFuncion,
    OperacionBinaria,
    Literal,
    Identificador
)


class TestAST(unittest.TestCase):

    # Comprueba la creación de un programa
    def test_programa(self):
        programa = Programa(instrucciones=[])

        self.assertEqual(programa.instrucciones, [])

    # Comprueba la declaración de una variable
    def test_declaracion_variable(self):
        variable = DeclaracionVariable(
            tipo="entero",
            nombre="humedad",
            valor=Literal(valor=50, tipo="entero")
        )

        self.assertEqual(variable.tipo, "entero")
        self.assertEqual(variable.nombre, "humedad")

    # Comprueba la declaración de una constante
    def test_declaracion_constante(self):
        constante = DeclaracionConstante(
            tipo="entero",
            nombre="MAXIMO",
            valor=Literal(valor=100, tipo="entero")
        )

        self.assertEqual(constante.nombre, "MAXIMO")

    # Comprueba una operación binaria
    def test_operacion_binaria(self):
        operacion = OperacionBinaria(
            izquierda=Identificador(nombre="humedad"),
            operador=">",
            derecha=Literal(valor=30, tipo="entero")
        )

        self.assertEqual(operacion.operador, ">")
        self.assertEqual(operacion.derecha.valor, 30) # type: ignore

    # Comprueba una condición
    def test_condicional(self):
        condicion = Condicional(
            condicion=Literal(valor=True, tipo="booleano"),
            bloque_si=[],
            bloque_si_no=[]
        )

        self.assertIsNotNone(condicion.condicion)

    # Comprueba un ciclo mientras
    def test_ciclo_mientras(self):
        ciclo = CicloMientras(
            condicion=Literal(valor=True, tipo="booleano"),
            instrucciones=[]
        )

        self.assertEqual(ciclo.instrucciones, [])

    # Comprueba una llamada a función
    def test_llamada_funcion(self):
        llamada = LlamadaFuncion(
            nombre="registrar",
            argumentos=[
                Literal(valor="Hola MILPA", tipo="texto")
            ]
        )

        self.assertEqual(llamada.nombre, "registrar")
        self.assertEqual(len(llamada.argumentos), 1)


if __name__ == "__main__":
    unittest.main()
