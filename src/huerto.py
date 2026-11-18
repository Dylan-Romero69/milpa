"""
Reglas compartidas entre el código MILPA, el .asm y el simulador de huerto.

Ubicación de una zona en el huerto (en este orden):
  1. Los campos 'fila' y 'columna' de la zona (empiezan en 1).
  2. El nombre parcela_F_C (fila F, columna C).
  3. La primera parcela libre, fila por fila.

Humedad y estado de una zona: variables humedad_actual_<sufijo> y
estado_cultivo_<sufijo>, donde el sufijo es "F_C" si la zona se llama
parcela_F_C y el nombre de la zona en cualquier otro caso.
"""

import re

HUMEDAD_POR_DEFECTO = 50
HUMEDAD_MIN_POR_DEFECTO = 35
RIEGO_MAX_POR_DEFECTO = 30

PATRON_PARCELA = re.compile(r"parcela_(\d+)_(\d+)$")
PATRON_SENSOR = re.compile(r"Sensor\s+(\S+)\s+de\s+(\S+):\s*$")


def parcela_vacia():
    return {
        "tierra": False, "cultivo": "", "humedad_min": 35,
        "riego_max": 6, "humedad": 50, "estado": "vacía", "zona": "",
    }


def calcular_estado(parcela):
    """Mismas reglas que el simulador del huerto."""
    if not parcela["tierra"]:
        return "vacía"
    if not parcela["cultivo"]:
        return "tierra"
    if parcela["humedad"] < parcela["humedad_min"]:
        return "seca"
    if parcela["humedad"] > parcela["humedad_min"] + parcela["riego_max"] * 5:
        return "dañada"
    return "saludable"


def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, int(round(valor))))


# =====================================================
# NOMBRES
# =====================================================

def sufijo_zona(nombre):
    coincidencia = PATRON_PARCELA.match(nombre)
    if coincidencia:
        return f"{coincidencia.group(1)}_{coincidencia.group(2)}"
    return nombre


def variable_humedad(nombre):
    return f"humedad_actual_{sufijo_zona(nombre)}"


def variable_estado(nombre):
    return f"estado_cultivo_{sufijo_zona(nombre)}"


def variables_humedad(nombre):
    """Nombres aceptados para la humedad de una zona (el primero es el que se escribe)."""
    candidatos = [variable_humedad(nombre), f"humedad_actual_{nombre}", f"humedad_{nombre}"]
    return list(dict.fromkeys(candidatos))


def posicion_por_nombre(nombre):
    coincidencia = PATRON_PARCELA.match(nombre)
    if coincidencia:
        return int(coincidencia.group(1)) - 1, int(coincidencia.group(2)) - 1
    return None


def limpiar_cultivo(cultivo):
    cultivo = str(cultivo or "").replace('"', "").strip()
    return "" if cultivo.lower() == "sin cultivo" else cultivo


# =====================================================
# UBICACIÓN
# =====================================================

def posicion_pedida(zona):
    """(fila, columna) desde 0 que pide la zona, o None si no pide ninguna."""
    fila, columna = zona.get("fila") or 0, zona.get("columna") or 0
    if isinstance(fila, (int, float)) and isinstance(columna, (int, float)) and fila > 0 and columna > 0:
        return int(fila) - 1, int(columna) - 1
    return posicion_por_nombre(zona["nombre"])


def ubicar_zonas(zonas, filas, columnas):
    """
    Asigna una parcela a cada zona. Devuelve (ubicadas, avisos):
    ubicadas es una lista de ((fila, columna), zona) y avisos explica las
    zonas que no se pudieron colocar.
    """
    ubicadas, avisos, pendientes = [], [], []
    ocupadas = {}

    for zona in zonas:
        posicion = posicion_pedida(zona)
        if posicion is None:
            pendientes.append(zona)
            continue
        fila, columna = posicion
        if not (0 <= fila < filas and 0 <= columna < columnas):
            avisos.append(
                f"La zona '{zona['nombre']}' pide la parcela {fila + 1}:{columna + 1}, "
                f"fuera del huerto ({filas} filas x {columnas} columnas)."
            )
            continue
        if posicion in ocupadas:
            avisos.append(
                f"La parcela {fila + 1}:{columna + 1} ya es de la zona "
                f"'{ocupadas[posicion]}'; se omite '{zona['nombre']}'."
            )
            continue
        ocupadas[posicion] = zona["nombre"]
        ubicadas.append((posicion, zona))

    libres = [
        (fila, columna)
        for fila in range(filas)
        for columna in range(columnas)
        if (fila, columna) not in ocupadas
    ]
    for zona in pendientes:
        if libres:
            ubicadas.append((libres.pop(0), zona))
        else:
            avisos.append(f"La zona '{zona['nombre']}' no cupo en el huerto.")

    return ubicadas, avisos


def construir_parcelas(zonas, filas, columnas, humedad_de):
    """
    Crea todas las parcelas a partir de las zonas.
    humedad_de(zona, posicion) devuelve la humedad o None (se usa 50 %).
    """
    parcelas = {
        (fila, columna): parcela_vacia()
        for fila in range(filas)
        for columna in range(columnas)
    }
    ubicadas, avisos = ubicar_zonas(zonas, filas, columnas)

    for posicion, zona in ubicadas:
        humedad_min = zona.get("humedad_min")
        riego_max = zona.get("riego_max")
        humedad = humedad_de(zona, posicion)
        parcela = parcelas[posicion]
        parcela.update({
            "tierra": True,
            "zona": zona["nombre"],
            "cultivo": limpiar_cultivo(zona.get("cultivo")),
            "humedad_min": limitar(humedad_min, 0, 100)
            if isinstance(humedad_min, (int, float)) else HUMEDAD_MIN_POR_DEFECTO,
            "riego_max": max(1, int(riego_max))
            if isinstance(riego_max, (int, float)) else RIEGO_MAX_POR_DEFECTO,
            "humedad": HUMEDAD_POR_DEFECTO if humedad is None else limitar(humedad, 0, 100),
        })
        parcela["estado"] = calcular_estado(parcela)

    return parcelas, avisos


# =====================================================
# DESDE UN .asm EJECUTADO
# =====================================================

def humedad_de_zona(nombre, variables):
    for candidato in variables_humedad(nombre):
        if candidato in variables:
            tipo, valor = variables[candidato]
            if tipo in {"entero", "decimal"}:
                return valor
    return None


def parcelas_desde_estado(estado, filas, columnas):
    """
    Convierte el estado leído de un .asm (extraer_estado) en parcelas.
    Devuelve (parcelas, avisos).
    """
    return construir_parcelas(
        estado["zonas"], filas, columnas,
        lambda zona, posicion: humedad_de_zona(zona["nombre"], estado["variables"]),
    )


def sensor_simulado(parcelas):
    """
    Función de entrada para SimuladorMIPS: responde a los sensores del
    programa con la humedad de las parcelas actuales, sin preguntar al usuario.
    """

    por_zona = {
        parcela.get("zona"): parcela
        for parcela in parcelas.values()
        if parcela.get("tierra") and parcela.get("zona")
    }

    def entrada(tipo, pregunta):
        coincidencia = PATRON_SENSOR.search(pregunta)
        if coincidencia:
            sensor, zona = coincidencia.groups()
            if sensor == "temperatura":
                return 25.0
            parcela = por_zona.get(zona)
            if parcela is None:
                posicion = posicion_por_nombre(zona)
                parcela = parcelas.get(posicion) if posicion else None
            if parcela and parcela.get("tierra"):
                return float(parcela["humedad"])
            return float(HUMEDAD_POR_DEFECTO)
        # lloviendo() y cualquier otra lectura entera: no llueve.
        return 0.0 if tipo == "decimal" else 0

    return entrada
