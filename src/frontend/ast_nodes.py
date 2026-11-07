
"""
Nodos del Árbol de Sintaxis Abstracta (AST) de MILPA.

Representan las instrucciones y expresiones del lenguaje.
"""

from dataclasses import dataclass, field


# Nodo base de todas las estructuras del AST
@dataclass
class Nodo:
    linea: int = 0
    columna: int = 0


# Representa el programa completo
@dataclass
class Programa(Nodo):
    instrucciones: list = field(default_factory=list)


# Representa una declaración de variable
@dataclass
class DeclaracionVariable(Nodo):
    tipo: str = ""
    nombre: str = ""
    valor: object = None


# Representa una constante
@dataclass
class DeclaracionConstante(Nodo):
    tipo: str = ""
    nombre: str = ""
    valor: object = None


# Representa una zona de cultivo
@dataclass
class DeclaracionZona(Nodo):
    nombre: str = ""
    campos: list = field(default_factory=list)


# Representa un campo de una zona
@dataclass
class CampoZona(Nodo):
    nombre: str = ""
    valor: object = None


# Representa una asignación
@dataclass
class Asignacion(Nodo):
    nombre: str = ""
    valor: object = None


# Representa una condición si / si_no
@dataclass
class Condicional(Nodo):
    condicion: object = None
    bloque_si: list = field(default_factory=list)
    bloque_si_no: list = field(default_factory=list)


# Representa un ciclo mientras
@dataclass
class CicloMientras(Nodo):
    condicion: object = None
    instrucciones: list = field(default_factory=list)


# Representa un ciclo para_cada
@dataclass
class CicloParaCada(Nodo):
    tipo: str = ""
    variable: str = ""
    zonas: list = field(default_factory=list)
    instrucciones: list = field(default_factory=list)


# Representa una llamada a una función
@dataclass
class LlamadaFuncion(Nodo):
    nombre: str = ""
    argumentos: list = field(default_factory=list)


# Representa un operador binario
@dataclass
class OperacionBinaria(Nodo):
    izquierda: object = None
    operador: str = ""
    derecha: object = None


# Representa un operador unario
@dataclass
class OperacionUnaria(Nodo):
    operador: str = ""
    operando: object = None


# Representa un número, texto o valor booleano
@dataclass
class Literal(Nodo):
    valor: object = None
    tipo: str = ""


# Representa el uso de una variable
@dataclass
class Identificador(Nodo):
    nombre: str = ""


# Representa el acceso a un campo de una zona
@dataclass
class AccesoCampo(Nodo):
    zona: str = ""
    campo: str = ""


# Imprime el árbol AST de forma jerárquica
def imprimir_ast(nodo, nivel=0):

    if nodo is None:
        return

    espacio = "    " * nivel

    # Obtiene el nombre del nodo
    nombre = type(nodo).__name__

    print(f"{espacio}└── {nombre}")

    # Recorre los atributos del nodo
    if hasattr(nodo, "__dataclass_fields__"):

        for atributo in nodo.__dataclass_fields__:

            valor = getattr(nodo, atributo)

            # Ignora posiciones del código
            if atributo in ("linea", "columna"):
                continue

            # Recorre listas de instrucciones o argumentos
            if isinstance(valor, list):

                if valor:
                    print(f"{espacio}    ├── {atributo}")

                    for elemento in valor:
                        imprimir_ast(elemento, nivel + 2)

            # Recorre otros nodos
            elif hasattr(valor, "__dataclass_fields__"):

                print(f"{espacio}    ├── {atributo}")
                imprimir_ast(valor, nivel + 2)

            # Imprime valores simples
            elif valor is not None:
                print(f"{espacio}    ├── {atributo}: {valor}")
