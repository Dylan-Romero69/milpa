
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


# Tipo que devuelve cada función predefinida.
RETORNO_FUNCIONES = {
    "leer": "decimal",
    "lloviendo": "booleano",
    "a_entero": "entero",
}

OPERADORES_BOOLEANOS = {"<", ">", "<=", ">=", "==", "!=", "y", "o"}


def literal_texto(valor):
    """Representa un texto literal entre comillas para distinguirlo de un nombre."""
    escapado = str(valor).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escapado}"'


class GeneradorIntermedio:

    def __init__(self):
        self.cuadruplos = []
        self.contador_temporales = 0
        self.etiquetas = {}
        self.contador_etiquetas = 0
        # Tipo de cada variable, constante, zona y temporal (lo usa el generador MIPS).
        self.tipos = {}

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
        self.tipos = {}

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
            self.tipos.setdefault(nodo.nombre, nodo.tipo)
            self.agregar("=", valor, "", nodo.nombre)

        elif isinstance(nodo, DeclaracionConstante):
            valor = self.generar_expresion(nodo.valor)
            self.tipos.setdefault(nodo.nombre, nodo.tipo)
            self.agregar("=", valor, "", nodo.nombre)

        elif isinstance(nodo, DeclaracionZona):
            self.tipos[nodo.nombre] = "zona"
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
        self.tipos[nodo.variable] = "zona"

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

        if nodo.nombre in RETORNO_FUNCIONES:
            resultado = self.nuevo_temporal()
            self.tipos[resultado] = RETORNO_FUNCIONES[nodo.nombre]

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
            if isinstance(nodo.valor, bool):
                return "verdadero" if nodo.valor else "falso"
            if isinstance(nodo.valor, str):
                return literal_texto(nodo.valor)
            return str(nodo.valor)

        if isinstance(nodo, Identificador):
            return nodo.nombre

        if isinstance(nodo, AccesoCampo):
            return f"{nodo.zona}.{nodo.campo}"

        if isinstance(nodo, OperacionBinaria):
            izquierda = self.generar_expresion(nodo.izquierda)
            derecha = self.generar_expresion(nodo.derecha)

            temporal = self.nuevo_temporal()
            self.tipos[temporal] = self.tipo_binaria(nodo, izquierda, derecha)

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
            self.tipos[temporal] = getattr(nodo, "tipo_sem", None) or (
                "booleano" if nodo.operador == "no"
                else self.tipo_de(operando)
            )

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

    def tipo_de(self, valor):
        """Tipo de un operando ya generado (literal, variable o temporal)."""
        valor = str(valor)
        if valor in self.tipos:
            return self.tipos[valor]
        if valor.startswith('"'):
            return "texto"
        if valor in {"verdadero", "falso"}:
            return "booleano"
        try:
            float(valor)
        except ValueError:
            return ""
        return "entero" if valor.lstrip("-").isdigit() else "decimal"

    def tipo_binaria(self, nodo, izquierda, derecha):
        tipo = getattr(nodo, "tipo_sem", None)
        if tipo and tipo != "error":
            return tipo
        if nodo.operador in OPERADORES_BOOLEANOS:
            return "booleano"
        tipos = {self.tipo_de(izquierda), self.tipo_de(derecha)}
        return "decimal" if "decimal" in tipos else "entero"

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
