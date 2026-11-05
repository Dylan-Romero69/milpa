"""Analizador léxico: texto -> lista de Token. Responsable: A."""
from dataclasses import dataclass


@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    col: int


def tokenizar(codigo, log):
    """Devuelve la lista de tokens terminada en EOF. Errores: E-LEX-01 a 03."""
    raise NotImplementedError
