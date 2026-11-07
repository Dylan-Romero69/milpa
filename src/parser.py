
"""
Analizador sintáctico del lenguaje MILPA.

Recibe los tokens del lexer y construye el AST.
Utiliza análisis descendente recursivo.
"""

from src.frontend.ast_nodes import (
    Programa,
    DeclaracionVariable,
    DeclaracionConstante,
    DeclaracionZona,
    CampoZona,
    Asignacion,
    Condicional,
    CicloMientras,
    CicloParaCada,
    LlamadaFuncion,
    OperacionBinaria,
    OperacionUnaria,
    Literal,
    Identificador,
    AccesoCampo
)


class ErrorSintactico(Exception):
    """Detiene el análisis cuando encuentra un error sintáctico."""
    pass


class Parser:

    TIPOS = {
        "TIPO_ENTERO": "entero",
        "TIPO_DECIMAL": "decimal",
        "TIPO_TEXTO": "texto",
        "TIPO_BOOLEANO": "booleano"
    }

    OPERADORES = {
        "SUMA": "+",
        "RESTA": "-",
        "MULTIPLICACION": "*",
        "DIVISION": "/",
        "MODULO": "%",
        "IGUAL": "==",
        "DIFERENTE": "!=",
        "MENOR": "<",
        "MENOR_IGUAL": "<=",
        "MAYOR": ">",
        "MAYOR_IGUAL": ">="
    }

    def __init__(self, tokens, errores=None):
        self.tokens = tokens
        self.errores = errores
        self.posicion = 0

    # Devuelve el token actual
    def actual(self):
        if self.posicion >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[self.posicion]

    # Devuelve el siguiente token
    def siguiente(self):
        posicion = self.posicion + 1

        if posicion >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[posicion]

    # Comprueba si el token actual tiene determinado tipo
    def comprobar(self, tipo):
        return self.actual().tipo == tipo

    # Avanza al siguiente token
    def avanzar(self):
        token = self.actual()

        if token.tipo != "EOF":
            self.posicion += 1

        return token

    # Exige un tipo de token determinado
    def consumir(self, tipo):
        if self.comprobar(tipo):
            return self.avanzar()

        self.error(
            f"Se esperaba {tipo}, pero se encontró "
            f"{self.actual().tipo}"
        )

    # Registra un error sintáctico
    def error(self, mensaje):
        token = self.actual()

        if self.errores is not None:
            self.errores.agregar(
                "sintáctico",
                "E-SIN-01",
                token.linea,
                token.columna,
                mensaje
            )

        raise ErrorSintactico(mensaje)

    # Comprueba si el identificador actual es una palabra lógica
    def comprobar_logico(self, palabra):
        return (
            self.comprobar("ID")
            and self.actual().valor == palabra
        )

    # Analiza el programa completo
    def analizar(self):
        instrucciones = []

        try:
            while not self.comprobar("EOF"):
                instrucciones.append(self.sentencia())

            return Programa(instrucciones=instrucciones)

        except ErrorSintactico:
            return None

    # Determina qué tipo de sentencia debe analizar
    def sentencia(self):

        if self.comprobar("ZONA"):
            return self.declaracion_zona()

        if self.comprobar("CONSTANTE"):
            return self.declaracion_constante()

        if self.actual().tipo in self.TIPOS:
            return self.declaracion_variable()

        if self.comprobar("SI"):
            return self.condicional()

        if self.comprobar("MIENTRAS"):
            return self.ciclo_mientras()

        if self.comprobar("PARA_CADA"):
            return self.ciclo_para_cada()

        if self.comprobar("ID"):
            return self.sentencia_identificador()

        self.error("Sentencia no válida")

    # Analiza declaraciones de variables
    def declaracion_variable(self):
        token_tipo = self.avanzar()
        tipo = self.TIPOS[token_tipo.tipo]

        nombre = self.consumir("ID")

        self.consumir("ASIGNACION")

        valor = self.expresion()

        return DeclaracionVariable(
            tipo=tipo,
            nombre=nombre.valor,
            valor=valor,
            linea=token_tipo.linea,
            columna=token_tipo.columna
        )

    # Analiza declaraciones de constantes
    def declaracion_constante(self):
        inicio = self.consumir("CONSTANTE")

        token_tipo = self.actual()

        if token_tipo.tipo not in self.TIPOS:
            self.error("Se esperaba un tipo de dato")

        tipo = self.TIPOS[self.avanzar().tipo]

        nombre = self.consumir("ID")

        self.consumir("ASIGNACION")

        valor = self.expresion()

        return DeclaracionConstante(
            tipo=tipo,
            nombre=nombre.valor,
            valor=valor,
            linea=inicio.linea,
            columna=inicio.columna
        )

    # Analiza declaraciones de zonas
    def declaracion_zona(self):
        inicio = self.consumir("ZONA")
        nombre = self.consumir("ID")

        self.consumir("LLAVE_ABRE")

        campos = []

        while not self.comprobar("LLAVE_CIERRA"):
            campo = self.consumir("ID")

            self.consumir("DOS_PUNTOS")

            valor = self.expresion()

            campos.append(
                CampoZona(
                    nombre=campo.valor,
                    valor=valor,
                    linea=campo.linea,
                    columna=campo.columna
                )
            )

            if not self.comprobar("LLAVE_CIERRA"):
                self.consumir("COMA")

        self.consumir("LLAVE_CIERRA")

        return DeclaracionZona(
            nombre=nombre.valor,
            campos=campos,
            linea=inicio.linea,
            columna=inicio.columna
        )

    # Analiza asignaciones o llamadas a funciones
    def sentencia_identificador(self):
        nombre = self.consumir("ID")

        # Comprueba si es una asignación
        if self.comprobar("ASIGNACION"):
            self.avanzar()

            valor = self.expresion()

            return Asignacion(
                nombre=nombre.valor,
                valor=valor,
                linea=nombre.linea,
                columna=nombre.columna
            )

        # Comprueba si es una llamada a función
        if self.comprobar("PARENTESIS_ABRE"):
            return self.llamada_funcion(nombre)

        self.error("Se esperaba una asignación o llamada a función")

    # Analiza llamadas a funciones
    def llamada_funcion(self, nombre=None):

        if nombre is None:
            nombre = self.consumir("ID")

        self.consumir("PARENTESIS_ABRE")

        argumentos = []

        if not self.comprobar("PARENTESIS_CIERRA"):
            argumentos.append(self.expresion())

            while self.comprobar("COMA"):
                self.avanzar()
                argumentos.append(self.expresion())

        self.consumir("PARENTESIS_CIERRA")

        return LlamadaFuncion(
            nombre=nombre.valor,
            argumentos=argumentos,
            linea=nombre.linea,
            columna=nombre.columna
        )

    # Analiza una condición si / si_no
    def condicional(self):
        inicio = self.consumir("SI")

        self.consumir("PARENTESIS_ABRE")
        condicion = self.expresion()
        self.consumir("PARENTESIS_CIERRA")

        bloque_si = self.bloque()
        bloque_si_no = []

        if self.comprobar("SI_NO"):
            self.avanzar()
            bloque_si_no = self.bloque()

        return Condicional(
            condicion=condicion,
            bloque_si=bloque_si,
            bloque_si_no=bloque_si_no,
            linea=inicio.linea,
            columna=inicio.columna
        )

    # Analiza un ciclo mientras
    def ciclo_mientras(self):
        inicio = self.consumir("MIENTRAS")

        self.consumir("PARENTESIS_ABRE")
        condicion = self.expresion()
        self.consumir("PARENTESIS_CIERRA")

        instrucciones = self.bloque()

        return CicloMientras(
            condicion=condicion,
            instrucciones=instrucciones,
            linea=inicio.linea,
            columna=inicio.columna
        )

    # Analiza un ciclo para_cada
    def ciclo_para_cada(self):
        inicio = self.consumir("PARA_CADA")

        self.consumir("ZONA")

        variable = self.consumir("ID")

        self.consumir("EN")
        self.consumir("CORCHETE_ABRE")

        zonas = [self.consumir("ID").valor]

        while self.comprobar("COMA"):
            self.avanzar()
            zonas.append(self.consumir("ID").valor)

        self.consumir("CORCHETE_CIERRA")

        instrucciones = self.bloque()

        return CicloParaCada(
            tipo="zona",
            variable=variable.valor,
            zonas=zonas,
            instrucciones=instrucciones,
            linea=inicio.linea,
            columna=inicio.columna
        )

    # Analiza un bloque de instrucciones
    def bloque(self):
        self.consumir("LLAVE_ABRE")

        instrucciones = []

        while not self.comprobar("LLAVE_CIERRA"):
            if self.comprobar("EOF"):
                self.error("Bloque sin llave de cierre")

            instrucciones.append(self.sentencia())

        self.consumir("LLAVE_CIERRA")

        return instrucciones

    # Expresiones lógicas OR
    def expresion(self):
        izquierda = self.expresion_y()

        while self.comprobar_logico("o"):
            operador = self.avanzar()

            derecha = self.expresion_y()

            izquierda = OperacionBinaria(
                izquierda=izquierda,
                operador=operador.valor,
                derecha=derecha
            )

        return izquierda

    # Expresiones lógicas AND
    def expresion_y(self):
        izquierda = self.expresion_no()

        while self.comprobar_logico("y"):
            operador = self.avanzar()

            derecha = self.expresion_no()

            izquierda = OperacionBinaria(
                izquierda=izquierda,
                operador=operador.valor,
                derecha=derecha
            )

        return izquierda

    # Negación lógica
    def expresion_no(self):

        if self.comprobar_logico("no"):
            operador = self.avanzar()

            return OperacionUnaria(
                operador=operador.valor,
                operando=self.expresion_no()
            )

        return self.expresion_relacional()

    # Expresiones relacionales
    def expresion_relacional(self):
        izquierda = self.expresion_aritmetica()

        if self.actual().tipo in (
            "IGUAL",
            "DIFERENTE",
            "MENOR",
            "MENOR_IGUAL",
            "MAYOR",
            "MAYOR_IGUAL"
        ):
            operador = self.avanzar()

            derecha = self.expresion_aritmetica()

            return OperacionBinaria(
                izquierda=izquierda,
                operador=self.OPERADORES[operador.tipo],
                derecha=derecha
            )

        return izquierda

    # Sumas y restas
    def expresion_aritmetica(self):
        izquierda = self.termino()

        while self.comprobar("SUMA") or self.comprobar("RESTA"):
            operador = self.avanzar()

            derecha = self.termino()

            izquierda = OperacionBinaria(
                izquierda=izquierda,
                operador=self.OPERADORES[operador.tipo],
                derecha=derecha
            )

        return izquierda

    # Multiplicaciones, divisiones y módulos
    def termino(self):
        izquierda = self.factor()

        while self.actual().tipo in (
            "MULTIPLICACION",
            "DIVISION",
            "MODULO"
        ):
            operador = self.avanzar()

            derecha = self.factor()

            izquierda = OperacionBinaria(
                izquierda=izquierda,
                operador=self.OPERADORES[operador.tipo],
                derecha=derecha
            )

        return izquierda

    # Factores y operaciones unarias
    def factor(self):

        if self.comprobar("RESTA"):
            self.avanzar()

            return OperacionUnaria(
                operador="-",
                operando=self.factor()
            )

        return self.primario()

    # Analiza los elementos básicos de una expresión
    def primario(self):

        token = self.actual()

        if self.comprobar("ENTERO"):
            self.avanzar()

            return Literal(
                valor=int(token.valor),
                tipo="entero",
                linea=token.linea,
                columna=token.columna
            )

        if self.comprobar("DECIMAL"):
            self.avanzar()

            return Literal(
                valor=float(token.valor),
                tipo="decimal",
                linea=token.linea,
                columna=token.columna
            )

        if self.comprobar("TEXTO"):
            self.avanzar()

            return Literal(
                valor=token.valor,
                tipo="texto",
                linea=token.linea,
                columna=token.columna
            )

        if self.comprobar("VERDADERO") or self.comprobar("FALSO"):
            self.avanzar()

            return Literal(
                valor=token.tipo == "VERDADERO",
                tipo="booleano",
                linea=token.linea,
                columna=token.columna
            )

        if self.comprobar("ID"):

            nombre = self.avanzar()

            if self.comprobar("PARENTESIS_ABRE"):
                return self.llamada_funcion(nombre)

            if self.comprobar("PUNTO"):
                self.avanzar()

                campo = self.consumir("ID")

                return AccesoCampo(
                    zona=nombre.valor,
                    campo=campo.valor,
                    linea=nombre.linea,
                    columna=nombre.columna
                )

            return Identificador(
                nombre=nombre.valor,
                linea=nombre.linea,
                columna=nombre.columna
            )

        if self.comprobar("PARENTESIS_ABRE"):
            self.avanzar()

            expresion = self.expresion()

            self.consumir("PARENTESIS_CIERRA")

            return expresion

        self.error("Expresión no válida")
