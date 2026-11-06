
"""
Gestión centralizada de errores del compilador MILPA.

Registra errores producidos durante las fases:
- Análisis léxico.
- Análisis sintáctico.
- Análisis semántico.
- Validaciones de dominio.
"""

from dataclasses import dataclass


@dataclass
class Error:
    """Representa un error detectado durante la compilación."""

    fase: str
    codigo: str
    linea: int
    col: int
    mensaje: str

    def __str__(self) -> str:
        return (
            f"[{self.codigo}] {self.fase} "
            f"(línea {self.linea}, col {self.col}): "
            f"{self.mensaje}"
        )


class ErrorLog:
    """Almacena y administra los errores de compilación."""

    def __init__(self) -> None:
        self.errores: list[Error] = []

    def agregar(
        self,
        fase: str,
        codigo: str,
        linea: int,
        col: int,
        mensaje: str
    ) -> None:
        """Registra un nuevo error."""
        error = Error(fase, codigo, linea, col, mensaje)
        self.errores.append(error)

    def hay_errores(self) -> bool:
        """Indica si existen errores registrados."""
        return len(self.errores) > 0

    def obtener_errores(self) -> list[Error]:
        """Devuelve todos los errores registrados."""
        return self.errores.copy()

    def imprimir(self) -> None:
        """Muestra todos los errores registrados."""
        for error in self.errores:
            print(error)

    def limpiar(self) -> None:
        """Elimina todos los errores registrados."""
        self.errores.clear()
