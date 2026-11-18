"""
Análisis semántico de MILPA.

Recorre el AST una sola vez, en orden, y hace tres cosas:
  1. Llena la tabla de símbolos y de direcciones (con ámbitos).
  2. Calcula el tipo de cada expresión y su valor constante cuando se conoce
     al compilar. Se guarda en el nodo como nodo.tipo_sem, nodo.val_const y
     nodo.magnitud (los necesita el generador de código).
  3. Registra TODOS los errores que encuentra (no se detiene en el primero).

Reglas principales (documento de definición, secciones 2 y 4):
  - entero -> decimal es una conversión implícita; decimal -> entero solo con a_entero(x).
  - La división entre enteros es entera (se trunca hacia cero).
  - No se puede ocultar una variable de un ámbito exterior ni redeclarar un nombre.
  - Un nodo con tipo 'error' no genera más errores encima (evita cascadas).

Códigos de error:
  E-SEM-01 variable no declarada        E-SEM-06 asignación a constante
  E-SEM-02 nombre ya declarado          E-SEM-07 condición no booleana
  E-SEM-03 tipos incompatibles          E-SEM-08 zona o campo de zona inválido
  E-SEM-04 función no definida          E-SEM-09 división entre cero
  E-SEM-05 argumentos incorrectos       E-SEM-10 se necesita un valor constante
  E-DOM-01 sensor desconocido           E-DOM-02 riego fuera de lo permitido
  E-DOM-03 humedad fuera de 0 a 100
"""

from src.symtab import Simbolo, TablaSimbolos

from src.frontend.ast_nodes import (
    Programa,
    DeclaracionVariable,
    DeclaracionConstante,
    DeclaracionZona,
    Asignacion,
    Condicional,
    CicloMientras,
    CicloParaCada,
    LlamadaFuncion,
    OperacionBinaria,
    OperacionUnaria,
    Literal,
    Identificador,
    AccesoCampo,
)

NUM = ("entero", "decimal")
SENSORES = ("humedad", "temperatura")
RIEGO_MAX_POR_DEFECTO = 30          # minutos, si la zona no declara riego_max
TIPOS_DECLARABLES = ("entero", "decimal", "texto", "booleano")

# Campos de una zona y su tipo. 'nombre' se genera solo y es de solo lectura.
CAMPOS_ZONA = {
    "cultivo": "texto",
    "humedad_min": "decimal",
    "riego_max": "entero",
    "fila": "entero",          # opcional: parcela del huerto (empieza en 1)
    "columna": "entero",       # opcional: va junto con 'fila'
    "nombre": "texto",
}

# Funciones predefinidas: parámetros, si aceptan cualquier cantidad y qué devuelven.
FUNCIONES = {
    "leer":      {"params": ["zona", "texto"],   "variadica": False, "retorno": "decimal"},
    "lloviendo": {"params": [],                  "variadica": False, "retorno": "booleano"},
    "regar":     {"params": ["zona", "entero"],  "variadica": False, "retorno": "vacio"},
    "registrar": {"params": None,                "variadica": True,  "retorno": "vacio"},
    "a_entero":  {"params": ["decimal"],         "variadica": False, "retorno": "entero"},
}

# 'y', 'o' y 'no' son operadores lógicos y no se pueden usar como nombres.
NOMBRES_RESERVADOS = {"y", "o", "no"}


def compatible(destino, origen):
    """True si un valor de tipo `origen` se puede guardar en un `destino`."""
    return destino == origen or (destino == "decimal" and origen == "entero")


def _posicion(n):
    """Posición donde empieza una expresión (la del operando más a la izquierda)."""
    while isinstance(n, OperacionBinaria):
        n = n.izquierda
    return (getattr(n, "linea", 0), getattr(n, "columna", 0))


def _division_entera(a, b):
    """División entera que trunca hacia cero, como la instrucción div de MIPS."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _resto(a, b):
    return a - b * _division_entera(a, b)


class AnalizadorSemantico:

    TIPOS = {"entero", "decimal", "texto", "booleano", "zona"}
    FUNCIONES = FUNCIONES

    def __init__(self, errores=None):
        self.tabla = TablaSimbolos()
        self.errores = errores
        self.zonas = {}          # nombre de zona -> dict con sus campos
        self.posiciones = {}     # (fila, columna) -> zona que ocupa esa parcela

    # ------------------------------------------------------------ errores
    def registrar_error(self, codigo, mensaje, nodo):
        """Registra un error. `nodo` puede ser un nodo del AST o una tupla (línea, columna)."""
        if isinstance(nodo, tuple):
            linea, columna = nodo
        else:
            linea = getattr(nodo, "linea", 0)
            columna = getattr(nodo, "columna", 0)

        fase = "Dominio" if codigo.startswith("E-DOM") else "Semantico"

        if self.errores is not None:
            self.errores.agregar(fase, codigo, linea, columna, mensaje)
        else:
            print(f"[{codigo}] Línea {linea}, columna {columna}: {mensaje}")

    # ------------------------------------------------------------ entrada
    def analizar(self, arbol):
        """Analiza el programa. Devuelve True si no hubo errores nuevos."""
        if not isinstance(arbol, Programa):
            self.registrar_error(
                "E-SEM-01", "El árbol recibido no es un programa válido.", arbol
            )
            return False

        antes = len(self.errores.obtener_errores()) if self.errores is not None else 0
        self.analizar_instrucciones(arbol.instrucciones)
        if self.errores is not None:
            return len(self.errores.obtener_errores()) == antes
        return True

    def analizar_instrucciones(self, instrucciones):
        for instruccion in instrucciones:
            self.analizar_nodo(instruccion)

    def analizar_nodo(self, nodo):
        if isinstance(nodo, DeclaracionVariable):
            self.declarar_variable(nodo, "variable")
        elif isinstance(nodo, DeclaracionConstante):
            self.declarar_variable(nodo, "constante")
        elif isinstance(nodo, DeclaracionZona):
            self.declarar_zona(nodo)
        elif isinstance(nodo, Asignacion):
            self.analizar_asignacion(nodo)
        elif isinstance(nodo, Condicional):
            self.analizar_condicional(nodo)
        elif isinstance(nodo, CicloMientras):
            self.analizar_mientras(nodo)
        elif isinstance(nodo, CicloParaCada):
            self.analizar_para_cada(nodo)
        elif isinstance(nodo, LlamadaFuncion):
            self.analizar_llamada(nodo)

    def analizar_bloque(self, instrucciones, preparar=None):
        self.tabla.entrar_ambito()
        if preparar:
            preparar()
        self.analizar_instrucciones(instrucciones)
        self.tabla.salir_ambito()

    # ------------------------------------------------------ declaraciones
    def nombre_libre(self, nombre, nodo):
        """True si el nombre se puede declarar; si no, registra E-SEM-02."""
        if nombre in FUNCIONES:
            self.registrar_error(
                "E-SEM-02", f"'{nombre}' es el nombre de una función predefinida.", nodo
            )
            return False
        if nombre in NOMBRES_RESERVADOS:
            self.registrar_error(
                "E-SEM-02", f"'{nombre}' es una palabra reservada y no se puede usar como nombre.", nodo
            )
            return False
        if self.tabla.existe(nombre):
            donde = "en este ámbito" if self.tabla.existe_en_actual(nombre) else "en un ámbito exterior"
            self.registrar_error("E-SEM-02", f"'{nombre}' ya está declarado {donde}.", nodo)
            return False
        return True

    def comprobar_valor_inicial(self, nodo, que):
        """Evalúa el valor de una declaración y comprueba que su tipo sea compatible."""
        tipo = self.expresion(nodo.valor)
        if tipo == "error":
            return False
        if nodo.tipo not in TIPOS_DECLARABLES:
            self.registrar_error("E-SEM-03", f"Tipo desconocido '{nodo.tipo}'.", nodo)
            return False
        if tipo == "vacio":
            self.registrar_error(
                "E-SEM-03", f"La expresión no devuelve ningún valor para {que} '{nodo.nombre}'.",
                _posicion(nodo.valor),
            )
            return False
        if not compatible(nodo.tipo, tipo):
            mensaje = f"No se puede asignar un valor {tipo} a {que} {nodo.tipo} '{nodo.nombre}'."
            if nodo.tipo == "entero" and tipo == "decimal":
                mensaje += " Usa a_entero(...) para convertirlo."
            self.registrar_error("E-SEM-03", mensaje, _posicion(nodo.valor))
            return False
        return True

    def declarar_variable(self, nodo, categoria):
        que = "la constante" if categoria == "constante" else "la variable"
        # Primero el valor: 'entero a = a + 1' debe fallar porque 'a' aún no existe.
        correcto = self.comprobar_valor_inicial(nodo, que)
        libre = self.nombre_libre(nodo.nombre, nodo)

        valor = None
        if categoria == "constante" and correcto:
            constante = getattr(nodo.valor, "val_const", None)
            if constante is None:
                self.registrar_error(
                    "E-SEM-10",
                    f"La constante '{nodo.nombre}' necesita un valor conocido al compilar.",
                    _posicion(nodo.valor),
                )
            else:
                valor = float(constante) if nodo.tipo == "decimal" else constante

        if libre:
            self.tabla.declarar(Simbolo(
                nombre=nodo.nombre,
                tipo=nodo.tipo,
                categoria=categoria,
                valor=valor,
                linea=nodo.linea,
                columna=nodo.columna,
                inicializada=True,
                magnitud=getattr(nodo.valor, "magnitud", None),
            ))

    def declarar_zona(self, nodo):
        if self.tabla.nivel != 0:
            self.registrar_error(
                "E-SEM-08", "Las zonas solo se pueden declarar en el ámbito global.", nodo
            )
        libre = self.nombre_libre(nodo.nombre, nodo)

        datos, vistos = {}, set()
        for campo in nodo.campos:
            posicion = (campo.linea, campo.columna)
            if campo.nombre == "nombre":
                self.registrar_error(
                    "E-SEM-08", "El campo 'nombre' se genera automáticamente.", posicion
                )
                continue
            if campo.nombre not in CAMPOS_ZONA:
                self.registrar_error(
                    "E-SEM-08",
                    f"Campo de zona desconocido '{campo.nombre}' "
                    "(válidos: cultivo, humedad_min, riego_max, fila, columna).",
                    posicion,
                )
                continue
            if campo.nombre in vistos:
                self.registrar_error(
                    "E-SEM-08", f"El campo '{campo.nombre}' está repetido.", posicion
                )
                continue
            vistos.add(campo.nombre)

            esperado = CAMPOS_ZONA[campo.nombre]
            tipo = self.expresion(campo.valor)
            if tipo == "error":
                continue
            if not compatible(esperado, tipo):
                self.registrar_error(
                    "E-SEM-03",
                    f"El campo '{campo.nombre}' debe ser {esperado}, no {tipo}.",
                    _posicion(campo.valor),
                )
                continue
            constante = getattr(campo.valor, "val_const", None)
            if constante is None:
                self.registrar_error(
                    "E-SEM-10",
                    f"El campo '{campo.nombre}' necesita un valor conocido al compilar.",
                    _posicion(campo.valor),
                )
                continue

            valor = float(constante) if esperado == "decimal" else constante
            if campo.nombre == "humedad_min" and not (0 <= valor <= 100):
                self.registrar_error(
                    "E-DOM-03",
                    f"humedad_min = {valor} está fuera del rango válido (0 a 100).",
                    _posicion(campo.valor),
                )
            if campo.nombre == "riego_max" and valor <= 0:
                self.registrar_error(
                    "E-DOM-02", "riego_max debe ser mayor que 0.", _posicion(campo.valor)
                )
            if campo.nombre in ("fila", "columna") and valor < 1:
                self.registrar_error(
                    "E-SEM-08", f"'{campo.nombre}' debe ser 1 o mayor (es {valor}).",
                    _posicion(campo.valor),
                )
                continue
            datos[campo.nombre] = valor

        for obligatorio in ("cultivo", "humedad_min"):
            if obligatorio not in vistos:
                self.registrar_error(
                    "E-SEM-08",
                    f"A la zona '{nodo.nombre}' le falta el campo '{obligatorio}'.",
                    nodo,
                )

        if ("fila" in vistos) != ("columna" in vistos):
            self.registrar_error(
                "E-SEM-08",
                f"La zona '{nodo.nombre}' debe indicar 'fila' y 'columna' juntas.",
                nodo,
            )
        elif "fila" in datos and "columna" in datos:
            posicion = (datos["fila"], datos["columna"])
            if posicion in self.posiciones:
                self.registrar_error(
                    "E-SEM-08",
                    f"La parcela {posicion[0]}:{posicion[1]} ya está ocupada por la zona "
                    f"'{self.posiciones[posicion]}'.",
                    nodo,
                )
            else:
                self.posiciones[posicion] = nodo.nombre

        campos = {
            "cultivo": datos.get("cultivo", ""),
            "humedad_min": datos.get("humedad_min", 0.0),
            "riego_max": datos.get("riego_max", RIEGO_MAX_POR_DEFECTO),
            "fila": datos.get("fila", 0),
            "columna": datos.get("columna", 0),
            "nombre": nodo.nombre,
        }
        if libre:
            self.tabla.declarar(Simbolo(
                nombre=nodo.nombre,
                tipo="zona",
                categoria="zona",
                valor=campos,
                linea=nodo.linea,
                columna=nodo.columna,
                inicializada=True,
            ))
            self.zonas[nodo.nombre] = campos

    # -------------------------------------------------------- sentencias
    def analizar_asignacion(self, nodo):
        tipo = self.expresion(nodo.valor)
        simbolo = self.tabla.buscar(nodo.nombre)

        if simbolo is None:
            self.registrar_error(
                "E-SEM-01", f"La variable '{nodo.nombre}' no está declarada.", nodo
            )
            return
        if simbolo.categoria == "constante":
            self.registrar_error(
                "E-SEM-06", f"'{nodo.nombre}' es una constante y no se puede modificar.", nodo
            )
            return
        if simbolo.categoria in ("zona", "alias"):
            self.registrar_error(
                "E-SEM-03", f"'{nodo.nombre}' es una zona y no se le puede asignar un valor.", nodo
            )
            return
        if tipo == "error":
            return
        if tipo == "vacio":
            self.registrar_error(
                "E-SEM-03", f"La expresión no devuelve ningún valor para '{nodo.nombre}'.",
                _posicion(nodo.valor),
            )
            return
        if not compatible(simbolo.tipo, tipo):
            mensaje = f"No se puede asignar un valor {tipo} a la variable {simbolo.tipo} '{nodo.nombre}'."
            if simbolo.tipo == "entero" and tipo == "decimal":
                mensaje += " Usa a_entero(...) para convertirlo."
            self.registrar_error("E-SEM-03", mensaje, _posicion(nodo.valor))

    def comprobar_condicion(self, condicion):
        tipo = self.expresion(condicion)
        if tipo not in ("booleano", "error"):
            self.registrar_error(
                "E-SEM-07", f"La condición debe ser booleana, pero es {tipo}.",
                _posicion(condicion),
            )

    def analizar_condicional(self, nodo):
        self.comprobar_condicion(nodo.condicion)
        self.analizar_bloque(nodo.bloque_si)
        if nodo.bloque_si_no:
            self.analizar_bloque(nodo.bloque_si_no)

    def analizar_mientras(self, nodo):
        self.comprobar_condicion(nodo.condicion)
        self.analizar_bloque(nodo.instrucciones)

    def analizar_para_cada(self, nodo):
        validas = []
        for nombre in nodo.zonas:
            simbolo = self.tabla.buscar(nombre)
            if simbolo is None:
                self.registrar_error("E-SEM-01", f"La zona '{nombre}' no está declarada.", nodo)
            elif simbolo.categoria != "zona":
                self.registrar_error("E-SEM-03", f"'{nombre}' no es una zona.", nodo)
            else:
                validas.append(nombre)

        def preparar():
            if self.nombre_libre(nodo.variable, nodo):
                self.tabla.declarar(Simbolo(
                    nombre=nodo.variable,
                    tipo="zona",
                    categoria="alias",
                    valor=validas,
                    linea=nodo.linea,
                    columna=nodo.columna,
                    inicializada=True,
                ))

        self.analizar_bloque(nodo.instrucciones, preparar)

    def analizar_llamada(self, nodo):
        self.expresion(nodo)

    # ------------------------------------------------------- expresiones
    def expresion(self, nodo):
        """Calcula el tipo de una expresión y lo guarda (con su valor constante) en el nodo."""
        nodo.tipo_sem = "error"
        nodo.val_const = None
        nodo.magnitud = None

        if isinstance(nodo, Literal):
            nodo.tipo_sem, nodo.val_const = nodo.tipo, nodo.valor
        elif isinstance(nodo, Identificador):
            self.expr_identificador(nodo)
        elif isinstance(nodo, AccesoCampo):
            self.expr_campo(nodo)
        elif isinstance(nodo, LlamadaFuncion):
            self.expr_llamada(nodo)
        elif isinstance(nodo, OperacionUnaria):
            self.expr_unaria(nodo)
        elif isinstance(nodo, OperacionBinaria):
            self.expr_binaria(nodo)
        return nodo.tipo_sem

    def expr_identificador(self, nodo):
        simbolo = self.tabla.buscar(nodo.nombre)
        if simbolo is None:
            self.registrar_error(
                "E-SEM-01", f"La variable '{nodo.nombre}' no está declarada.", nodo
            )
            return
        nodo.tipo_sem = simbolo.tipo
        if simbolo.categoria == "constante":
            nodo.val_const = simbolo.valor
        nodo.magnitud = simbolo.magnitud

    def expr_campo(self, nodo):
        simbolo = self.tabla.buscar(nodo.zona)
        if simbolo is None:
            self.registrar_error("E-SEM-01", f"La zona '{nodo.zona}' no está declarada.", nodo)
            return
        if simbolo.categoria not in ("zona", "alias"):
            self.registrar_error(
                "E-SEM-03", f"'{nodo.zona}' no es una zona y no tiene campos.", nodo
            )
            return
        if nodo.campo not in CAMPOS_ZONA:
            self.registrar_error(
                "E-SEM-08", f"La zona no tiene el campo '{nodo.campo}'.", nodo
            )
            return
        nodo.tipo_sem = CAMPOS_ZONA[nodo.campo]
        if simbolo.categoria == "zona":
            nodo.val_const = simbolo.valor[nodo.campo]
        if nodo.campo == "humedad_min":
            nodo.magnitud = "humedad"

    def expr_llamada(self, nodo):
        tipos = [self.expresion(a) for a in nodo.argumentos]
        especificacion = FUNCIONES.get(nodo.nombre)
        if especificacion is None:
            self.registrar_error(
                "E-SEM-04", f"La función '{nodo.nombre}' no está definida.", nodo
            )
            return
        nodo.tipo_sem = especificacion["retorno"]

        if especificacion["variadica"]:
            if not nodo.argumentos:
                self.registrar_error(
                    "E-SEM-05", f"'{nodo.nombre}' necesita al menos un argumento.", nodo
                )
            for i, tipo in enumerate(tipos):
                if tipo in ("zona", "vacio"):
                    self.registrar_error(
                        "E-SEM-05",
                        f"El argumento {i + 1} de '{nodo.nombre}' no se puede imprimir ({tipo}).",
                        _posicion(nodo.argumentos[i]),
                    )
            return

        parametros = especificacion["params"]
        if len(tipos) != len(parametros):
            self.registrar_error(
                "E-SEM-05",
                f"'{nodo.nombre}' espera {len(parametros)} argumento(s) "
                f"pero recibió {len(tipos)}.",
                nodo,
            )
            return

        correcto = "error" not in tipos
        for i, (tipo, esperado) in enumerate(zip(tipos, parametros)):
            if tipo != "error" and not compatible(esperado, tipo):
                self.registrar_error(
                    "E-SEM-05",
                    f"El argumento {i + 1} de '{nodo.nombre}' debe ser {esperado}, no {tipo}.",
                    _posicion(nodo.argumentos[i]),
                )
                correcto = False
        if not correcto:
            return

        if nodo.nombre == "leer":
            self.validar_sensor(nodo)
        elif nodo.nombre == "regar":
            self.validar_riego(nodo)

    def validar_sensor(self, nodo):
        """V1: el sensor debe ser conocido y escrito como un texto fijo."""
        sensor = nodo.argumentos[1]
        if sensor.val_const is None:
            self.registrar_error(
                "E-DOM-01", "El sensor debe ser un texto conocido al compilar.",
                _posicion(sensor),
            )
        elif sensor.val_const not in SENSORES:
            self.registrar_error(
                "E-DOM-01",
                f"Sensor desconocido '{sensor.val_const}' (válidos: humedad, temperatura).",
                _posicion(sensor),
            )
        else:
            nodo.magnitud = sensor.val_const

    def validar_riego(self, nodo):
        """V2: la duración no puede ser negativa, cero ni mayor que riego_max de la zona."""
        zona, duracion = nodo.argumentos
        if duracion.val_const is None:
            return          # duración variable: no se puede comprobar al compilar
        if duracion.val_const <= 0:
            self.registrar_error(
                "E-DOM-02",
                f"La duración de riego debe ser positiva (es {duracion.val_const}).",
                _posicion(duracion),
            )
            return
        if not isinstance(zona, Identificador):
            return
        simbolo = self.tabla.buscar(zona.nombre)
        if simbolo is None:
            return
        zonas = [simbolo] if simbolo.categoria == "zona" else [
            self.tabla.buscar(n) for n in simbolo.valor
        ]
        for z in zonas:
            maximo = z.valor["riego_max"]
            if duracion.val_const > maximo:
                self.registrar_error(
                    "E-DOM-02",
                    f"La duración {duracion.val_const} excede riego_max ({maximo}) "
                    f"de la zona '{z.nombre}'.",
                    _posicion(duracion),
                )

    def expr_unaria(self, nodo):
        tipo = self.expresion(nodo.operando)
        if tipo == "error":
            return
        valor = nodo.operando.val_const
        if nodo.operador == "-":
            if tipo in NUM:
                nodo.tipo_sem = tipo
                if valor is not None:
                    nodo.val_const = -valor
                return
            self.registrar_error("E-SEM-03", f"No se puede negar un valor {tipo}.", nodo)
        else:  # no
            if tipo == "booleano":
                nodo.tipo_sem = "booleano"
                if valor is not None:
                    nodo.val_const = not valor
                return
            self.registrar_error(
                "E-SEM-03", f"'no' necesita un booleano, pero recibió {tipo}.", nodo
            )

    def expr_binaria(self, nodo):
        izq = self.expresion(nodo.izquierda)
        der = self.expresion(nodo.derecha)
        if "error" in (izq, der):
            return
        op = nodo.operador
        a, b = nodo.izquierda.val_const, nodo.derecha.val_const
        conocidos = a is not None and b is not None

        if op in ("+", "-", "*", "/", "%"):
            if izq in NUM and der in NUM:
                if op == "%" and not (izq == "entero" and der == "entero"):
                    self.registrar_error(
                        "E-SEM-03", "El operador '%' solo se aplica entre enteros.", nodo
                    )
                    return
                nodo.tipo_sem = "decimal" if "decimal" in (izq, der) else "entero"
                if conocidos:
                    if op in ("/", "%") and b == 0:
                        self.registrar_error(
                            "E-SEM-09", "División entre cero.", _posicion(nodo.derecha)
                        )
                    else:
                        nodo.val_const = self.plegar(op, a, b, nodo.tipo_sem)
                return
        elif op in ("<", "<=", ">", ">="):
            if izq in NUM and der in NUM:
                nodo.tipo_sem = "booleano"
                self.validar_rango_humedad(nodo)
                if conocidos:
                    nodo.val_const = {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
                return
        elif op in ("==", "!="):
            if (izq in NUM and der in NUM) or (izq == der == "booleano"):
                nodo.tipo_sem = "booleano"
                self.validar_rango_humedad(nodo)
                if conocidos:
                    nodo.val_const = (a == b) if op == "==" else (a != b)
                return
        elif op in ("y", "o"):
            if izq == der == "booleano":
                nodo.tipo_sem = "booleano"
                if conocidos:
                    nodo.val_const = (a and b) if op == "y" else (a or b)
                return

        self.registrar_error(
            "E-SEM-03", f"El operador '{op}' no se puede aplicar a {izq} y {der}.", nodo
        )

    @staticmethod
    def plegar(op, a, b, tipo):
        """Calcula una operación entre constantes (plegado de constantes)."""
        if tipo == "entero":
            return {
                "+": a + b, "-": a - b, "*": a * b,
                "/": _division_entera(a, b) if b else None,
                "%": _resto(a, b) if b else None,
            }[op]
        a, b = float(a), float(b)
        return {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else None}[op]

    def validar_rango_humedad(self, nodo):
        """V3: comparar una lectura de humedad con una constante fuera de 0 a 100."""
        for lado, otro in ((nodo.izquierda, nodo.derecha), (nodo.derecha, nodo.izquierda)):
            if (
                lado.magnitud == "humedad"
                and otro.val_const is not None
                and not (0 <= otro.val_const <= 100)
            ):
                self.registrar_error(
                    "E-DOM-03",
                    f"Se compara la humedad con {otro.val_const}, "
                    "fuera del rango válido (0 a 100).",
                    _posicion(otro),
                )
