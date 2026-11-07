"""Analizador léxico: texto -> lista de Token. Responsable: A.

Reconoce palabras reservadas, identificadores, literales (entero, decimal, texto),
operadores y delimitadores. Ignora espacios, tabulaciones, saltos de línea y
comentarios que empiezan con //.

Errores léxicos (se siguen acumulando para reportar varios en una sola corrida):
  E-LEX-01  carácter inválido
  E-LEX-02  texto sin cerrar
  E-LEX-03  número mal formado
Líneas y columnas empiezan en 1.
"""
import re
from dataclasses import dataclass

PALABRAS_RESERVADAS = {
    "zona", "constante", "entero", "decimal", "texto", "booleano",
    "si", "si_no", "mientras", "repetir", "para_cada", "en",
    "y", "o", "no", "verdadero", "falso",
}
OPERADORES_DOBLES = {"==", "!=", "<=", ">="}
OPERADORES_SIMPLES = set("+-*/%=<>")
DELIMITADORES = set("(){}[],:.")

# Todo lo que "parece" un número: dígitos seguidos de letras, puntos o guiones bajos.
# Después se valida si es un ENTERO o un DECIMAL bien formado.
_RE_NUMERO = re.compile(r"[0-9][0-9A-Za-z_.]*")
_RE_ENTERO = re.compile(r"[0-9]+")
_RE_DECIMAL = re.compile(r"[0-9]+\.[0-9]+")


@dataclass
class Token:
    tipo: str      # PALABRA_RESERVADA, ID, ENTERO, DECIMAL, TEXTO, OPERADOR, DELIMITADOR, EOF
    lexema: str    # para TEXTO es el contenido sin las comillas
    linea: int
    col: int


def _es_letra(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z") or c == "_"


def _es_digito(c):
    return "0" <= c <= "9"


def tokenizar(codigo, log):
    """Devuelve la lista de tokens terminada en EOF.

    Si hay errores léxicos quedan registrados en `log` y el análisis continúa.
    """
    tokens = []
    n = len(codigo)
    i = 0
    linea = 1
    inicio = 0  # índice donde empieza la línea actual

    while i < n:
        c = codigo[i]
        col = i - inicio + 1

        if c == "\n":
            linea += 1
            i += 1
            inicio = i
            continue
        if c in " \t\r":
            i += 1
            continue
        if c == "/" and i + 1 < n and codigo[i + 1] == "/":
            while i < n and codigo[i] != "\n":
                i += 1
            continue

        # Identificadores y palabras reservadas
        if _es_letra(c):
            j = i
            while j < n and (_es_letra(codigo[j]) or _es_digito(codigo[j])):
                j += 1
            lexema = codigo[i:j]
            tipo = "PALABRA_RESERVADA" if lexema in PALABRAS_RESERVADAS else "ID"
            tokens.append(Token(tipo, lexema, linea, col))
            i = j
            continue

        # Números
        if _es_digito(c):
            m = _RE_NUMERO.match(codigo, i)
            lexema = m.group()
            if _RE_ENTERO.fullmatch(lexema):
                tokens.append(Token("ENTERO", lexema, linea, col))
            elif _RE_DECIMAL.fullmatch(lexema):
                tokens.append(Token("DECIMAL", lexema, linea, col))
            else:
                log.agregar("léxico", "E-LEX-03", linea, col,
                            f"número mal formado '{lexema}'")
            i = m.end()
            continue

        # Textos
        if c == '"':
            j = i + 1
            while j < n and codigo[j] not in '"\n':
                j += 1
            if j < n and codigo[j] == '"':
                tokens.append(Token("TEXTO", codigo[i + 1:j], linea, col))
                i = j + 1
            else:
                log.agregar("léxico", "E-LEX-02", linea, col,
                            "texto sin cerrar: falta la comilla de cierre")
                i = j  # no consume el salto de línea
            continue

        # Operadores
        if codigo[i:i + 2] in OPERADORES_DOBLES:
            tokens.append(Token("OPERADOR", codigo[i:i + 2], linea, col))
            i += 2
            continue
        if c in OPERADORES_SIMPLES:
            tokens.append(Token("OPERADOR", c, linea, col))
            i += 1
            continue

        # Delimitadores
        if c in DELIMITADORES:
            tokens.append(Token("DELIMITADOR", c, linea, col))
            i += 1
            continue

        # Cualquier otra cosa es un carácter inválido
        if c == "!":
            log.agregar("léxico", "E-LEX-01", linea, col,
                        "carácter inválido '!' (¿quisiste escribir '!='?)")
        else:
            log.agregar("léxico", "E-LEX-01", linea, col,
                        f"carácter inválido '{c}'")
        i += 1

    tokens.append(Token("EOF", "", linea, n - inicio + 1))
    return tokens
