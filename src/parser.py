"""Analizador sintáctico descendente recursivo: tokens -> AST. Responsable: A.

Sigue la GLC del documento de definición. Se detiene en el primer error
(E-SIN-01) y lo registra en el log con la posición del token problemático.
Devuelve un Programa, o None si hubo error.
"""
from src import ast_nodes as A

TIPOS = {"entero", "decimal", "texto", "booleano"}
OP_REL = {"==", "!=", "<", "<=", ">", ">="}


class ErrorSintactico(Exception):
    def __init__(self, token, mensaje):
        super().__init__(mensaje)
        self.token = token
        self.mensaje = mensaje


def describir(tok):
    if tok.tipo == "EOF":
        return "el fin del archivo"
    if tok.tipo == "TEXTO":
        return f'el texto "{tok.lexema}"'
    return f"'{tok.lexema}'"


class Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    # ---- utilidades ----
    @property
    def actual(self):
        return self.t[self.i]

    def siguiente(self):
        return self.t[min(self.i + 1, len(self.t) - 1)]

    def avanzar(self):
        tok = self.t[self.i]
        if tok.tipo != "EOF":
            self.i += 1
        return tok

    def es(self, tipo, lexema=None):
        tok = self.actual
        return tok.tipo == tipo and (lexema is None or tok.lexema == lexema)

    def espera(self, tipo, lexema=None, que=None):
        if self.es(tipo, lexema):
            return self.avanzar()
        if que is None:
            que = f"'{lexema}'" if lexema else tipo
        raise ErrorSintactico(
            self.actual, f"se esperaba {que} pero se encontró {describir(self.actual)}")

    # ---- programa y sentencias ----
    def programa(self):
        sentencias = []
        while not self.es("EOF"):
            sentencias.append(self.sentencia())
        return A.Programa(sentencias=sentencias, linea=1, col=1)

    def bloque(self):
        self.espera("DELIMITADOR", "{")
        sentencias = []
        while not self.es("DELIMITADOR", "}"):
            if self.es("EOF"):
                raise ErrorSintactico(
                    self.actual, "se esperaba '}' pero se encontró el fin del archivo "
                                 "(falta cerrar un bloque)")
            sentencias.append(self.sentencia())
        self.avanzar()  # }
        return sentencias

    def sentencia(self):
        tok = self.actual
        if tok.tipo == "PALABRA_RESERVADA":
            lx = tok.lexema
            if lx == "zona":
                return self.decl_zona()
            if lx == "constante":
                return self.decl_const()
            if lx in TIPOS:
                return self.decl_var()
            if lx == "si":
                return self.si()
            if lx == "mientras":
                return self.mientras()
            if lx == "repetir":
                return self.repetir()
            if lx == "para_cada":
                return self.para_cada()
            raise ErrorSintactico(tok, f"no se esperaba '{lx}' aquí")
        if tok.tipo == "ID":
            sig = self.siguiente()
            if sig.tipo == "OPERADOR" and sig.lexema == "=":
                return self.asignacion()
            if sig.tipo == "DELIMITADOR" and sig.lexema == "(":
                return self.llamada()
            raise ErrorSintactico(
                sig, f"se esperaba '=' o '(' después de '{tok.lexema}' "
                     f"pero se encontró {describir(sig)}")
        raise ErrorSintactico(tok, f"sentencia inesperada: {describir(tok)}")

    def decl_zona(self):
        tok = self.avanzar()  # zona
        nombre = self.espera("ID", que="un nombre de zona").lexema
        self.espera("DELIMITADOR", "{")
        campos = [self.campo_zona()]
        while self.es("DELIMITADOR", ","):
            self.avanzar()
            campos.append(self.campo_zona())
        self.espera("DELIMITADOR", "}")
        return A.DeclZona(nombre=nombre, campos=campos, linea=tok.linea, col=tok.col)

    def campo_zona(self):
        tok = self.espera("ID", que="un nombre de campo")
        self.espera("DELIMITADOR", ":")
        return A.CampoZona(nombre=tok.lexema, valor=self.exp(), linea=tok.linea, col=tok.col)

    def decl_const(self):
        tok = self.avanzar()  # constante
        if not (self.actual.tipo == "PALABRA_RESERVADA" and self.actual.lexema in TIPOS):
            raise ErrorSintactico(
                self.actual, f"se esperaba un tipo (entero, decimal, texto o booleano) "
                             f"pero se encontró {describir(self.actual)}")
        tipo = self.avanzar().lexema
        nombre = self.espera("ID", que="un nombre de constante").lexema
        self.espera("OPERADOR", "=")
        return A.DeclConst(tipo_decl=tipo, nombre=nombre, valor=self.exp(),
                           linea=tok.linea, col=tok.col)

    def decl_var(self):
        tok = self.avanzar()  # tipo
        nombre = self.espera("ID", que="un nombre de variable").lexema
        self.espera("OPERADOR", "=")
        return A.DeclVar(tipo_decl=tok.lexema, nombre=nombre, valor=self.exp(),
                         linea=tok.linea, col=tok.col)

    def asignacion(self):
        tok = self.avanzar()  # ID
        self.avanzar()        # =
        return A.Asig(nombre=tok.lexema, valor=self.exp(), linea=tok.linea, col=tok.col)

    def si(self):
        tok = self.avanzar()  # si
        self.espera("DELIMITADOR", "(")
        cond = self.exp()
        self.espera("DELIMITADOR", ")")
        entonces = self.bloque()
        sino = None
        if self.es("PALABRA_RESERVADA", "si_no"):
            self.avanzar()
            sino = self.bloque()
        return A.Si(cond=cond, entonces=entonces, sino=sino, linea=tok.linea, col=tok.col)

    def mientras(self):
        tok = self.avanzar()  # mientras
        self.espera("DELIMITADOR", "(")
        cond = self.exp()
        self.espera("DELIMITADOR", ")")
        return A.Mientras(cond=cond, cuerpo=self.bloque(), linea=tok.linea, col=tok.col)

    def repetir(self):
        tok = self.avanzar()  # repetir
        cuerpo = self.bloque()
        self.espera("PALABRA_RESERVADA", "mientras")
        self.espera("DELIMITADOR", "(")
        cond = self.exp()
        self.espera("DELIMITADOR", ")")
        return A.Repetir(cuerpo=cuerpo, cond=cond, linea=tok.linea, col=tok.col)

    def para_cada(self):
        tok = self.avanzar()  # para_cada
        self.espera("PALABRA_RESERVADA", "zona")
        var = self.espera("ID", que="un nombre para la zona").lexema
        self.espera("PALABRA_RESERVADA", "en")
        self.espera("DELIMITADOR", "[")
        zonas = [self.espera("ID", que="el nombre de una zona").lexema]
        while self.es("DELIMITADOR", ","):
            self.avanzar()
            zonas.append(self.espera("ID", que="el nombre de una zona").lexema)
        self.espera("DELIMITADOR", "]")
        return A.ParaCada(var=var, zonas=zonas, cuerpo=self.bloque(),
                          linea=tok.linea, col=tok.col)

    def llamada(self):
        tok = self.avanzar()  # ID
        self.espera("DELIMITADOR", "(")
        args = []
        if not self.es("DELIMITADOR", ")"):
            args.append(self.exp())
            while self.es("DELIMITADOR", ","):
                self.avanzar()
                args.append(self.exp())
        self.espera("DELIMITADOR", ")")
        return A.Llamada(nombre=tok.lexema, args=args, linea=tok.linea, col=tok.col)

    # ---- expresiones (de menor a mayor precedencia) ----
    def exp(self):
        izq = self.exp_y()
        while self.es("PALABRA_RESERVADA", "o"):
            op = self.avanzar()
            izq = A.BinOp(op="o", izq=izq, der=self.exp_y(), linea=op.linea, col=op.col)
        return izq

    def exp_y(self):
        izq = self.exp_no()
        while self.es("PALABRA_RESERVADA", "y"):
            op = self.avanzar()
            izq = A.BinOp(op="y", izq=izq, der=self.exp_no(), linea=op.linea, col=op.col)
        return izq

    def exp_no(self):
        if self.es("PALABRA_RESERVADA", "no"):
            op = self.avanzar()
            return A.UnOp(op="no", operando=self.exp_no(), linea=op.linea, col=op.col)
        return self.exp_rel()

    def exp_rel(self):
        izq = self.exp_arit()
        if self.actual.tipo == "OPERADOR" and self.actual.lexema in OP_REL:
            op = self.avanzar()
            izq = A.BinOp(op=op.lexema, izq=izq, der=self.exp_arit(),
                          linea=op.linea, col=op.col)
        return izq

    def exp_arit(self):
        izq = self.termino()
        while self.actual.tipo == "OPERADOR" and self.actual.lexema in ("+", "-"):
            op = self.avanzar()
            izq = A.BinOp(op=op.lexema, izq=izq, der=self.termino(),
                          linea=op.linea, col=op.col)
        return izq

    def termino(self):
        izq = self.factor()
        while self.actual.tipo == "OPERADOR" and self.actual.lexema in ("*", "/", "%"):
            op = self.avanzar()
            izq = A.BinOp(op=op.lexema, izq=izq, der=self.factor(),
                          linea=op.linea, col=op.col)
        return izq

    def factor(self):
        if self.es("OPERADOR", "-"):
            op = self.avanzar()
            return A.UnOp(op="neg", operando=self.factor(), linea=op.linea, col=op.col)
        return self.primario()

    def primario(self):
        tok = self.actual
        pos = dict(linea=tok.linea, col=tok.col)
        if tok.tipo == "ENTERO":
            self.avanzar()
            return A.Literal(tipo_lit="entero", valor=int(tok.lexema), **pos)
        if tok.tipo == "DECIMAL":
            self.avanzar()
            return A.Literal(tipo_lit="decimal", valor=float(tok.lexema), **pos)
        if tok.tipo == "TEXTO":
            self.avanzar()
            return A.Literal(tipo_lit="texto", valor=tok.lexema, **pos)
        if tok.tipo == "PALABRA_RESERVADA" and tok.lexema in ("verdadero", "falso"):
            self.avanzar()
            return A.Literal(tipo_lit="booleano", valor=(tok.lexema == "verdadero"), **pos)
        if tok.tipo == "ID":
            sig = self.siguiente()
            if sig.tipo == "DELIMITADOR" and sig.lexema == ".":
                self.avanzar()
                self.avanzar()
                campo = self.espera("ID", que="el nombre de un campo").lexema
                return A.AccesoCampo(objeto=tok.lexema, campo=campo, **pos)
            if sig.tipo == "DELIMITADOR" and sig.lexema == "(":
                return self.llamada()
            self.avanzar()
            return A.Var(nombre=tok.lexema, **pos)
        if self.es("DELIMITADOR", "("):
            self.avanzar()
            e = self.exp()
            self.espera("DELIMITADOR", ")")
            return e
        raise ErrorSintactico(tok, f"se esperaba una expresión pero se encontró {describir(tok)}")


def parsear(tokens, log):
    """Devuelve el Programa (AST) o None si hay un error sintáctico (queda en `log`)."""
    try:
        return Parser(tokens).programa()
    except ErrorSintactico as e:
        log.agregar("sintáctico", "E-SIN-01", e.token.linea, e.token.col, e.mensaje)
        return None
