
from dataclasses import dataclass


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    categoria: str          # variable, constante, zona o alias (nombre de zona en un para_cada)
    valor: object = None
    linea: int = 0
    columna: int = 0
    ambito: int = 0
    direccion: str = ""     # etiqueta en el segmento .data (tabla de direcciones)
    tamano: int = 0         # bytes que ocupa en memoria
    inicializada: bool = False
    magnitud: object = None  # "humedad" o "temperatura" si guarda una lectura de sensor


class TablaSimbolos:
    def __init__(self):
        # Cada diccionario representa un ámbito
        self.ambitos = [{}]
        self.nivel = 0
        self.todos = []   # todos los símbolos declarados, aunque su ámbito ya se haya cerrado

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

    def existe_en_actual(self, nombre):
        """Comprueba si un nombre ya fue declarado en el ámbito actual."""
        return nombre in self.ambitos[-1]

    def declarar(self, simbolo):
        """Registra un símbolo si no existe previamente (no se permite ocultar nombres)."""
        if self.existe(simbolo.nombre):
            return False

        simbolo.ambito = self.nivel
        if not simbolo.direccion and simbolo.categoria in ("variable", "constante"):
            simbolo.direccion = f"var_{simbolo.nombre}"
            simbolo.tamano = simbolo.tamano or 4
        elif not simbolo.direccion and simbolo.categoria == "zona":
            simbolo.direccion = f"zona_{simbolo.nombre}"
            simbolo.tamano = simbolo.tamano or 16
        self.ambitos[-1][simbolo.nombre] = simbolo
        self.todos.append(simbolo)
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
        return list(self.todos)

    def imprimir(self):
        """Muestra la tabla de símbolos."""
        print("\n========== TABLA DE SIMBOLOS ==========")
        print(
            f"{'NOMBRE':<18}"
            f"{'TIPO':<12}"
            f"{'CATEGORIA':<15}"
            f"{'VALOR':<15}"
            f"{'AMBITO':<8}"
            f"{'DIRECCION':<22}"
            f"{'TAMANO':<7}"
        )
        print("-" * 97)

        for simbolo in self.obtener_todos():
            valor = simbolo.valor

            print(
                f"{simbolo.nombre:<18}"
                f"{simbolo.tipo:<12}"
                f"{simbolo.categoria:<15}"
                f"{str(valor)[:14]:<15}"
                f"{simbolo.ambito:<8}"
                f"{simbolo.direccion or '-':<22}"
                f"{simbolo.tamano:<7}"
            )

        print("=" * 97)
