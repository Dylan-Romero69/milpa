"""Análisis semántico: tipos, casting, ámbitos y validaciones V1 a V3. Responsable: A."""
from dataclasses import dataclass

from old.ast_nodes import (AccesoCampo, Asig, BinOp, DeclConst, DeclVar, DeclZona,
                           Literal, Llamada, Mientras, ParaCada, Programa, Repetir,
                           Si, UnOp, Var)
from src.symtab import ErrorTabla

NUM = ("entero", "decimal")


def reportar(log, codigo, linea, col, mensaje):
    """Único punto que usa el ErrorLog. Fase: 'dominio' para E-DOM, si no 'semántico'."""
    fase = "dominio" if codigo.startswith("E-DOM") else "semántico"
    log.agregar(fase, codigo, linea, col, mensaje)


# ---------------------------------------------------------------- tipos ----
def para_asignar(destino, origen):
    """'' = sin cambio, 'i2d' = insertar conversión, None = error E-SEM-03."""
    if destino == origen:
        return ""
    if destino == "decimal" and origen == "entero":
        return "i2d"
    return None


def tipo_binario(op, t1, t2):
    """Tipo del resultado, o None (E-SEM-03). Si se mezclan entero y decimal,
    al operando entero se le inserta i2d."""
    if op in ("+", "-", "*", "/") and t1 in NUM and t2 in NUM:
        return "decimal" if "decimal" in (t1, t2) else "entero"
    if op == "%" and t1 == t2 == "entero":
        return "entero"
    if op in ("<", "<=", ">", ">=") and t1 in NUM and t2 in NUM:
        return "booleano"
    if op in ("==", "!=") and ((t1 in NUM and t2 in NUM) or t1 == t2 == "booleano"):
        return "booleano"
    if op in ("y", "o") and t1 == t2 == "booleano":
        return "booleano"
    return None


def tipo_unario(op, t):
    """op es 'neg' (menos unario) o 'no'."""
    if op == "neg" and t in NUM:
        return t
    if op == "no" and t == "booleano":
        return "booleano"
    return None


# ------------------------------------------------- funciones predefinidas ---
# nombre: (tipos de los parámetros, tipo que devuelve)
FUNCIONES = {
    "leer": (["texto"], "decimal"),
    "lloviendo": ([], "booleano"),
    "regar": (["zona", "entero"], None),
    "registrar": ("*", None),          # uno o más valores de cualquier tipo
    "a_entero": (["decimal"], "entero"),
}
SENSORES = ("humedad", "temperatura")  # V1
CAMPOS_ZONA = {"cultivo": "texto", "humedad_min": "entero", "riego_max": "entero"}
CAMPOS_LECTURA = {**CAMPOS_ZONA, "nombre": "texto"}   # z.nombre se genera solo


def comprobar_argumentos(nombre, tipos):
    """None si está bien; si no, el mensaje para E-SEM-05."""
    params, _ = FUNCIONES[nombre]
    if params == "*":
        if not tipos or "zona" in tipos:
            return f"'{nombre}' necesita uno o más valores (no zonas)"
        return None
    if len(tipos) != len(params):
        return f"'{nombre}' espera {len(params)} argumento(s) y recibió {len(tipos)}"
    for esperado, real in zip(params, tipos):
        if esperado == "zona":
            bien = real == "zona"
        else:
            bien = para_asignar(esperado, real) is not None
        if not bien:
            return f"'{nombre}' esperaba {esperado} y recibió {real}"
    return None


# ------------------------------------------------ plegado de constantes ----
def plegar(op, a, b, ambos_enteros):
    """Calcula 'a op b' con valores conocidos; None si no se puede (división entre 0)."""
    if op in ("/", "%") and b == 0:
        return None
    if op == "%" or (op == "/" and ambos_enteros):
        q = abs(a) // abs(b)                  # el entero trunca hacia cero, como MIPS
        q = q if (a < 0) == (b < 0) else -q
        return a - b * q if op == "%" else q
    if op == "+": return a + b
    if op == "-": return a - b
    if op == "*": return a * b
    if op == "/": return a / b
    if op == "<": return a < b
    if op == "<=": return a <= b
    if op == ">": return a > b
    if op == ">=": return a >= b
    if op == "==": return a == b
    if op == "!=": return a != b
    if op == "y": return a and b
    return a or b                             # "o"


# ------------------------------------------------------- pila semántica ----
@dataclass
class Elemento:
    simbolo: str            # símbolo gramatical o token (ENTERO, ID, Exp...)
    tipo: str = None        # .tipo
    val: object = None      # .val, si se conoce al compilar
    lugar: str = None       # variable o temporal t# con el resultado
    linea: int = 0
    col: int = 0


class PilaSemantica:
    def __init__(self):
        self.items = []
        self.traza = []     # una línea por paso, para --pila

    def _anotar(self, accion):
        pila = " | ".join(f"{e.simbolo}:{e.tipo}={e.val}" for e in self.items)
        self.traza.append(f"{len(self.traza) + 1:>3}  {accion:<28} [{pila}]")

    def push(self, elemento, accion="apilar"):
        self.items.append(elemento)
        self._anotar(f"{accion} {elemento.simbolo}")

    def pop(self, accion="desapilar"):
        elemento = self.items.pop()
        self._anotar(f"{accion} {elemento.simbolo}")
        return elemento

    def imprimir_traza(self):
        print("\n".join(self.traza))


# ------------------------------------------------------------ recorrido ----
class Analizador:
    """Recorre el AST, llena n.tipo y n.val, y reporta errores.
    Para B (cuádruplos): n.simbolo guarda el Simbolo (dirección) en DeclVar, DeclConst,
    DeclZona, Asig y Var. Si una expresión tiene n.val, es una constante conocida."""

    def __init__(self, tabla, log):
        self.tabla = tabla
        self.log = log
        self.pila = PilaSemantica()
        self.alias = {}      # alias de un para_cada -> lista de sus zonas (Simbolo)

    def error(self, codigo, nodo, mensaje):
        reportar(self.log, codigo, nodo.linea, nodo.col, mensaje)

    def zonas_de(self, nombre):
        """Zonas a las que se refiere un nombre (zona declarada o alias); None si no es zona."""
        if nombre in self.alias:
            return self.alias[nombre]
        s = self.tabla.buscar(nombre)
        if s is not None and s.categoria == "zona":
            return [s]
        return None

    def declarar(self, n, tipo, categoria, valor=None):
        try:
            n.simbolo = self.tabla.declarar(n.nombre, tipo, categoria, valor, True)
        except ErrorTabla as e:
            self.error("E-SEM-02", n, str(e))

    def compatible(self, destino, e, que):
        """Revisa que e se pueda guardar en 'que' (de tipo destino). E-SEM-03 si no."""
        if e.tipo == "error" or para_asignar(destino, e.tipo) is not None:
            return True
        ayuda = " (use a_entero)" if (destino, e.tipo) == ("entero", "decimal") else ""
        self.error("E-SEM-03", e, f"no se puede guardar {e.tipo} en {que} de tipo {destino}{ayuda}")
        return False

    def condicion(self, cond):
        e = self.exp(cond)
        if e.tipo not in ("booleano", "error"):
            self.error("E-SEM-07", e, f"la condición debe ser booleana y es {e.tipo}")

    def bloque(self, sentencias):
        self.tabla.abrir_ambito()
        for s in sentencias:
            self.sentencia(s)
        self.tabla.cerrar_ambito()

    # ---- sentencias ----
    def sentencia(self, n):
        if isinstance(n, Programa):
            for s in n.sentencias:
                self.sentencia(s)
        elif isinstance(n, DeclZona):
            self.decl_zona(n)
        elif isinstance(n, DeclConst):
            self.decl_const(n)
        elif isinstance(n, DeclVar):
            self.decl_var(n)
        elif isinstance(n, Asig):
            self.asignacion(n)
        elif isinstance(n, Si):
            self.condicion(n.cond)
            self.bloque(n.entonces)
            if n.sino is not None:
                self.bloque(n.sino)
        elif isinstance(n, Mientras):
            self.condicion(n.cond)
            self.bloque(n.cuerpo)
        elif isinstance(n, Repetir):
            self.bloque(n.cuerpo)
            self.condicion(n.cond)
        elif isinstance(n, ParaCada):
            self.para_cada(n)
        elif isinstance(n, Llamada):
            self.exp(n)

    def decl_var(self, n):
        e = self.exp(n.valor)              # primero la expresión: "entero x = x" es E-SEM-01
        self.compatible(n.tipo_decl, e, f"la variable '{n.nombre}'")
        self.declarar(n, n.tipo_decl, "variable")
        n.tipo = n.tipo_decl

    def decl_const(self, n):
        e = self.exp(n.valor)
        ok = self.compatible(n.tipo_decl, e, f"la constante '{n.nombre}'")
        valor = e.val if ok else None
        if ok and e.tipo != "error" and valor is None:
            self.error("E-SEM-03", e, "una constante necesita un valor conocido al compilar")
        if valor is not None and n.tipo_decl == "decimal":
            valor = float(valor)
        self.declarar(n, n.tipo_decl, "constante", valor)
        n.tipo, n.val = n.tipo_decl, valor

    def decl_zona(self, n):
        if len(self.tabla.ambitos) > 1:
            self.error("E-SEM-08", n, "una zona solo se puede declarar fuera de los bloques")
        vistos, valores = set(), {}
        for c in n.campos:
            e = self.exp(c.valor)
            if c.nombre not in CAMPOS_ZONA:
                self.error("E-SEM-08", c, f"la zona no tiene el campo '{c.nombre}'")
                continue
            if c.nombre in vistos:
                self.error("E-SEM-08", c, f"el campo '{c.nombre}' está repetido")
                continue
            vistos.add(c.nombre)
            if not self.compatible(CAMPOS_ZONA[c.nombre], e, f"el campo '{c.nombre}'") or e.tipo == "error":
                continue
            if e.val is None:
                self.error("E-SEM-03", e, f"el campo '{c.nombre}' debe tener un valor conocido al compilar")
                continue
            valores[c.nombre] = e.val
            if c.nombre == "humedad_min" and not 0 <= e.val <= 100:     # V3
                self.error("E-DOM-03", e, f"humedad_min = {e.val} está fuera del rango 0 a 100")
            if c.nombre == "riego_max" and e.val <= 0:
                self.error("E-SEM-03", e, "riego_max debe ser un entero positivo")
        for campo in CAMPOS_ZONA:
            if campo not in vistos:
                self.error("E-SEM-08", n, f"falta el campo '{campo}'")
        self.declarar(n, "zona", "zona", valores)     # los campos quedan en Simbolo.valor
        n.tipo = "zona"

    def asignacion(self, n):
        e = self.exp(n.valor)
        s = self.tabla.buscar(n.nombre)
        if s is None and n.nombre not in self.alias:
            self.error("E-SEM-01", n, f"la variable '{n.nombre}' no está declarada")
        elif n.nombre in self.alias or s.categoria == "zona":
            self.error("E-SEM-03", n, f"'{n.nombre}' es una zona y no se le puede asignar")
        elif s.categoria == "constante":
            self.error("E-SEM-06", n, f"'{n.nombre}' es una constante")
        else:
            self.compatible(s.tipo, e, f"la variable '{n.nombre}'")
            n.simbolo, n.tipo = s, s.tipo

    def para_cada(self, n):
        if n.var in self.alias or self.tabla.buscar(n.var) is not None:
            self.error("E-SEM-02", n, f"'{n.var}' ya existe y no se puede usar como alias")
            return
        zonas = []
        for nombre in n.zonas:
            s = self.tabla.buscar(nombre)
            if s is None:
                self.error("E-SEM-01", n, f"la zona '{nombre}' no está declarada")
            elif s.categoria != "zona":
                self.error("E-SEM-03", n, f"'{nombre}' no es una zona")
            else:
                zonas.append(s)
        self.alias[n.var] = zonas
        self.bloque(n.cuerpo)
        del self.alias[n.var]

    # ---- expresiones: cada una deja su resultado en la pila semántica ----
    def exp(self, n):
        """Analiza la expresión n y devuelve su Elemento (ya sacado de la pila)."""
        self.expresion(n)
        return self.pila.pop("usar")

    def expresion(self, n):
        lugar, accion, val = None, "apilar", None
        if isinstance(n, Literal):
            simbolo, tipo, val, lugar = "LIT", n.tipo_lit, n.valor, repr(n.valor)
        elif isinstance(n, Var):
            simbolo, lugar = "ID", n.nombre
            tipo, val = self.var(n)
        elif isinstance(n, AccesoCampo):
            simbolo, lugar = "ID.ID", f"{n.objeto}.{n.campo}"
            tipo = self.campo(n)
        elif isinstance(n, UnOp):
            self.expresion(n.operando)
            e = self.pila.pop("reducir")
            simbolo, accion = n.op, "resultado"
            tipo = "error" if e.tipo == "error" else tipo_unario(n.op, e.tipo)
            if tipo is None:
                self.error("E-SEM-03", n, f"no se puede usar '{n.op}' con {e.tipo}")
                tipo = "error"
            if tipo != "error" and e.val is not None:
                val = -e.val if n.op == "neg" else (not e.val)
        elif isinstance(n, BinOp):
            self.expresion(n.izq)
            self.expresion(n.der)
            d = self.pila.pop("reducir")
            i = self.pila.pop("reducir")
            simbolo, accion = n.op, "resultado"
            if "error" in (i.tipo, d.tipo):
                tipo = "error"
            else:
                tipo = tipo_binario(n.op, i.tipo, d.tipo)
                if tipo is None:
                    self.error("E-SEM-03", n, f"no se puede usar '{n.op}' entre {i.tipo} y {d.tipo}")
                    tipo = "error"
            if tipo != "error" and i.val is not None and d.val is not None:
                val = plegar(n.op, i.val, d.val, i.tipo == d.tipo == "entero")
        else:                                   # Llamada
            simbolo, accion = n.nombre, "resultado"
            tipo = self.llamada(n)
        n.tipo, n.val = tipo, val
        self.pila.push(Elemento(simbolo, tipo, val, lugar, n.linea, n.col), accion)

    def var(self, n):
        """(tipo, val) de un identificador; val solo si es constante."""
        if n.nombre in self.alias:
            return "zona", None
        s = self.tabla.buscar(n.nombre)
        if s is None:
            self.error("E-SEM-01", n, f"'{n.nombre}' no está declarado")
            return "error", None
        n.simbolo = s
        return s.tipo, (s.valor if s.categoria == "constante" else None)

    def campo(self, n):
        if self.zonas_de(n.objeto) is None:
            if self.tabla.buscar(n.objeto) is None:
                self.error("E-SEM-01", n, f"'{n.objeto}' no está declarado")
            else:
                self.error("E-SEM-03", n, f"'{n.objeto}' no es una zona")
            return "error"
        if n.campo not in CAMPOS_LECTURA:
            self.error("E-SEM-01", n, f"la zona no tiene el campo '{n.campo}'")
            return "error"
        return CAMPOS_LECTURA[n.campo]

    def llamada(self, n):
        for a in n.args:
            self.expresion(a)
        datos = [self.pila.pop("reducir") for _ in n.args][::-1]
        if n.nombre not in FUNCIONES:
            self.error("E-SEM-04", n, f"la función '{n.nombre}' no está definida")
            return "error"
        retorno = FUNCIONES[n.nombre][1] or "vacio"
        tipos = [d.tipo for d in datos]
        if "error" in tipos:                    # ya se reportó dentro del argumento
            return retorno
        problema = comprobar_argumentos(n.nombre, tipos)
        if problema:
            self.error("E-SEM-05", n, problema)
        elif n.nombre == "leer" and datos[0].val is not None and datos[0].val not in SENSORES:
            self.error("E-DOM-01", datos[0], f"sensor desconocido '{datos[0].val}'")      # V1
        elif n.nombre == "regar" and datos[1].val is not None:                            # V2
            for z in self.zonas_de(n.args[0].nombre):
                riego = z.valor.get("riego_max")
                if riego is not None and datos[1].val > riego:
                    self.error("E-DOM-02", n, f"regar {datos[1].val} min a '{z.nombre}' "
                                              f"supera su riego_max ({riego})")
        return retorno


def analizar(ast, tabla, log):
    """Analiza el programa. Devuelve la pila semántica (su traza se muestra con --pila)."""
    a = Analizador(tabla, log)
    a.sentencia(ast)
    return a.pila