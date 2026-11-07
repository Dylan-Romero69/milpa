
import re


"""Conversión de expresiones entre infija, postfija y prefija."""


# Precedencia de operadores
PRECEDENCIA = {
    "o": 1,
    "y": 2,
    "==": 3,
    "!=": 3,
    "<": 3,
    ">": 3,
    "<=": 3,
    ">=": 3,
    "+": 4,
    "-": 4,
    "*": 5,
    "/": 5,
    "%": 5,
    "^": 6,
    "u-": 7,
    "u_no": 7,
}

ASOCIATIVIDAD_DERECHA = {"^", "u-", "u_no"}

PATRON = re.compile(
    r"\d+(?:\.\d+)?|"
    r"[a-zA-Z_][a-zA-Z0-9_]*|"
    r"<=|>=|==|!=|"
    r"[+\-*/%^()<>]"
)


def tokenizar(expresion):
    """Divide la expresión en tokens."""

    if isinstance(expresion, (list, tuple)):
        return [str(token) for token in expresion]

    tokens = PATRON.findall(expresion)
    reconstruida = "".join(tokens)

    original = re.sub(r"\s+", "", expresion)

    if reconstruida != original:
        raise ValueError("La expresión contiene caracteres inválidos")

    return tokens


def preparar_operadores(tokens):
    """Identifica operadores unarios."""

    resultado = []

    for i, token in enumerate(tokens):
        if token == "-":
            es_unario = (
                i == 0
                or tokens[i - 1] in PRECEDENCIA
                or tokens[i - 1] == "("
            )

            if es_unario:
                token = "u-"

        elif token.lower() == "no":
            token = "u_no"

        resultado.append(token)

    return resultado


def a_postfija(expresion):
    """Convierte una expresión infija a postfija."""

    tokens = preparar_operadores(tokenizar(expresion))

    salida = []
    pila = []

    for token in tokens:

        if token == "(":
            pila.append(token)

        elif token == ")":

            while pila and pila[-1] != "(":
                salida.append(pila.pop())

            if not pila:
                raise ValueError("Paréntesis desbalanceados")

            pila.pop()

        elif token in PRECEDENCIA:

            while (
                pila
                and pila[-1] in PRECEDENCIA
                and (
                    PRECEDENCIA[pila[-1]] > PRECEDENCIA[token]
                    or (
                        PRECEDENCIA[pila[-1]] == PRECEDENCIA[token]
                        and token not in ASOCIATIVIDAD_DERECHA
                    )
                )
            ):
                salida.append(pila.pop())

            pila.append(token)

        else:
            salida.append(token)

    while pila:
        operador = pila.pop()

        if operador in {"(", ")"}:
            raise ValueError("Paréntesis desbalanceados")

        salida.append(operador)

    return " ".join(salida)


def a_prefija(expresion):
    """Convierte una expresión infija a prefija."""

    postfija = a_postfija(expresion).split()
    pila = []

    operadores_unarios = {"u-", "u_no"}

    for token in postfija:

        if token in PRECEDENCIA:

            if token in operadores_unarios:
                if not pila:
                    raise ValueError("Falta un operando")

                operando = pila.pop()
                pila.append((token, operando))

            else:
                if len(pila) < 2:
                    raise ValueError("Faltan operandos")

                derecha = pila.pop()
                izquierda = pila.pop()

                pila.append((token, izquierda, derecha))

        else:
            pila.append(token)

    if len(pila) != 1:
        raise ValueError("Expresión inválida")

    def recorrer(nodo):
        if isinstance(nodo, str):
            return nodo

        return " ".join(
            [nodo[0]] + [recorrer(hijo) for hijo in nodo[1:]]
        )

    return recorrer(pila[0])
