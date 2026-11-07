
from dataclasses import dataclass


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    categoria: str
    valor: object = None
    linea: int = 0
    columna: int = 0
    ambito: int = 0


class TablaSimbolos:
    def __init__(self):
        # Cada diccionario representa un ámbito
        self.ambitos = [{}]
        self.nivel = 0

    def entrar_ambito(self):
        """Crea un nuevo ámbito."""
        self.ambitos.append({})
        self.nivel += 1

    def salir_ambito(self):
        """Elimina el ámbito actual."""
        if self.nivel > 0:
            self.ambitos.pop()
            self.nivel -= 1

    def existe(self, nombre):
        """Comprueba si un nombre ya fue declarado."""
        for ambito in self.ambitos:
            if nombre in ambito:
                return True
        return False

    def declarar(self, simbolo):
        """Registra un símbolo si no existe previamente."""
        if self.existe(simbolo.nombre):
            return False

        simbolo.ambito = self.nivel
        self.ambitos[-1][simbolo.nombre] = simbolo
        return True

    def buscar(self, nombre):
        """Busca un símbolo desde el ámbito actual hacia afuera."""
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]

        return None

    def actualizar_valor(self, nombre, valor):
        """Actualiza el valor de un símbolo."""
        simbolo = self.buscar(nombre)

        if simbolo is None:
            return False

        simbolo.valor = valor
        return True

    def obtener_todos(self):
        """Devuelve todos los símbolos registrados."""
        simbolos = []

        for ambito in self.ambitos:
            simbolos.extend(ambito.values())

        return simbolos

    def imprimir(self):
        """Muestra la tabla de símbolos."""
        print("\n========== TABLA DE SIMBOLOS ==========")
        print(
            f"{'NOMBRE':<18}"
            f"{'TIPO':<12}"
            f"{'CATEGORIA':<15}"
            f"{'VALOR':<15}"
            f"{'AMBITO':<8}"
        )
        print("-" * 68)

        for simbolo in self.obtener_todos():
            valor = simbolo.valor

            print(
                f"{simbolo.nombre:<18}"
                f"{simbolo.tipo:<12}"
                f"{simbolo.categoria:<15}"
                f"{str(valor):<15}"
                f"{simbolo.ambito:<8}"
            )

        print("=" * 68)
