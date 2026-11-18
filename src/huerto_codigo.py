"""
Sincronización en tiempo real entre el código MILPA y el huerto.

Código -> huerto:  analizar_codigo() lee las zonas y las variables de humedad
    y estado aunque el programa esté a medio escribir o tenga errores en otras
    partes; parcelas_desde_codigo() las convierte en parcelas.

Huerto -> código:  aplicar_huerto_al_codigo() edita solo lo necesario:
    reescribe el bloque de la zona que cambió, actualiza el número de su
    humedad, agrega zonas nuevas al final y borra las que se quitaron del
    huerto. El resto del programa (ciclos, registrar, comentarios) no se toca.
"""

import re
from dataclasses import dataclass, field

from src.core.errors import ErrorLog
from src.frontend.lexer import Lexer
from src.huerto import (
    construir_parcelas,
    limpiar_cultivo,
    posicion_por_nombre,
    ubicar_zonas,
    variable_estado,
    variable_humedad,
    variables_humedad,
)

TIPOS_DECLARACION = {
    "TIPO_ENTERO": "entero",
    "TIPO_DECIMAL": "decimal",
    "TIPO_TEXTO": "texto",
    "TIPO_BOOLEANO": "booleano",
}
LITERALES = {"ENTERO", "DECIMAL", "TEXTO", "VERDADERO", "FALSO"}


@dataclass
class ZonaCodigo:
    nombre: str
    campos: dict = field(default_factory=dict)
    inicio: int = 0          # posición de la palabra 'zona'
    fin: int = 0             # posición después de '}'


@dataclass
class VariableCodigo:
    nombre: str
    tipo: str
    valor: object = None     # None si el valor no es un literal simple
    inicio: int = 0
    fin: int = 0
    valor_inicio: int = None
    valor_fin: int = None


@dataclass
class ModeloCodigo:
    zonas: list = field(default_factory=list)
    variables: dict = field(default_factory=dict)


# =====================================================
# CÓDIGO -> MODELO
# =====================================================

def _inicios_de_linea(texto):
    inicios = [0]
    for i, ch in enumerate(texto):
        if ch == "\n":
            inicios.append(i + 1)
    return inicios


def analizar_codigo(texto):
    """Lee zonas y declaraciones globales sin exigir que el programa compile."""

    tokens = Lexer(texto, ErrorLog()).analizar()
    inicios = _inicios_de_linea(texto)

    def posicion(token):
        return inicios[token.linea - 1] + token.columna - 1

    def fin(token):
        largo = len(token.valor) + 2 if token.tipo == "TEXTO" else len(token.valor)
        return posicion(token) + largo

    def tipo(i):
        return tokens[i].tipo if i < len(tokens) else "EOF"

    def literal(i):
        """Lee un literal (con signo opcional). Devuelve (valor, primer, último) o None."""
        signo = 1
        primero = i
        if tipo(i) == "RESTA" and tipo(i + 1) in {"ENTERO", "DECIMAL"}:
            signo, i = -1, i + 1
        token = tokens[i] if i < len(tokens) else None
        if token is None or token.tipo not in LITERALES:
            return None
        if token.tipo == "ENTERO":
            valor = signo * int(token.valor)
        elif token.tipo == "DECIMAL":
            valor = signo * float(token.valor)
        elif token.tipo == "TEXTO":
            valor = token.valor
        else:
            valor = token.tipo == "VERDADERO"
        return valor, primero, i

    modelo = ModeloCodigo()
    profundidad = 0
    i = 0

    while i < len(tokens) and tipo(i) != "EOF":
        actual = tipo(i)

        if actual == "LLAVE_ABRE":
            profundidad += 1
        elif actual == "LLAVE_CIERRA":
            profundidad = max(0, profundidad - 1)

        elif (
            profundidad == 0
            and actual == "ZONA"
            and tipo(i + 1) == "ID"
            and tipo(i + 2) == "LLAVE_ABRE"
        ):
            zona = ZonaCodigo(tokens[i + 1].valor, inicio=posicion(tokens[i]))
            j = i + 3
            completa = False
            while j < len(tokens):
                t = tipo(j)
                if t == "LLAVE_CIERRA":
                    completa = True
                    break
                if t in {"EOF", "ZONA", "LLAVE_ABRE"}:
                    break
                if t == "ID" and tipo(j + 1) == "DOS_PUNTOS":
                    nombre_campo = tokens[j].valor
                    k = j + 2
                    while tipo(k) not in {"COMA", "LLAVE_CIERRA", "EOF", "ZONA", "LLAVE_ABRE"}:
                        k += 1
                    leido = literal(j + 2)
                    zona.campos[nombre_campo] = (
                        leido[0] if leido and leido[2] == k - 1 else None
                    )
                    j = k
                    continue
                j += 1
            if completa:
                zona.fin = fin(tokens[j])
                modelo.zonas.append(zona)
                i = j + 1
                continue

        elif (
            profundidad == 0
            and actual in TIPOS_DECLARACION
            and tipo(i + 1) == "ID"
            and tipo(i + 2) == "ASIGNACION"
        ):
            nombre = tokens[i + 1].valor
            leido = literal(i + 3)
            ultimo = leido[2] if leido else i + 2
            siguiente = ultimo + 1
            simple = leido is not None and (
                tipo(siguiente) in {"EOF", "LLAVE_CIERRA"}
                or tokens[siguiente].linea != tokens[ultimo].linea
            )
            # Si el valor es una expresión, la declaración llega hasta el fin de la línea.
            linea = tokens[i].linea
            final = ultimo
            while tipo(final + 1) != "EOF" and tokens[final + 1].linea == linea:
                final += 1
            if nombre not in modelo.variables:
                modelo.variables[nombre] = VariableCodigo(
                    nombre=nombre,
                    tipo=TIPOS_DECLARACION[actual],
                    valor=leido[0] if simple else None,
                    inicio=posicion(tokens[i]),
                    fin=fin(tokens[final]),
                    valor_inicio=posicion(tokens[leido[1]]) if simple else None,
                    valor_fin=fin(tokens[leido[2]]) if simple else None,
                )
            i = final + 1
            continue

        i += 1

    return modelo


def _zonas_para_ubicar(modelo):
    return [{"nombre": zona.nombre, **zona.campos} for zona in modelo.zonas]


def parcelas_desde_codigo(modelo, filas, columnas, anteriores=None):
    """
    Construye todas las parcelas a partir del código. Si una zona no tiene
    variable de humedad, conserva la humedad que ya tenía en el huerto.
    Devuelve (parcelas, avisos).
    """
    anteriores = anteriores or {}

    def humedad_de(zona, posicion):
        for nombre in variables_humedad(zona["nombre"]):
            variable = modelo.variables.get(nombre)
            if variable and isinstance(variable.valor, (int, float)) and not isinstance(variable.valor, bool):
                return variable.valor
        previa = anteriores.get(posicion)
        if previa and previa.get("tierra") and previa.get("zona") == zona["nombre"]:
            return previa["humedad"]
        return None

    return construir_parcelas(_zonas_para_ubicar(modelo), filas, columnas, humedad_de)


# =====================================================
# HUERTO -> CÓDIGO
# =====================================================

def bloque_zona(nombre, parcela, posicion, con_posicion, sangria=""):
    lineas = [
        f'cultivo: "{parcela["cultivo"]}"',
        f'humedad_min: {parcela["humedad_min"]}',
        f'riego_max: {parcela["riego_max"]}',
    ]
    if con_posicion:
        lineas += [f"fila: {posicion[0] + 1}", f"columna: {posicion[1] + 1}"]
    cuerpo = ",\n".join(f"{sangria}    {linea}" for linea in lineas)
    return f"zona {nombre} {{\n{cuerpo}\n{sangria}}}"


def declaraciones_estado(nombre, parcela):
    return (
        f"entero {variable_humedad(nombre)} = {parcela['humedad']}\n"
        f'texto {variable_estado(nombre)} = "{parcela["estado"]}"'
    )


def _numero_igual(a, b):
    return isinstance(a, (int, float)) and not isinstance(a, bool) and round(a) == round(b)


def _zona_igual(zona, parcela, posicion, posicion_actual):
    campos = zona.campos
    return (
        limpiar_cultivo(campos.get("cultivo")) == parcela["cultivo"]
        and _numero_igual(campos.get("humedad_min"), parcela["humedad_min"])
        and (
            _numero_igual(campos.get("riego_max"), parcela["riego_max"])
            or ("riego_max" not in campos and parcela["riego_max"] == 30)
        )
        and posicion_actual == posicion
    )


def _linea_completa(texto, inicio, fin):
    """Extiende [inicio, fin) a líneas completas si no hay más código en ellas."""
    linea_inicio = texto.rfind("\n", 0, inicio) + 1
    linea_fin = texto.find("\n", fin)
    linea_fin = len(texto) if linea_fin == -1 else linea_fin + 1
    if texto[linea_inicio:inicio].strip() or texto[fin:linea_fin].strip():
        return inicio, fin
    return linea_inicio, linea_fin


def aplicar_huerto_al_codigo(texto, parcelas, filas, columnas):
    """Devuelve el código con las zonas del huerto actualizadas (edición mínima)."""

    modelo = analizar_codigo(texto)
    zonas_codigo = {zona.nombre: zona for zona in modelo.zonas}
    ubicadas, _avisos = ubicar_zonas(_zonas_para_ubicar(modelo), filas, columnas)
    posicion_de = {zona["nombre"]: posicion for posicion, zona in ubicadas}

    ediciones = []          # (inicio, fin, texto nuevo)
    nuevas = []

    def variable_de(nombres):
        for nombre in nombres:
            if nombre in modelo.variables:
                return modelo.variables[nombre]
        return None

    def borrar(inicio, fin):
        ediciones.append((*_linea_completa(texto, inicio, fin), ""))

    # Zonas que el huerto ya no tiene en su parcela: se borran del código.
    for nombre, posicion in posicion_de.items():
        parcela = parcelas.get(posicion)
        if parcela and parcela["tierra"] and (parcela.get("zona") or nombre) == nombre:
            continue
        zona = zonas_codigo[nombre]
        borrar(zona.inicio, zona.fin)
        for variable in (
            variable_de(variables_humedad(nombre)),
            modelo.variables.get(variable_estado(nombre)),
        ):
            if variable:
                borrar(variable.inicio, variable.fin)

    # Zonas que siguen o que son nuevas.
    for posicion in sorted(parcelas):
        parcela = parcelas[posicion]
        if not parcela["tierra"]:
            continue
        nombre = parcela.get("zona") or "parcela_{}_{}".format(posicion[0] + 1, posicion[1] + 1)
        parcela["zona"] = nombre
        zona = zonas_codigo.get(nombre)

        if zona is None:
            nuevas.append(
                bloque_zona(nombre, parcela, posicion, con_posicion=True)
                + "\n" + declaraciones_estado(nombre, parcela)
            )
            continue

        if not _zona_igual(zona, parcela, posicion, posicion_de.get(nombre)):
            linea_inicio = texto.rfind("\n", 0, zona.inicio) + 1
            sangria = re.match(r"[ \t]*", texto[linea_inicio:zona.inicio]).group()
            con_posicion = (
                "fila" in zona.campos
                or "columna" in zona.campos
                or posicion_por_nombre(nombre) != posicion
            )
            ediciones.append((
                zona.inicio, zona.fin,
                bloque_zona(nombre, parcela, posicion, con_posicion, sangria),
            ))

        agregar = []
        humedad = variable_de(variables_humedad(nombre))
        if humedad is None:
            agregar.append(f"entero {variable_humedad(nombre)} = {parcela['humedad']}")
        elif humedad.valor_inicio is not None and not _numero_igual(humedad.valor, parcela["humedad"]):
            ediciones.append((humedad.valor_inicio, humedad.valor_fin, str(parcela["humedad"])))

        estado = modelo.variables.get(variable_estado(nombre))
        linea_estado = f'texto {variable_estado(nombre)} = "{parcela["estado"]}"'
        if estado is None and humedad is not None:
            # Va justo después de la humedad que ya existe.
            ediciones.append((humedad.fin, humedad.fin, "\n" + linea_estado))
        elif estado is None:
            agregar.append(linea_estado)
        elif estado.valor_inicio is not None and estado.valor != parcela["estado"]:
            ediciones.append((estado.valor_inicio, estado.valor_fin, f'"{parcela["estado"]}"'))

        if agregar:
            ediciones.append((zona.fin, zona.fin, "\n" + "\n".join(agregar)))

    if nuevas:
        if not texto.strip() or texto.endswith("\n\n"):
            separador = ""
        else:
            separador = "\n" if texto.endswith("\n") else "\n\n"
        ediciones.append((len(texto), len(texto), separador + "\n\n".join(nuevas) + "\n"))

    # Aplicar de atrás hacia adelante para que las posiciones sigan siendo válidas.
    resultado = texto
    for inicio, fin, nuevo in sorted(ediciones, key=lambda e: (e[0], e[1]), reverse=True):
        resultado = resultado[:inicio] + nuevo + resultado[fin:]

    if ediciones and any(nuevo == "" for _i, _f, nuevo in ediciones):
        resultado = re.sub(r"\n{3,}", "\n\n", resultado).lstrip("\n")

    return resultado
