"""
Generación de código MIPS32 para MARS 4.5 a partir de los cuádruplos.

Representación de los datos (todo valor ocupa una palabra de 32 bits):
  entero / booleano  entero con signo (booleano: 0 = falso, 1 = verdadero)
  decimal            flotante IEEE-754 de precisión simple; las operaciones
                     se hacen en el coprocesador 1 ($f4, $f6) y el resultado
                     vuelve a un registro entero con mfc1
  texto              dirección de una cadena .asciiz
  zona               dirección de un registro de 6 palabras en .data:
                       +0  nombre (texto)       +8   humedad_min (decimal)
                       +4  cultivo (texto)      +12  riego_max (entero)
                       +16 fila (entero)        +20  columna (entero)
                       (fila y columna valen 0 si la zona no las indica)

Registros:
  $t0-$t9  temporales asignados por AsignadorRegistros (linear scan)
  $k0,$k1  registros de trabajo del generador (MARS no instala un manejador
           de excepciones que los use)
  $fp      base de los temporales derramados a memoria (-4($fp), -8($fp)...)

Cada variable se declara en .data con un comentario de tipo, por ejemplo
"var_humedad: .word 0  # entero". El lector de .asm (src/mips_sim.py) usa
esos comentarios para reconstruir el huerto.
"""

import re
import struct

from src.regalloc import AsignadorRegistros


ARITMETICOS = {"+", "-", "*", "/", "%"}
RELACIONALES = {"<", ">", "<=", ">=", "==", "!="}
LOGICOS = {"y", "o"}

CAMPOS_ZONA = ("nombre", "cultivo", "humedad_min", "riego_max", "fila", "columna")
DESPLAZAMIENTO_CAMPO = {campo: 4 * i for i, campo in enumerate(CAMPOS_ZONA)}
TIPO_CAMPO = {
    "nombre": "texto",
    "cultivo": "texto",
    "humedad_min": "decimal",
    "riego_max": "entero",
    "fila": "entero",
    "columna": "entero",
}
RIEGO_MAX_POR_DEFECTO = 30

RETORNO_FUNCIONES = {
    "leer": "decimal",
    "lloviendo": "booleano",
    "a_entero": "entero",
}

VERDADEROS = {"verdadero", "true"}
FALSOS = {"falso", "false"}


def bits_flotante(valor):
    """Patrón de bits IEEE-754 (precisión simple) de un número."""
    return struct.unpack(">I", struct.pack(">f", float(valor)))[0]


def nombre_seguro(nombre):
    """Convierte un nombre en una etiqueta MIPS válida (solo ASCII)."""
    return re.sub(r"[^A-Za-z0-9_]", lambda m: "_x{:02X}_".format(ord(m.group())), str(nombre))


def texto_de_literal(valor):
    """Quita las comillas y los escapes de un literal de texto."""
    contenido = valor[1:-1]
    return re.sub(r"\\(.)", r"\1", contenido)


def escapar_asciiz(texto):
    """Escapa un texto para .asciiz. MARS guarda un byte por carácter (Latin-1)."""
    seguro = "".join(ch if ord(ch) < 256 else "?" for ch in texto)
    return (
        seguro.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


class GeneradorMIPS:
    """Traduce cuádruplos de MILPA a código MIPS32 para MARS."""

    A = "$k0"
    B = "$k1"

    def __init__(self, cuadruplos, asignador=None, tipos=None):
        self.cuadruplos = cuadruplos
        self.asignador = asignador or AsignadorRegistros(cuadruplos)
        self.tipos_declarados = dict(tipos or {})

        self.ubicaciones = {}
        self.tipos = {}
        self.variables = {}
        self.zonas = {}
        self.cadenas = {}
        self.iteradores = []
        self.cursor_de = {}
        self.destinos = set()
        self.codigo = []
        self.datos = []
        self.parametros = []
        self.contador_etiquetas = 0

        self.temporales_memoria = {}

    # =====================================================
    # CLASIFICACIÓN DE OPERANDOS
    # =====================================================

    def es_temporal(self, nombre):
        return bool(re.fullmatch(r"t\d+", str(nombre)))

    def es_numero(self, valor):
        try:
            float(valor)
            return True
        except (ValueError, TypeError):
            return False

    def es_cadena(self, valor):
        return (
            isinstance(valor, str)
            and len(valor) >= 2
            and valor[0] == '"'
            and valor[-1] == '"'
        )

    def es_booleano(self, valor):
        return str(valor).lower() in VERDADEROS | FALSOS

    def es_literal(self, valor):
        return self.es_numero(valor) or self.es_cadena(valor) or self.es_booleano(valor)

    def es_nombre(self, valor):
        """Variable o zona (ni literal, ni temporal, ni acceso a campo)."""
        return bool(valor) and not (
            self.es_literal(valor)
            or self.es_temporal(valor)
            or "." in valor
        )

    def tipo_operando(self, valor, tipos=None):
        tipos = self.tipos if tipos is None else tipos
        valor = str(valor)

        if self.es_cadena(valor):
            return "texto"
        if self.es_booleano(valor):
            return "booleano"
        if self.es_numero(valor):
            return "entero" if re.fullmatch(r"-?\d+", valor) else "decimal"
        if "." in valor:
            return TIPO_CAMPO.get(valor.split(".", 1)[1], "entero")
        if valor in self.zonas:
            return "zona"
        return tipos.get(valor, "")

    # =====================================================
    # PREPARACIÓN
    # =====================================================

    def inferir_tipos(self):
        """Completa los tipos que no vinieron del generador intermedio."""

        tipos = dict(self.tipos_declarados)

        for _ in range(10):
            cambio = False

            def fijar(nombre, tipo):
                nonlocal cambio
                if not nombre or not tipo or nombre in self.tipos_declarados:
                    return
                actual = tipos.get(nombre)
                if actual is None or (actual == "entero" and tipo == "decimal"):
                    if actual != tipo:
                        tipos[nombre] = tipo
                        cambio = True

            for c in self.cuadruplos:
                op = c.operador
                t1 = self.tipo_operando(c.argumento1, tipos)
                t2 = self.tipo_operando(c.argumento2, tipos)

                if op in ARITMETICOS:
                    fijar(c.resultado, "decimal" if "decimal" in (t1, t2) else "entero")
                elif op in RELACIONALES | LOGICOS or op == "UNARIO_no":
                    fijar(c.resultado, "booleano")
                elif op == "UNARIO_-":
                    fijar(c.resultado, t1 or "entero")
                elif op == "=":
                    fijar(c.resultado, t1)
                elif op == "CALL" and c.argumento1 in RETORNO_FUNCIONES:
                    fijar(c.resultado, RETORNO_FUNCIONES[c.argumento1])
                elif op == "ITER_INICIO":
                    fijar(c.argumento1, "zona")

            if not cambio:
                break

        return tipos

    def nueva_etiqueta(self, prefijo):
        self.contador_etiquetas += 1
        return f"{prefijo}_{self.contador_etiquetas}"

    def cadena(self, texto):
        """Etiqueta de una cadena en .data (se reutiliza si ya existe)."""
        if texto not in self.cadenas:
            self.cadenas[texto] = f"cad_{len(self.cadenas)}"
        return self.cadenas[texto]

    def destino_salto(self, c):
        return c.resultado.strip("()")

    def preparar(self):
        """Reúne zonas, variables, cadenas y destinos de salto."""

        self.ubicaciones = self.asignador.asignar()
        self.temporales_memoria = dict(self.asignador.derramas)

        self.zonas = {}
        self.variables = {}
        self.cadenas = {}
        self.iteradores = []
        self.cursor_de = {}
        self.destinos = set()
        self.contador_etiquetas = 0
        self.cadena("")

        # Zonas: se declaran con CAMPO y se recorren con ITER_INICIO.
        for c in self.cuadruplos:
            if c.operador == "CAMPO":
                zona = self.zonas.setdefault(c.argumento1, {})
                zona[c.argumento2] = c.resultado
            elif c.operador == "ITER_INICIO":
                for nombre in filter(None, c.argumento2.split(",")):
                    self.zonas.setdefault(nombre.strip(), {})

        self.tipos = self.inferir_tipos()

        for c in self.cuadruplos:
            op = c.operador

            if op in {"JUMP", "JUMP_IF_FALSE"}:
                self.destinos.add(self.destino_salto(c))

            if op in {"JUMP", "LABEL", "NOP", "RET"}:
                continue

            if op in {"CAMPO", "JUMP_IF_FALSE"}:
                candidatos = (c.resultado if op == "CAMPO" else c.argumento1,)
            elif op == "CALL":
                candidatos = (c.resultado,)
            elif op in {"ITER_INICIO", "ITER_SIGUIENTE"}:
                candidatos = (c.argumento1,)
            else:
                candidatos = (c.argumento1, c.argumento2, c.resultado)

            for valor in candidatos:
                if self.es_cadena(valor):
                    self.cadena(texto_de_literal(valor))
                elif "." in str(valor) and not self.es_numero(valor):
                    zona = valor.split(".", 1)[0]
                    if zona not in self.zonas:
                        self.variables.setdefault(zona, "zona")
                elif self.es_nombre(valor) and valor not in self.zonas:
                    self.variables.setdefault(valor, self.tipos.get(valor) or "entero")

        for texto in ("verdadero", "falso"):
            self.cadena(texto)

        return self

    # =====================================================
    # CARGA Y ALMACENAMIENTO
    # =====================================================

    def emitir(self, instruccion):
        self.codigo.append(f"    {instruccion}")

    def ubicacion_temporal(self, temporal):
        return self.ubicaciones.get(temporal)

    def cargar_operando(self, valor, registro):
        """Carga un operando en un registro y devuelve su tipo."""

        valor = str(valor)
        tipo = self.tipo_operando(valor)

        if valor == "":
            self.emitir(f"li {registro}, 0")

        elif self.es_cadena(valor):
            self.emitir(f"la {registro}, {self.cadena(texto_de_literal(valor))}")

        elif self.es_booleano(valor):
            self.emitir(f"li {registro}, {1 if valor.lower() in VERDADEROS else 0}")

        elif self.es_numero(valor):
            if tipo == "decimal":
                self.emitir(f"li {registro}, 0x{bits_flotante(valor):08X}    # {valor}")
            else:
                self.emitir(f"li {registro}, {int(valor)}")

        elif self.es_temporal(valor):
            ubicacion = self.ubicacion_temporal(valor)
            if ubicacion and ubicacion.startswith("$"):
                if ubicacion != registro:
                    self.emitir(f"move {registro}, {ubicacion}")
            elif ubicacion:
                self.emitir(f"lw {registro}, {ubicacion}")
            else:
                self.emitir(f"li {registro}, 0")

        elif "." in valor:
            zona, campo = valor.split(".", 1)
            desplazamiento = DESPLAZAMIENTO_CAMPO.get(campo, 0)
            if zona in self.zonas:
                self.emitir(f"lw {registro}, zona_{nombre_seguro(zona)}+{desplazamiento}")
            else:
                self.emitir(f"lw {registro}, var_{nombre_seguro(zona)}")
                self.emitir(f"lw {registro}, {desplazamiento}({registro})")

        elif valor in self.zonas:
            self.emitir(f"la {registro}, zona_{nombre_seguro(valor)}")

        else:
            self.emitir(f"lw {registro}, var_{nombre_seguro(valor)}")

        return tipo

    def guardar_resultado(self, destino, registro):
        """Guarda un registro en un temporal o una variable."""

        if not destino:
            return

        if self.es_temporal(destino):
            ubicacion = self.ubicacion_temporal(destino)
            if ubicacion and ubicacion.startswith("$"):
                if ubicacion != registro:
                    self.emitir(f"move {ubicacion}, {registro}")
            elif ubicacion:
                self.emitir(f"sw {registro}, {ubicacion}")
        else:
            self.emitir(f"sw {registro}, var_{nombre_seguro(destino)}")

    def a_decimal(self, registro):
        """Convierte un entero (en un registro) a flotante, en el mismo registro."""
        self.emitir(f"mtc1 {registro}, $f4")
        self.emitir("cvt.s.w $f4, $f4")
        self.emitir(f"mfc1 {registro}, $f4")

    def a_entero(self, registro):
        """Trunca un flotante (en un registro) a entero, en el mismo registro."""
        self.emitir(f"mtc1 {registro}, $f4")
        self.emitir("trunc.w.s $f4, $f4")
        self.emitir(f"mfc1 {registro}, $f4")

    def ajustar(self, registro, tipo_origen, tipo_destino):
        if tipo_destino == "decimal" and tipo_origen in {"entero", "booleano"}:
            self.a_decimal(registro)
        elif tipo_destino == "entero" and tipo_origen == "decimal":
            self.a_entero(registro)

    def cargar_dos(self, c, forzar_decimal=False):
        """Carga ambos operandos; si alguno es decimal, los dos quedan en flotante."""
        t1 = self.cargar_operando(c.argumento1, self.A)
        t2 = self.cargar_operando(c.argumento2, self.B)
        flotante = forzar_decimal or "decimal" in (t1, t2)
        if flotante:
            self.ajustar(self.A, t1, "decimal")
            self.ajustar(self.B, t2, "decimal")
            self.emitir(f"mtc1 {self.A}, $f4")
            self.emitir(f"mtc1 {self.B}, $f6")
        return flotante

    # =====================================================
    # OPERACIONES
    # =====================================================

    def generar_asignacion(self, c):
        tipo = self.cargar_operando(c.argumento1, self.A)
        self.ajustar(self.A, tipo, self.tipo_operando(c.resultado))
        self.guardar_resultado(c.resultado, self.A)

    def generar_aritmetica(self, c):
        flotante = self.cargar_dos(
            c, forzar_decimal=self.tipo_operando(c.resultado) == "decimal" and c.operador != "%"
        )

        if flotante and c.operador != "%":
            instruccion = {"+": "add.s", "-": "sub.s", "*": "mul.s", "/": "div.s"}[c.operador]
            self.emitir(f"{instruccion} $f4, $f4, $f6")
            self.emitir(f"mfc1 {self.A}, $f4")

        elif c.operador == "/":
            self.emitir(f"div {self.A}, {self.B}")
            self.emitir(f"mflo {self.A}")

        elif c.operador == "%":
            self.emitir(f"div {self.A}, {self.B}")
            self.emitir(f"mfhi {self.A}")

        else:
            instruccion = {"+": "add", "-": "sub", "*": "mul"}[c.operador]
            self.emitir(f"{instruccion} {self.A}, {self.A}, {self.B}")

        self.guardar_resultado(c.resultado, self.A)

    def generar_relacional(self, c):
        op = c.operador

        if self.cargar_dos(c):
            # Comparación en el coprocesador 1: la bandera se pasa a $k0.
            comparacion = {
                "<": "c.lt.s $f4, $f6",
                ">": "c.lt.s $f6, $f4",
                "<=": "c.le.s $f4, $f6",
                ">=": "c.le.s $f6, $f4",
                "==": "c.eq.s $f4, $f6",
                "!=": "c.eq.s $f4, $f6",
            }[op]
            etiqueta = self.nueva_etiqueta("Lcmp")
            self.emitir(comparacion)
            self.emitir(f"li {self.A}, 1")
            self.emitir(f"bc1t {etiqueta}")
            self.emitir(f"li {self.A}, 0")
            self.codigo.append(f"{etiqueta}:")
            if op == "!=":
                self.emitir(f"xori {self.A}, {self.A}, 1")

        elif op == "<":
            self.emitir(f"slt {self.A}, {self.A}, {self.B}")
        elif op == ">":
            self.emitir(f"slt {self.A}, {self.B}, {self.A}")
        elif op == "<=":
            self.emitir(f"slt {self.A}, {self.B}, {self.A}")
            self.emitir(f"xori {self.A}, {self.A}, 1")
        elif op == ">=":
            self.emitir(f"slt {self.A}, {self.A}, {self.B}")
            self.emitir(f"xori {self.A}, {self.A}, 1")
        elif op == "==":
            self.emitir(f"seq {self.A}, {self.A}, {self.B}")
        elif op == "!=":
            self.emitir(f"sne {self.A}, {self.A}, {self.B}")

        self.guardar_resultado(c.resultado, self.A)

    def generar_logica(self, c):
        self.cargar_operando(c.argumento1, self.A)
        self.cargar_operando(c.argumento2, self.B)

        instruccion = "and" if c.operador == "y" else "or"
        self.emitir(f"{instruccion} {self.A}, {self.A}, {self.B}")

        self.guardar_resultado(c.resultado, self.A)

    def generar_unaria(self, c):
        tipo = self.cargar_operando(c.argumento1, self.A)

        if c.operador == "UNARIO_-":
            if tipo == "decimal":
                self.emitir(f"mtc1 {self.A}, $f4")
                self.emitir("neg.s $f4, $f4")
                self.emitir(f"mfc1 {self.A}, $f4")
            else:
                self.emitir(f"sub {self.A}, $zero, {self.A}")

        elif c.operador == "UNARIO_no":
            self.emitir(f"sltiu {self.A}, {self.A}, 1")

        self.guardar_resultado(c.resultado, self.A)

    def generar_salto(self, c):
        self.emitir(f"j L{self.destino_salto(c)}")

    def generar_salto_condicional(self, c):
        self.cargar_operando(c.argumento1, self.A)
        self.emitir(f"beq {self.A}, $zero, L{self.destino_salto(c)}")

    # =====================================================
    # ZONAS Y PARA_CADA
    # =====================================================

    def generar_campo(self, c):
        """Los campos constantes van en .data; los calculados se guardan al ejecutar."""
        if self.es_literal(c.resultado):
            return
        campo = c.argumento2
        tipo = self.cargar_operando(c.resultado, self.A)
        self.ajustar(self.A, tipo, TIPO_CAMPO.get(campo, "entero"))
        desplazamiento = DESPLAZAMIENTO_CAMPO.get(campo, 0)
        self.emitir(f"sw {self.A}, zona_{nombre_seguro(c.argumento1)}+{desplazamiento}")

    def generar_iter_inicio(self, c):
        numero = len(self.iteradores)
        zonas = [z.strip() for z in c.argumento2.split(",") if z.strip()]
        self.iteradores.append(zonas)
        self.cursor_de[c.argumento1] = numero

        self.emitir(f"la {self.A}, iter_{numero}")
        self.emitir(f"sw {self.A}, cursor_{numero}")

    def generar_iter_siguiente(self, c):
        """Toma la siguiente zona de la lista; al terminar la variable queda en 0."""
        numero = self.cursor_de.get(c.argumento1, 0)
        self.emitir(f"lw {self.A}, cursor_{numero}")
        self.emitir(f"lw {self.B}, 0({self.A})")
        self.emitir(f"sw {self.B}, var_{nombre_seguro(c.argumento1)}")
        self.emitir(f"addi {self.A}, {self.A}, 4")
        self.emitir(f"sw {self.A}, cursor_{numero}")

    # =====================================================
    # FUNCIONES PREDEFINIDAS
    # =====================================================

    def imprimir_cadena(self, texto):
        self.emitir(f"la $a0, {self.cadena(texto)}")
        self.emitir("li $v0, 4")
        self.emitir("syscall")

    def imprimir_valor(self, valor):
        """Imprime un valor según su tipo."""
        tipo = self.cargar_operando(valor, "$a0")

        if tipo == "texto":
            self.emitir("li $v0, 4")
        elif tipo == "decimal":
            self.emitir("mtc1 $a0, $f12")
            self.emitir("li $v0, 2")
        elif tipo == "booleano":
            etiqueta = self.nueva_etiqueta("Lbool")
            self.emitir(f"move {self.A}, $a0")
            self.emitir(f"la $a0, {self.cadena('falso')}")
            self.emitir(f"beq {self.A}, $zero, {etiqueta}")
            self.emitir(f"la $a0, {self.cadena('verdadero')}")
            self.codigo.append(f"{etiqueta}:")
            self.emitir("li $v0, 4")
        elif tipo == "zona":
            self.emitir("lw $a0, 0($a0)")
            self.emitir("li $v0, 4")
        else:
            self.emitir("li $v0, 1")

        self.emitir("syscall")

    def salto_de_linea(self):
        self.emitir("li $a0, 10")
        self.emitir("li $v0, 11")
        self.emitir("syscall")

    def generar_parametro(self, c):
        self.parametros.append(c.argumento1)

    def generar_llamada(self, c):
        nombre = c.argumento1

        try:
            cantidad = int(c.argumento2 or 0)
        except ValueError:
            cantidad = 0
        cantidad = min(cantidad, len(self.parametros))
        argumentos = self.parametros[len(self.parametros) - cantidad:]
        del self.parametros[len(self.parametros) - cantidad:]

        self.codigo.append(f"    # {nombre}({', '.join(argumentos)})")

        if nombre == "registrar":
            for argumento in argumentos:
                self.imprimir_valor(argumento)
            self.salto_de_linea()

        elif nombre == "regar":
            # Simula la válvula: informa qué zona se riega y cuántos minutos.
            self.imprimir_cadena("Regando ")
            if argumentos:
                self.imprimir_valor(argumentos[0])
            if len(argumentos) > 1:
                self.imprimir_cadena(" durante ")
                self.imprimir_valor(argumentos[1])
                self.imprimir_cadena(" min")
            self.salto_de_linea()

        elif nombre == "leer":
            # Sensor: el valor se pide por la consola de MARS.
            self.imprimir_cadena("Sensor ")
            if len(argumentos) > 1:
                self.imprimir_valor(argumentos[1])
            if argumentos:
                self.imprimir_cadena(" de ")
                self.imprimir_valor(argumentos[0])
            self.imprimir_cadena(": ")
            self.emitir("li $v0, 6")
            self.emitir("syscall")
            self.emitir(f"mfc1 {self.A}, $f0")
            self.guardar_resultado(c.resultado, self.A)

        elif nombre == "lloviendo":
            self.imprimir_cadena("¿Está lloviendo? (1 = sí, 0 = no): ")
            self.emitir("li $v0, 5")
            self.emitir("syscall")
            self.emitir(f"sltu {self.A}, $zero, $v0")
            self.guardar_resultado(c.resultado, self.A)

        elif nombre == "a_entero":
            tipo = self.cargar_operando(argumentos[0] if argumentos else "0", self.A)
            if tipo == "decimal":
                self.a_entero(self.A)
            self.guardar_resultado(c.resultado, self.A)

    # =====================================================
    # PROGRAMA
    # =====================================================

    def generar_instruccion(self, c, numero):
        """Traduce un cuádruplo individual."""

        op = c.operador

        if op == "NOP":
            return

        elif op == "=":
            self.generar_asignacion(c)

        elif op in ARITMETICOS:
            self.generar_aritmetica(c)

        elif op in RELACIONALES:
            self.generar_relacional(c)

        elif op in LOGICOS:
            self.generar_logica(c)

        elif op in {"UNARIO_-", "UNARIO_no"}:
            self.generar_unaria(c)

        elif op == "JUMP":
            self.generar_salto(c)

        elif op == "JUMP_IF_FALSE":
            self.generar_salto_condicional(c)

        elif op == "PARAM":
            self.generar_parametro(c)

        elif op == "CALL":
            self.generar_llamada(c)

        elif op == "CAMPO":
            self.generar_campo(c)

        elif op == "ITER_INICIO":
            self.generar_iter_inicio(c)

        elif op == "ITER_SIGUIENTE":
            self.generar_iter_siguiente(c)

        elif op == "RET":
            self.emitir("li $v0, 10")
            self.emitir("syscall")

        elif op == "LABEL":
            self.codigo.append(f"L{c.resultado}:")

    def datos_variables(self):
        lineas = []
        for nombre in sorted(self.variables):
            tipo = self.variables[nombre]
            etiqueta = f"var_{nombre_seguro(nombre)}"
            if tipo == "decimal":
                lineas.append(f"{etiqueta}: .float 0.0  # decimal")
            elif tipo == "texto":
                lineas.append(f"{etiqueta}: .word {self.cadena('')}  # texto")
            else:
                lineas.append(f"{etiqueta}: .word 0  # {tipo or 'entero'}")
        return lineas

    def valor_campo(self, zona, campo, valor):
        if campo in {"nombre", "cultivo"}:
            texto = texto_de_literal(valor) if self.es_cadena(valor) else (valor or "")
            if campo == "nombre":
                texto = zona
            return f".word {self.cadena(texto)}"
        if campo == "humedad_min":
            numero = float(valor) if self.es_numero(valor) else 0.0
            return f".float {numero!r}"
        por_defecto = RIEGO_MAX_POR_DEFECTO if campo == "riego_max" else 0
        numero = int(float(valor)) if self.es_numero(valor) else por_defecto
        return f".word {numero}"

    def datos_zonas(self):
        lineas = []
        for zona, campos in self.zonas.items():
            lineas.append(f"zona_{nombre_seguro(zona)}:  # zona {zona}")
            for campo in CAMPOS_ZONA:
                valor = campos.get(campo, "")
                if campo == "riego_max" and campo not in campos:
                    valor = str(RIEGO_MAX_POR_DEFECTO)
                lineas.append(f"    {self.valor_campo(zona, campo, valor)}  # {campo}")
        for numero, zonas in enumerate(self.iteradores):
            lista = ", ".join(f"zona_{nombre_seguro(z)}" for z in zonas)
            lineas.append(f"iter_{numero}: .word {lista + ', ' if lista else ''}0")
            lineas.append(f"cursor_{numero}: .word 0")
        return lineas

    def datos_cadenas(self):
        return [
            f'{etiqueta}: .asciiz "{escapar_asciiz(texto)}"'
            for texto, etiqueta in self.cadenas.items()
        ]

    def generar(self):
        """Genera el programa MIPS completo."""

        self.preparar()
        self.codigo = []
        self.parametros = []

        # Generar instrucciones de cada cuádruplo (las etiquetas Ln solo
        # aparecen donde llega algún salto).
        for i, c in enumerate(self.cuadruplos, start=1):
            if str(i) in self.destinos:
                self.codigo.append(f"L{i}:")
            self.generar_instruccion(c, i)

        final = len(self.cuadruplos) + 1
        if str(final) in self.destinos:
            self.codigo.append(f"L{final}:")

        total_memoria = max(self.asignador.derramas.values(), default=0)

        salida = [
            "# Programa MILPA compilado a MIPS32 (MARS 4.5)",
            "",
            ".data",
        ]
        salida.extend(self.datos_variables())
        salida.extend(self.datos_zonas())
        salida.extend(self.datos_cadenas())

        salida.extend([
            "",
            ".text",
            ".globl main",
            "main:",
            "    move $fp, $sp",
        ])

        if total_memoria:
            salida.append(f"    addi $sp, $sp, -{total_memoria}")

        salida.extend(self.codigo)

        salida.extend([
            "",
            "    # Fin del programa",
            "    li $v0, 10",
            "    syscall",
        ])

        return "\n".join(salida) + "\n"

    def guardar(self, ruta):
        """Guarda el código generado en un archivo ASM."""

        contenido = self.generar()

        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)

        return ruta
