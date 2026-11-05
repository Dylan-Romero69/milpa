"""Registro de errores de todas las fases. Responsable: A."""
from dataclasses import dataclass


@dataclass
class Error:
    fase: str      # léxico, sintáctico, semántico, dominio
    codigo: str    # E-LEX-01, E-SEM-03, ...
    linea: int
    col: int
    mensaje: str

    def __str__(self):
        return f"[{self.codigo}] {self.fase} (línea {self.linea}, col {self.col}): {self.mensaje}"


class ErrorLog:
    def __init__(self):
        self.errores: list[Error] = []

    def agregar(self, fase, codigo, linea, col, mensaje):
        self.errores.append(Error(fase, codigo, linea, col, mensaje))

    def hay_errores(self):
        return bool(self.errores)

    def imprimir(self):
        for e in self.errores:
            print(e)
