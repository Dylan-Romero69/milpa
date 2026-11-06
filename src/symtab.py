"""Tabla de símbolos y de direcciones. Responsable: A."""
from dataclasses import dataclass

TAMANOS = {"entero": 4, "decimal": 4, "booleano": 4, "texto": 4, "zona": 16}


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
    desplazamiento: int = 0   # bytes desde el inicio de los datos


class ErrorTabla(Exception):
    """Redeclaración (siempre es E-SEM-02)."""


class TablaSimbolos:
    def __init__(self):
        self.ambitos = [{}]   # el primero es el global
        self.todos = []       # todos los símbolos, para imprimir al final
        self.veces = {}       # cuántas veces se declaró cada nombre

    def abrir_ambito(self):
        self.ambitos.append({})

    def cerrar_ambito(self):
        self.ambitos.pop()

    def declarar(self, nombre, tipo, categoria, valor=None, inicializada=False):
        if nombre in self.ambitos[-1]:
            raise ErrorTabla(f"'{nombre}' ya está declarado en este ámbito")
        for ambito in self.ambitos[:-1]:
            if nombre in ambito:
                raise ErrorTabla(f"'{nombre}' oculta una variable externa")
        self.veces[nombre] = self.veces.get(nombre, 0) + 1
        direccion = ("z_" if categoria == "zona" else "v_") + nombre
        if len(self.ambitos) > 1:                  # dentro de un bloque: v_x_1, v_x_2...
            direccion += f"_{self.veces[nombre]}"
        s = Simbolo(nombre, tipo, categoria, len(self.ambitos) - 1, direccion,
                    TAMANOS[tipo], valor, inicializada, self.tamano_datos())
        self.ambitos[-1][nombre] = s
        self.todos.append(s)
        return s

    def buscar(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def tamano_datos(self):
        return sum(s.tamano for s in self.todos)

    def imprimir(self):
        print(f"{'Nombre':<14}{'Tipo':<10}{'Categoría':<11}{'Nivel':<6}"
              f"{'Dirección':<16}{'Desp.':<6}{'Tamaño':<9}Valor / Inic.")
        for s in self.todos:
            info = "sí" if s.inicializada else "no"
            if s.valor is not None:
                info = f"{s.valor} / {info}"
            print(f"{s.nombre:<14}{s.tipo:<10}{s.categoria:<11}{s.nivel:<6}"
                  f"{s.direccion:<16}{s.desplazamiento:<6}{s.tamano} bytes  {info}")
        print(f"Total de datos: {self.tamano_datos()} bytes")