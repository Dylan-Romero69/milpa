"""Generador de cuádruplos a partir del AST validado. Responsable: B."""
from dataclasses import dataclass


@dataclass
class Cuadruplo:
    op: str
    arg1: str = "-"
    arg2: str = "-"
    res: str = "-"

    def __str__(self):
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.res})"


def generar(ast, tabla):
    raise NotImplementedError
