
from dataclasses import dataclass

from src.frontend.ast_nodes import (
    Programa,
    DeclaracionVariable,
    DeclaracionConstante,
    DeclaracionZona,
    Asignacion,
    Condicional,
    CicloMientras,
    CicloParaCada,
    LlamadaFuncion,
    OperacionBinaria,
    OperacionUnaria,
    Literal,
    Identificador,
    AccesoCampo,
)


@dataclass
class Cuadruplo:
    operador: str
    argumento1: str = ""
    argumento2: str = ""
    resultado: str = ""

    def __str__(self):
        return (
            f"({self.operador}, {self.argumento1}, "
            f"{self.argumento2}, {self.resultado})"
        )


class GeneradorIntermedio:

    def __init__(self):
        self.cuadruplos = []
        self.contador_temporales = 0
        self.etiquetas = {}
        self.contador_etiquetas = 0

    def nuevo_temporal(self):
        self.contador_temporales += 1
        return f"t{self.contador_temporales}"

    def nueva_etiqueta(self):
        self.contador_etiquetas += 1
        return f"L{self.contador_etiquetas}"

    def agregar(self, operador, argumento1="", argumento2="", resultado=""):
        cuadruplo = Cuadruplo(
            operador,
            str(argumento1),
            str(argumento2),
            str(resultado)
        )

        self.cuadruplos.append(cuadruplo)
        return len(self.cuadruplos)

    def reservar_salto(self, operador, argumento1=""):
        """Agrega un salto pendiente de destino."""
        return self.agregar(operador, argumento1, "", "?")


    def completar_salto(self, posicion, destino):
        """Completa el destino de un salto."""
        destino = str(destino)

        if not destino.startswith("("):
            destino = f"({destino})"

        self.cuadruplos[posicion - 1].resultado = destino


    def generar(self, arbol):
        self.cuadruplos = []
        self.contador_temporales = 0
        self.contador_etiquetas = 0

        if not isinstance(arbol, Programa):
            raise TypeError("Se esperaba un nodo Programa.")

        self.generar_instrucciones(arbol.instrucciones)

        # Finalización del programa
        self.agregar("RET")

        return self.cuadruplos

    def generar_instrucciones(self, instrucciones):
        for instruccion in instrucciones:
            self.generar_nodo(instruccion)

    def generar_nodo(self, nodo):

        if isinstance(nodo, DeclaracionVariable):
            valor = self.generar_expresion(nodo.valor)
            self.agregar("=", valor, "", nodo.nombre)

        elif isinstance(nodo, DeclaracionConstante):
            valor = self.generar_expresion(nodo.valor)
            self.agregar("=", valor, "", nodo.nombre)

        elif isinstance(nodo, DeclaracionZona):
            for campo in nodo.campos:
                valor = self.generar_expresion(campo.valor)
                self.agregar("CAMPO", nodo.nombre, campo.nombre, valor)

        elif isinstance(nodo, Asignacion):
            valor = self.generar_expresion(nodo.valor)
            self.agregar("=", valor, "", nodo.nombre)

        elif isinstance(nodo, Condicional):
            self.generar_condicional(nodo)

        elif isinstance(nodo, CicloMientras):
            self.generar_mientras(nodo)

        elif isinstance(nodo, CicloParaCada):
            self.generar_para_cada(nodo)

        elif isinstance(nodo, LlamadaFuncion):
            self.generar_llamada(nodo)

    def generar_condicional(self, nodo):
        condicion = self.generar_expresion(nodo.condicion)

        salto_falso = self.reservar_salto(
            "JUMP_IF_FALSE", condicion
        )

        self.generar_instrucciones(nodo.bloque_si)

        if nodo.bloque_si_no:
            salto_fin = self.reservar_salto("JUMP")

            destino_falso = len(self.cuadruplos) + 1
            self.completar_salto(salto_falso, destino_falso)

            self.generar_instrucciones(nodo.bloque_si_no)

            destino_fin = len(self.cuadruplos) + 1
            self.completar_salto(salto_fin, destino_fin)

        else:
            destino_falso = len(self.cuadruplos) + 1
            self.completar_salto(salto_falso, destino_falso)

    def generar_mientras(self, nodo):
        inicio = len(self.cuadruplos) + 1

        condicion = self.generar_expresion(nodo.condicion)

        salto_fin = self.reservar_salto(
            "JUMP_IF_FALSE", condicion
        )

        self.generar_instrucciones(nodo.instrucciones)

        self.agregar("JUMP", "", "", f"({inicio})")

        destino_fin = len(self.cuadruplos) + 1
        self.completar_salto(salto_fin, f"({destino_fin})")

    def generar_para_cada(self, nodo):
        inicio = len(self.cuadruplos) + 1

        self.agregar(
            "ITER_INICIO",
            nodo.variable,
            ",".join(nodo.zonas)
        )

        self.agregar(
            "ITER_SIGUIENTE",
            nodo.variable
        )

        salto_fin = self.reservar_salto("JUMP_IF_FALSE", nodo.variable)

        self.generar_instrucciones(nodo.instrucciones)

        self.agregar("JUMP", "", "", f"({inicio + 1})")

        destino_fin = len(self.cuadruplos) + 1
        self.completar_salto(salto_fin, f"({destino_fin})")

    def generar_llamada(self, nodo):
        for argumento in nodo.argumentos:
            valor = self.generar_expresion(argumento)
            self.agregar("PARAM", valor)

        resultado = ""

        if nodo.nombre in {"leer", "lloviendo", "a_entero"}:
            resultado = self.nuevo_temporal()

        self.agregar(
            "CALL",
            nodo.nombre,
            len(nodo.argumentos), # type: ignore
            resultado
        )

    def generar_expresion(self, nodo):

        if nodo is None:
            return ""

        if isinstance(nodo, Literal):
            return str(nodo.valor)

        if isinstance(nodo, Identificador):
            return nodo.nombre

        if isinstance(nodo, AccesoCampo):
            return f"{nodo.zona}.{nodo.campo}"

        if isinstance(nodo, OperacionBinaria):
            izquierda = self.generar_expresion(nodo.izquierda)
            derecha = self.generar_expresion(nodo.derecha)

            temporal = self.nuevo_temporal()

            self.agregar(
                nodo.operador,
                izquierda,
                derecha,
                temporal
            )

            return temporal

        if isinstance(nodo, OperacionUnaria):
            operando = self.generar_expresion(nodo.operando)
            temporal = self.nuevo_temporal()

            self.agregar(
                "UNARIO_" + nodo.operador,
                operando,
                "",
                temporal
            )

            return temporal

        if isinstance(nodo, LlamadaFuncion):
            self.generar_llamada(nodo)

            if nodo.nombre in {"leer", "lloviendo", "a_entero"}:
                return f"t{self.contador_temporales}"

            return ""

        return ""

    def imprimir(self):
        print("\n========== CODIGO INTERMEDIO ==========")

        print(
            f"{'N':<5}"
            f"{'OPERADOR':<20}"
            f"{'ARGUMENTO 1':<20}"
            f"{'ARGUMENTO 2':<20}"
            f"{'RESULTADO':<15}"
        )

        print("-" * 80)

        for i, cuadruplo in enumerate(self.cuadruplos, start=1):

            resultado = cuadruplo.resultado

            # Mostrar los destinos de los saltos entre paréntesis
            if cuadruplo.operador in {"JUMP", "JUMP_IF_FALSE"}:
                if resultado and not resultado.startswith("("):
                    resultado = f"({resultado})"

            print(
                f"{i:<5}"
                f"{cuadruplo.operador:<20}"
                f"{cuadruplo.argumento1:<20}"
                f"{cuadruplo.argumento2:<20}"
                f"{resultado:<15}"
            )

        print("=" * 80)
