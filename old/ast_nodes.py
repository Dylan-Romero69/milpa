"""Nodos del AST. Responsable: A. Ver docs/FORMATOS.md.

Todos los nodos heredan de Nodo, que guarda:
  linea, col  posición en el código fuente (para los errores)
  tipo        tipo de la expresión; lo llena el análisis semántico
              (entero, decimal, texto, booleano, zona, vacio)
  val         valor constante si se conoce al compilar; lo llena el semántico

Un bloque ({ ... }) se representa como una lista de sentencias.
"""
from dataclasses import dataclass, field, fields
from typing import Any, Optional


@dataclass(kw_only=True)
class Nodo:
    linea: int = 0
    col: int = 0
    tipo: Optional[str] = None
    val: Any = None


# ---- Programa y sentencias -------------------------------------------------
@dataclass
class Programa(Nodo):
    sentencias: list = field(default_factory=list)


@dataclass
class CampoZona(Nodo):
    nombre: str = ""
    valor: Nodo = None


@dataclass
class DeclZona(Nodo):
    nombre: str = ""
    campos: list = field(default_factory=list)       # lista de CampoZona


@dataclass
class DeclConst(Nodo):
    tipo_decl: str = ""                               # entero, decimal, texto, booleano
    nombre: str = ""
    valor: Nodo = None


@dataclass
class DeclVar(Nodo):
    tipo_decl: str = ""
    nombre: str = ""
    valor: Nodo = None


@dataclass
class Asig(Nodo):
    nombre: str = ""
    valor: Nodo = None


@dataclass
class Si(Nodo):
    cond: Nodo = None
    entonces: list = field(default_factory=list)
    sino: Optional[list] = None                       # None si no hay si_no


@dataclass
class Mientras(Nodo):
    cond: Nodo = None
    cuerpo: list = field(default_factory=list)


@dataclass
class Repetir(Nodo):                                  # opcional: repetir { } mientras (cond)
    cuerpo: list = field(default_factory=list)
    cond: Nodo = None


@dataclass
class ParaCada(Nodo):
    var: str = ""                                     # nombre del alias de la zona
    zonas: list = field(default_factory=list)         # nombres de zonas (strings)
    cuerpo: list = field(default_factory=list)


# ---- Expresiones ------------------------------------------------------------
@dataclass
class BinOp(Nodo):
    op: str = ""                                      # + - * / % == != < <= > >= y o
    izq: Nodo = None
    der: Nodo = None


@dataclass
class UnOp(Nodo):
    op: str = ""                                      # neg, no
    operando: Nodo = None


@dataclass
class Literal(Nodo):
    tipo_lit: str = ""                                # entero, decimal, texto, booleano
    valor: Any = None                                 # int, float, str o bool de Python


@dataclass
class Var(Nodo):
    nombre: str = ""


@dataclass
class AccesoCampo(Nodo):
    objeto: str = ""                                  # nombre de la zona (o alias)
    campo: str = ""


@dataclass
class Llamada(Nodo):                                  # sentencia o expresión
    nombre: str = ""
    args: list = field(default_factory=list)


# ---- Impresión del árbol (para --ast) -----------------------------------------
def formatear(nodo, nivel=0):
    pad = "  " * nivel
    if not isinstance(nodo, Nodo):
        return pad + repr(nodo)
    escalares, hijos = [], []
    for f in fields(nodo):
        v = getattr(nodo, f.name)
        if f.name in ("linea", "col"):
            continue
        if f.name in ("tipo", "val"):
            if v is not None:
                escalares.append(f"{f.name}={v!r}")
        elif isinstance(v, Nodo) or (isinstance(v, list) and v and isinstance(v[0], Nodo)):
            hijos.append((f.name, v))
        else:
            escalares.append(f"{f.name}={v!r}")
    cab = type(nodo).__name__ + (f"({', '.join(escalares)})" if escalares else "")
    lineas = [pad + cab]
    for nombre, v in hijos:
        lineas.append(f"{pad}  .{nombre}:")
        for x in (v if isinstance(v, list) else [v]):
            lineas.append(formatear(x, nivel + 2))
    return "\n".join(lineas)
