
from dataclasses import dataclass


@dataclass
class IntervaloVida:
    """Representa el tiempo de vida de un temporal."""

    temporal: str
    inicio: int
    fin: int
    registro: str = ""
    desplazamiento: int = -1


class AsignadorRegistros:
    """Asigna registros MIPS mediante el algoritmo Linear Scan."""

    REGISTROS_DISPONIBLES = [
        "$t0", "$t1", "$t2", "$t3", "$t4",
        "$t5", "$t6", "$t7", "$t8", "$t9"
    ]

    def __init__(self, cuadruplos, registros=None):
        self.cuadruplos = cuadruplos
        self.registros = registros or self.REGISTROS_DISPONIBLES.copy()

        self.intervalos = []
        self.asignaciones = {}
        self.derramas = {}
        self.ubicaciones = {}

    def es_temporal(self, nombre):
        """Comprueba si un identificador es un temporal."""
        import re
        return bool(re.fullmatch(r"t\d+", str(nombre)))

    def calcular_intervalos(self):
        """Calcula el primer y último uso de cada temporal."""

        posiciones = {}

        for i, c in enumerate(self.cuadruplos):
            # Los argumentos representan usos.
            for argumento in (c.argumento1, c.argumento2):
                if self.es_temporal(argumento):
                    if argumento not in posiciones:
                        posiciones[argumento] = [i, i]
                    else:
                        posiciones[argumento][1] = i

            # El resultado representa una definición.
            if self.es_temporal(c.resultado):
                temporal = c.resultado

                if temporal not in posiciones:
                    posiciones[temporal] = [i, i]
                else:
                    posiciones[temporal][1] = max(
                        posiciones[temporal][1], i
                    )

        self.intervalos = [
            IntervaloVida(nombre, inicio, fin)
            for nombre, (inicio, fin) in posiciones.items()
        ]

        self.intervalos.sort(key=lambda x: x.inicio)

        return self.intervalos

    def asignar(self):
        """Asigna registros mediante Linear Scan."""

        self.calcular_intervalos()

        activos = []
        siguiente_derrame = 4

        self.asignaciones.clear()
        self.derramas.clear()
        self.ubicaciones.clear()

        for intervalo in self.intervalos:

            # Liberar registros de temporales que ya terminaron.
            activos.sort(key=lambda x: x[0])

            activos = [
                activo for activo in activos
                if activo[0] >= intervalo.inicio
            ]

            registros_ocupados = {
                activo[2] for activo in activos
            }

            disponibles = [
                registro for registro in self.registros
                if registro not in registros_ocupados
            ]

            if disponibles:
                registro = disponibles[0]

                intervalo.registro = registro
                self.asignaciones[intervalo.temporal] = registro
                self.ubicaciones[intervalo.temporal] = registro

                activos.append((
                    intervalo.fin,
                    intervalo.temporal,
                    registro
                ))

            else:
                # Seleccionar el temporal que termina más tarde.
                ultimo = max(activos, key=lambda x: x[0])

                if ultimo[0] > intervalo.fin:
                    # Reutilizar el registro del temporal desplazado.
                    activos.remove(ultimo)

                    temporal_anterior = ultimo[1]
                    registro = ultimo[2]

                    self.asignaciones.pop(
                        temporal_anterior, None
                    )

                    self.derramas[temporal_anterior] = (
                        siguiente_derrame
                    )

                    self.ubicaciones[temporal_anterior] = (
                        f"-{siguiente_derrame}($fp)"
                    )

                    siguiente_derrame += 4

                    intervalo.registro = registro
                    self.asignaciones[intervalo.temporal] = registro
                    self.ubicaciones[intervalo.temporal] = registro

                    activos.append((
                        intervalo.fin,
                        intervalo.temporal,
                        registro
                    ))

                else:
                    # Desplazar el temporal actual a memoria.
                    self.derramas[intervalo.temporal] = (
                        siguiente_derrame
                    )

                    self.ubicaciones[intervalo.temporal] = (
                        f"-{siguiente_derrame}($fp)"
                    )

                    intervalo.desplazamiento = siguiente_derrame
                    siguiente_derrame += 4

        return self.ubicaciones

    def imprimir(self):
        """Muestra los intervalos y sus asignaciones."""

        print("\n========== ASIGNACION DE REGISTROS ==========")

        print(
            f"{'TEMPORAL':<12}"
            f"{'INICIO':<10}"
            f"{'FIN':<10}"
            f"{'UBICACION':<15}"
        )

        print("-" * 47)

        for intervalo in self.intervalos:
            ubicacion = self.ubicaciones.get(
                intervalo.temporal, "Sin asignar"
            )

            print(
                f"{intervalo.temporal:<12}"
                f"{intervalo.inicio:<10}"
                f"{intervalo.fin:<10}"
                f"{ubicacion:<15}"
            )

        print("-" * 47)
        print(f"Registros utilizados: {len(self.asignaciones)}")
        print(f"Temporales en memoria: {len(self.derramas)}")
        print("=============================================")
