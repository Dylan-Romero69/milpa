
from src.symtab import Simbolo, TablaSimbolos

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
    AccesoCampo,
)


class AnalizadorSemantico:

    TIPOS = {
        "entero",
        "decimal",
        "texto",
        "booleano",
        "zona",
    }

    FUNCIONES = {
        "leer": (0, 0),
        "lloviendo": (0, 0),
        "regar": (1, 1),
        "registrar": (1, 1),
        "a_entero": (1, 1),
    }

    OPERADORES_LOGICOS = {"y", "o"}
    OPERADORES_RELACIONALES = {
        "==", "!=", "<", ">", "<=", ">="
    }

    def __init__(self, errores=None):
        self.tabla = TablaSimbolos()
        self.errores = errores
        self.zonas = {}

    
    def registrar_error(self, codigo, mensaje, nodo):
        """Registra un error semántico."""
        linea = getattr(nodo, "linea", 0)
        columna = getattr(nodo, "columna", 0)

        if self.errores is not None:
            self.errores.agregar(
                "Semantico",
                codigo,
                linea,
                columna,
                mensaje
            )
        else:
            print(
                f"[{codigo}] Línea {linea}, "
                f"columna {columna}: {mensaje}"
            )


 
    def analizar(self, arbol):
        """Inicia el análisis semántico."""
        if not isinstance(arbol, Programa):
            self.registrar_error(
                "E-SEM-01",
                "El árbol recibido no es un programa válido.",
                arbol
            )
            return False

        errores_iniciales = (
            len(self.errores.obtener_errores())
            if self.errores is not None else 0
        )

        self.analizar_instrucciones(arbol.instrucciones)

        if self.errores is not None:
            errores_finales = len(self.errores.obtener_errores())
            return errores_finales == errores_iniciales

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

    def declarar_variable(self, nodo, categoria):
        if nodo.tipo not in self.TIPOS - {"zona"}:
            self.registrar_error(
                "E-SEM-02",
                f"Tipo de dato no válido: {nodo.tipo}.",
                nodo
            )
            return

        if self.tabla.existe(nodo.nombre):
            self.registrar_error(
                "E-SEM-01",
                f"El identificador '{nodo.nombre}' ya fue declarado.",
                nodo
            )
            return

        tipo_valor = self.obtener_tipo(nodo.valor)

        if tipo_valor is not None and not self.tipos_compatibles(
            nodo.tipo, tipo_valor
        ):
            self.registrar_error(
                "E-SEM-03",
                f"No se puede asignar '{tipo_valor}' a '{nodo.tipo}'.",
                nodo
            )
            return

        simbolo = Simbolo(
            nombre=nodo.nombre,
            tipo=nodo.tipo,
            categoria=categoria,
            valor=nodo.valor
        )

        self.tabla.declarar(simbolo)

        self.analizar_expresion(nodo.valor)

    def declarar_zona(self, nodo):
        if self.tabla.existe(nodo.nombre):
            self.registrar_error(
                "E-SEM-01",
                f"El identificador '{nodo.nombre}' ya fue declarado.",
                nodo
            )
            return

        campos = {}

        for campo in nodo.campos:
            if not isinstance(campo, CampoZona):
                continue

            if campo.nombre in campos:
                self.registrar_error(
                    "E-SEM-01",
                    f"Campo duplicado '{campo.nombre}' en zona.",
                    campo
                )
                continue

            campos[campo.nombre] = campo.valor

        requeridos = {
            "cultivo",
            "humedad_min",
            "riego_max"
        }

        for campo in requeridos:
            if campo not in campos:
                self.registrar_error(
                    "E-SEM-04",
                    f"Falta el campo '{campo}' en la zona.",
                    nodo
                )

        simbolo = Simbolo(
            nombre=nodo.nombre,
            tipo="zona",
            categoria="zona",
            valor=campos
        )

        self.tabla.declarar(simbolo)
        self.zonas[nodo.nombre] = campos

    def analizar_asignacion(self, nodo):
        simbolo = self.tabla.buscar(nodo.nombre)

        if simbolo is None:
            self.registrar_error(
                "E-SEM-05",
                f"La variable '{nodo.nombre}' no está declarada.",
                nodo
            )
            self.analizar_expresion(nodo.valor)
            return

        if simbolo.categoria == "constante":
            self.registrar_error(
                "E-SEM-06",
                f"No se puede modificar la constante '{nodo.nombre}'.",
                nodo
            )
            return

        tipo_valor = self.obtener_tipo(nodo.valor)

        if tipo_valor is not None and not self.tipos_compatibles(
            simbolo.tipo, tipo_valor
        ):
            self.registrar_error(
                "E-SEM-03",
                f"No se puede asignar '{tipo_valor}' a '{simbolo.tipo}'.",
                nodo
            )

        self.analizar_expresion(nodo.valor)

    def analizar_condicional(self, nodo):
        tipo = self.obtener_tipo(nodo.condicion)

        if tipo is not None and tipo != "booleano":
            self.registrar_error(
                "E-SEM-07",
                "La condición de 'si' debe ser booleana.",
                nodo
            )

        self.analizar_expresion(nodo.condicion)
        self.analizar_instrucciones(nodo.bloque_si)
        self.analizar_instrucciones(nodo.bloque_si_no)

    def analizar_mientras(self, nodo):
        tipo = self.obtener_tipo(nodo.condicion)

        if tipo is not None and tipo != "booleano":
            self.registrar_error(
                "E-SEM-07",
                "La condición de 'mientras' debe ser booleana.",
                nodo
            )

        self.analizar_expresion(nodo.condicion)
        self.analizar_instrucciones(nodo.instrucciones)

    def analizar_para_cada(self, nodo):
        if nodo.tipo != "zona":
            self.registrar_error(
                "E-SEM-02",
                "El ciclo para_cada debe utilizar el tipo zona.",
                nodo
            )

        for nombre_zona in nodo.zonas:
            if nombre_zona not in self.zonas:
                self.registrar_error(
                    "E-SEM-05",
                    f"La zona '{nombre_zona}' no está declarada.",
                    nodo
                )

        self.tabla.entrar_ambito()

        simbolo = Simbolo(
            nombre=nodo.variable,
            tipo="zona",
            categoria="variable"
        )

        if not self.tabla.declarar(simbolo):
            self.registrar_error(
                "E-SEM-01",
                f"El identificador '{nodo.variable}' ya fue declarado.",
                nodo
            )

        self.analizar_instrucciones(nodo.instrucciones)
        self.tabla.salir_ambito()

    def analizar_llamada(self, nodo):
        if nodo.nombre not in self.FUNCIONES:
            self.registrar_error(
                "E-SEM-08",
                f"Función '{nodo.nombre}' no reconocida.",
                nodo
            )
            return

        minimo, maximo = self.FUNCIONES[nodo.nombre]
        cantidad = len(nodo.argumentos)

        if cantidad < minimo or cantidad > maximo:
            self.registrar_error(
                "E-SEM-08",
                f"La función '{nodo.nombre}' recibió "
                f"{cantidad} argumentos.",
                nodo
            )

        for argumento in nodo.argumentos:
            self.analizar_expresion(argumento)

    def analizar_expresion(self, nodo):
        if nodo is None:
            return

        if isinstance(nodo, Identificador):
            if self.tabla.buscar(nodo.nombre) is None:
                self.registrar_error(
                    "E-SEM-05",
                    f"La variable '{nodo.nombre}' no está declarada.",
                    nodo
                )

        elif isinstance(nodo, AccesoCampo):
            simbolo = self.tabla.buscar(nodo.zona)

            if simbolo is None or simbolo.tipo != "zona":
                self.registrar_error(
                    "E-SEM-05",
                    f"La zona '{nodo.zona}' no está declarada.",
                    nodo
                )
            else:
                campos = simbolo.valor or {}

                if nodo.campo not in campos:
                    self.registrar_error(
                        "E-SEM-04",
                        f"Campo '{nodo.campo}' no existe en la zona.",
                        nodo
                    )

        elif isinstance(nodo, OperacionBinaria):
            self.analizar_expresion(nodo.izquierda)
            self.analizar_expresion(nodo.derecha)

        elif isinstance(nodo, OperacionUnaria):
            self.analizar_expresion(nodo.operando)

        elif isinstance(nodo, LlamadaFuncion):
            self.analizar_llamada(nodo)

    def obtener_tipo(self, nodo):
        if nodo is None:
            return None

        if isinstance(nodo, Literal):
            return nodo.tipo

        if isinstance(nodo, Identificador):
            simbolo = self.tabla.buscar(nodo.nombre)
            return simbolo.tipo if simbolo else None

        if isinstance(nodo, AccesoCampo):
            simbolo = self.tabla.buscar(nodo.zona)

            if simbolo is None:
                return None

            campos = simbolo.valor or {}
            valor = campos.get(nodo.campo)

            if nodo.campo == "cultivo":
                return "texto"

            if nodo.campo in {"humedad_min", "riego_max"}:
                return self.obtener_tipo(valor)

        if isinstance(nodo, OperacionUnaria):
            if nodo.operador == "no":
                return "booleano"

            return self.obtener_tipo(nodo.operando)

        if isinstance(nodo, OperacionBinaria):
            operador = nodo.operador

            if operador in self.OPERADORES_RELACIONALES:
                return "booleano"

            if operador in self.OPERADORES_LOGICOS:
                return "booleano"

            tipo_izq = self.obtener_tipo(nodo.izquierda)
            tipo_der = self.obtener_tipo(nodo.derecha)

            if tipo_izq == "decimal" or tipo_der == "decimal":
                return "decimal"

            if tipo_izq == tipo_der == "entero":
                return "entero"

        if isinstance(nodo, LlamadaFuncion):
            if nodo.nombre == "leer":
                return "texto"

            if nodo.nombre == "lloviendo":
                return "booleano"

            if nodo.nombre == "a_entero":
                return "entero"

        return None

    def tipos_compatibles(self, destino, origen):
        if destino == origen:
            return True

        # Se permite convertir entero a decimal
        if destino == "decimal" and origen == "entero":
            return True

        return False
