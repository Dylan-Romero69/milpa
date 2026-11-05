"""Tabla de símbolos y de direcciones con pila de ámbitos. Responsable: A."""
from dataclasses import dataclass


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    categoria: str       # variable, constante, zona
    nivel: int
    direccion: str       # etiqueta en .data
    tamano: int
    valor: object = None
    inicializada: bool = False
