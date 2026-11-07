"""
Analizador léxico del lenguaje MILPA.

Convierte el codigo fuente en una secuencia de tokens
"""

from dataclasses import dataclass
from src.core.errors import ErrorLog

# Representa un token del lenguaje
@dataclass
class Token:
    tipo: str
    valor: str
    linea: int
    columna: int

class Lexer:
    #Palabras reservadas del lenguaje MILPA
    PALABRAS_RESERVADAS = {
        "zona": "ZONA",
        "constante": "CONSTANTE",
        "entero": "TIPO_ENTERO",
        "decimal": "TIPO_DECIMAL",
        "texto": "TIPO_TEXTO",
        "booleano": "TIPO_BOOLEANO",
        "si": "SI",
        "si_no": "SI_NO",
        "mientras": "MIENTRAS",
        "para_cada": "PARA_CADA",
        "en": "EN",
        "verdadero": "VERDADERO",
        "falso": "FALSO",
    }

    # Operadores y símbolos del lenguaje
    SIMBOLOS = {
        "+": "SUMA",
        "-": "RESTA",
        "*": "MULTIPLICACION",
        "/": "DIVISION",
        "%": "MODULO",
        "=": "ASIGNACION",
        "==": "IGUAL",
        "!=": "DIFERENTE",
        "<": "MENOR",
        "<=": "MENOR_IGUAL",
        ">": "MAYOR",
        ">=": "MAYOR_IGUAL",
        "{": "LLAVE_ABRE",
        "}": "LLAVE_CIERRA",
        "(": "PARENTESIS_ABRE",
        ")": "PARENTESIS_CIERRA",
        "[": "CORCHETE_ABRE",
        "]": "CORCHETE_CIERRA",
        ",": "COMA",
        ":": "DOS_PUNTOS",
        ".": "PUNTO",
    }

    def __init__(self, codigo, errores = None):
        self.codigo = codigo
        self.errores = errores if errores is not None else ErrorLog()

        self.tokens = []
        self.posicion = 0
        self.linea = 1
        self.columna = 1

    # Devuelve el carácter actual
    def actual(self):
        if self.posicion >= len(self.codigo):
            return None

        return self.codigo[self.posicion]

    # Devuelve el siguiente carácter
    def siguiente(self):
        posicion = self.posicion + 1

        if posicion >= len(self.codigo):
            return None

        return self.codigo[posicion]

    # Avanza una posición en el código
    def avanzar(self):
        caracter = self.actual()

        if caracter is None:
            return

        self.posicion += 1

        if caracter == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1

    # Agrega un token a la lista
    def agregar_token(self, tipo, valor, linea, columna):
        self.tokens.append(
            Token(tipo, valor, linea, columna)
        )

    # Analiza los identificadores y palabras reservadas
    def leer_identificador(self):
        inicio = self.posicion
        linea = self.linea
        columna = self.columna

        while self.actual() is not None:
            caracter = self.actual()

            assert caracter is not None
            if not (caracter.isalnum() or caracter == "_"):
                break

            self.avanzar()

        palabra = self.codigo[inicio:self.posicion]

        tipo = self.PALABRAS_RESERVADAS.get(
            palabra, "ID"
        )

        self.agregar_token(
            tipo, palabra, linea, columna
        )

    # Analiza números enteros y decimales
    def leer_numero(self):
        inicio = self.posicion
        linea = self.linea
        columna = self.columna

        assert self.actual() is not None
        while self.actual() is not None and self.actual().isdigit(): # type: ignore
            self.avanzar()

        tipo = "ENTERO"

        # Comprueba si el número tiene decimales
        if self.actual() == "." and (
            self.siguiente() is not None
            and self.siguiente().isdigit() # type: ignore
        ):
            tipo = "DECIMAL"
            self.avanzar()

            while self.actual() is not None and self.actual().isdigit(): # type: ignore
                self.avanzar()

        valor = self.codigo[inicio:self.posicion]

        self.agregar_token(
            tipo, valor, linea, columna
        )

    # Analiza cadenas de texto
    def leer_texto(self):
        linea = self.linea
        columna = self.columna

        self.avanzar()  # Omite la comilla inicial

        inicio = self.posicion

        while self.actual() is not None and self.actual() != '"':
            if self.actual() == "\n":
                break

            self.avanzar()

        if self.actual() != '"':
            self.errores.agregar(
                "léxico",
                "E-LEX-02",
                linea,
                columna,
                "Texto sin cerrar"
            )
            return

        valor = self.codigo[inicio:self.posicion]

        self.avanzar()  # Omite la comilla final

        self.agregar_token(
            "TEXTO", valor, linea, columna
        )

    # Realiza el análisis léxico completo
    def analizar(self):

        while self.actual() is not None:

            caracter = self.actual()

            # Ignora espacios y tabulaciones
            if caracter in " \t\r": # type: ignore
                self.avanzar()
                continue

            # Ignora saltos de línea
            if caracter == "\n":
                self.avanzar()
                continue

            # Identificadores y palabras reservadas
            assert caracter is not None
            if caracter.isalpha() or caracter == "_":
                self.leer_identificador()
                continue

            # Números
            if caracter.isdigit():
                self.leer_numero()
                continue

            # Cadenas de texto
            if caracter == '"':
                self.leer_texto()
                continue

            # Operadores de dos caracteres
            dos_caracteres = (
                caracter + self.siguiente()
                if self.siguiente() is not None
                else ""
            )

            if dos_caracteres in self.SIMBOLOS:
                linea = self.linea
                columna = self.columna

                self.agregar_token(
                    self.SIMBOLOS[dos_caracteres],
                    dos_caracteres,
                    linea,
                    columna
                )

                self.avanzar()
                self.avanzar()
                continue

            # Operadores y símbolos de un carácter
            if caracter in self.SIMBOLOS:
                linea = self.linea
                columna = self.columna

                self.agregar_token(
                    self.SIMBOLOS[caracter],
                    caracter,
                    linea,
                    columna
                )

                self.avanzar()
                continue

            # Carácter no reconocido
            self.errores.agregar(
                "léxico",
                "E-LEX-01",
                self.linea,
                self.columna,
                f"Carácter inválido: {caracter}"
            )

            self.avanzar()

        # Marca el final del código fuente
        self.agregar_token(
            "EOF", "", self.linea, self.columna
        )

        return self.tokens
    
    
    # Imprime los tokens en formato de tabla
    def imprimir_tabla(self):

        if not self.tokens:
            print("\nNo hay tokens para mostrar.")
            return

        encabezados = ["TIPO", "VALOR", "LINEA", "COLUMNA"]

        # Prepara los datos de cada token
        filas = [
            [
                token.tipo,
                token.valor if token.valor else "EOF",
                str(token.linea),
                str(token.columna)
            ]
            for token in self.tokens
        ]

        # Calcula el ancho necesario para cada columna
        anchos = []

        for i, encabezado in enumerate(encabezados):
            ancho = max(
                len(encabezado),
                max(len(fila[i]) for fila in filas)
            )
            anchos.append(ancho)

        # Construye los separadores de la tabla
        separador = "+".join(
            "-" * (ancho + 2) for ancho in anchos
        )

        # Imprime encabezados
        print("\nTABLA DE TOKENS - MILPA")
        print("+" + separador + "+")

        print(
            "| " +
            " | ".join(
                encabezados[i].ljust(anchos[i])
                for i in range(len(encabezados))
            ) +
            " |"
        )

        print("+" + separador + "+")

        # Imprime cada token
        for fila in filas:
            print(
                "| " +
                " | ".join(
                    fila[i].ljust(anchos[i])
                    for i in range(len(fila))
                ) +
                " |"
            )

        print("+" + separador + "+")
        print(f"Total de tokens: {len(self.tokens)}")
