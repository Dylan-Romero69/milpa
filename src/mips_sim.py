"""
Lector y simulador de programas MIPS32 (sintaxis de MARS 4.5).

Permite que MILPA cargue un .asm, lo ensamble, lo ejecute instrucción por
instrucción y lea el estado final de la memoria para reconstruir el huerto.

Soporta las directivas .data/.text/.word/.float/.asciiz/.ascii/.space/.byte/
.half/.align, las instrucciones enteras y de punto flotante más comunes
(incluidas las pseudoinstrucciones de MARS como li, la, move, seq, blt...)
y las llamadas al sistema 1, 2, 4, 5, 6, 8, 10, 11 y 17.

Uso:
    sim = SimuladorMIPS(texto_asm, entrada=funcion_opcional)
    sim.ejecutar()
    estado = extraer_estado(sim)   # zonas y variables de un .asm de MILPA
"""

import math
import re
import struct


BASE_DATOS = 0x10010000
BASE_TEXTO = 0x00400000
PILA_INICIAL = 0x7FFFEFFC
GP_INICIAL = 0x10008000
MAX_PASOS = 2_000_000

NOMBRES_REGISTROS = [
    "zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
    "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
    "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
    "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra",
]
INDICE_REGISTRO = {nombre: i for i, nombre in enumerate(NOMBRES_REGISTROS)}
INDICE_REGISTRO["s8"] = 30

INSTRUCCIONES = {
    "add", "addu", "addi", "addiu", "sub", "subu", "subi", "subiu",
    "mul", "mulo", "mulou", "mult", "multu", "div", "divu", "rem", "remu",
    "mflo", "mfhi", "mtlo", "mthi", "and", "andi", "or", "ori", "xor", "xori",
    "nor", "not", "neg", "negu", "abs", "sll", "sllv", "srl", "srlv", "sra", "srav",
    "slt", "slti", "sltu", "sltiu", "seq", "sne", "sgt", "sge", "sle",
    "li", "la", "lui", "move", "nop", "lw", "sw", "lb", "lbu", "sb", "lh", "lhu", "sh",
    "j", "b", "jal", "jr", "jalr", "beq", "bne", "blt", "ble", "bgt", "bge",
    "bltu", "bleu", "bgtu", "bgeu", "beqz", "bnez", "bgez", "bgtz", "blez", "bltz",
    "mtc1", "mfc1", "lwc1", "l.s", "swc1", "s.s", "li.s", "add.s", "sub.s", "mul.s",
    "div.s", "neg.s", "abs.s", "mov.s", "sqrt.s", "cvt.s.w", "cvt.w.s", "trunc.w.s",
    "round.w.s", "floor.w.s", "ceil.w.s", "c.eq.s", "c.lt.s", "c.le.s", "bc1t", "bc1f",
    "syscall",
}


class ErrorMIPS(Exception):
    """Error al ensamblar o ejecutar, con la línea del .asm."""

    def __init__(self, mensaje, linea=None):
        self.linea = linea
        super().__init__(f"línea {linea}: {mensaje}" if linea else mensaje)


# =====================================================
# CONVERSIONES
# =====================================================

def a32(valor):
    """Ajusta un entero a 32 bits con signo."""
    valor &= 0xFFFFFFFF
    return valor - 0x100000000 if valor & 0x80000000 else valor


def sin_signo(valor):
    return valor & 0xFFFFFFFF


def bits_a_flotante(bits):
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def flotante_a_bits(valor):
    try:
        return struct.unpack("<I", struct.pack("<f", valor))[0]
    except OverflowError:
        return 0x7F800000 if valor > 0 else 0xFF800000


def formato_flotante(valor):
    """Imprime un float como Java (Float.toString), que es lo que hace MARS."""
    if math.isnan(valor):
        return "NaN"
    if math.isinf(valor):
        return "Infinity" if valor > 0 else "-Infinity"
    if valor == 0:
        return "-0.0" if math.copysign(1, valor) < 0 else "0.0"

    # Menor cantidad de dígitos que conserva el mismo float de 32 bits.
    bits = flotante_a_bits(valor)
    for digitos in range(1, 10):
        texto = f"{valor:.{digitos}g}"
        if flotante_a_bits(float(texto)) == bits:
            break
    numero = float(texto)

    if 1e-3 <= abs(numero) < 1e7:
        texto = repr(numero)
        if "e" in texto:
            texto = f"{numero:f}".rstrip("0")
        if texto.endswith("."):
            texto += "0"
        if "." not in texto:
            texto += ".0"
        return texto

    mantisa, exponente = f"{numero:.{max(digitos - 1, 1)}e}".split("e")
    mantisa = mantisa.rstrip("0")
    if mantisa.endswith("."):
        mantisa += "0"
    return f"{mantisa}E{int(exponente)}"


def decodificar_nombre(etiqueta):
    """Revierte nombre_seguro() del generador: _x28_ -> '('."""
    return re.sub(r"_x([0-9A-F]{2})_", lambda m: chr(int(m.group(1), 16)), etiqueta)


# =====================================================
# ANÁLISIS DEL TEXTO
# =====================================================

def separar_comentario(linea):
    """Devuelve (código, comentario) respetando el # dentro de comillas."""
    en_cadena = False
    escape = False
    for i, ch in enumerate(linea):
        if escape:
            escape = False
        elif ch == "\\":
            escape = True
        elif ch == '"':
            en_cadena = not en_cadena
        elif ch == "#" and not en_cadena:
            return linea[:i], linea[i + 1:].strip()
    return linea, ""


def leer_cadena(texto, linea):
    """Interpreta el contenido de un literal "..." con escapes."""
    texto = texto.strip()
    if len(texto) < 2 or texto[0] != '"' or texto[-1] != '"':
        raise ErrorMIPS(f"cadena inválida: {texto}", linea)
    escapes = {"n": "\n", "t": "\t", "0": "\0", "\\": "\\", '"': '"', "'": "'", "r": "\r"}
    resultado, i, contenido = [], 0, texto[1:-1]
    while i < len(contenido):
        ch = contenido[i]
        if ch == "\\" and i + 1 < len(contenido):
            resultado.append(escapes.get(contenido[i + 1], contenido[i + 1]))
            i += 2
        else:
            resultado.append(ch)
            i += 1
    return "".join(resultado)


def separar_operandos(texto):
    """Separa por comas (fuera de comillas)."""
    partes, actual, en_cadena = [], [], False
    for ch in texto:
        if ch == '"':
            en_cadena = not en_cadena
        if ch == "," and not en_cadena:
            partes.append("".join(actual).strip())
            actual = []
        else:
            actual.append(ch)
    if "".join(actual).strip():
        partes.append("".join(actual).strip())
    return partes


class Declaracion:
    """Un dato de .data: etiqueta, directiva, dirección y comentario."""

    def __init__(self, etiqueta, directiva, direccion, comentario, linea):
        self.etiqueta = etiqueta
        self.directiva = directiva
        self.direccion = direccion
        self.comentario = comentario
        self.linea = linea


# =====================================================
# SIMULADOR
# =====================================================

class SimuladorMIPS:

    def __init__(self, texto, entrada=None, max_pasos=MAX_PASOS):
        self.texto = texto
        self.entrada = entrada
        self.max_pasos = max_pasos

        self.memoria = {}
        self.etiquetas = {}
        self.instrucciones = []
        self.declaraciones = []
        self.pendientes = []

        self.registros = [0] * 32
        self.registros[INDICE_REGISTRO["sp"]] = PILA_INICIAL
        self.registros[INDICE_REGISTRO["gp"]] = GP_INICIAL
        self.flotantes = [0] * 32
        self.bandera_fp = [False] * 8
        self.hi = 0
        self.lo = 0
        self.pc = 0

        self.salida = []
        self.pasos = 0
        self.terminado = False
        self.error = None

        self.ensamblar()

    # -------------------------------------------------
    # ENSAMBLADO
    # -------------------------------------------------

    def ensamblar(self):
        seccion = "text"
        direccion_datos = BASE_DATOS
        etiquetas_pendientes = []

        for numero, cruda in enumerate(self.texto.splitlines(), start=1):
            codigo, comentario = separar_comentario(cruda)
            codigo = codigo.strip()

            while True:
                coincidencia = re.match(r"^([A-Za-z_.$][\w.$]*)\s*:(.*)$", codigo)
                if not coincidencia or coincidencia.group(1).startswith("."):
                    break
                etiqueta = coincidencia.group(1)
                if etiqueta in self.etiquetas:
                    raise ErrorMIPS(f"etiqueta repetida '{etiqueta}'", numero)
                if seccion == "data":
                    etiquetas_pendientes.append((etiqueta, numero, comentario))
                else:
                    self.etiquetas[etiqueta] = BASE_TEXTO + 4 * len(self.instrucciones)
                codigo = coincidencia.group(2).strip()

            if not codigo:
                continue

            partes = codigo.split(None, 1)
            nombre = partes[0].lower()
            resto = partes[1] if len(partes) > 1 else ""

            if nombre in {".data", ".kdata"}:
                seccion = "data"
                continue
            if nombre in {".text", ".ktext"}:
                seccion = "text"
                continue
            if nombre in {".globl", ".global", ".extern", ".eqv", ".set"}:
                continue

            if seccion == "data":
                direccion_datos = self.directiva(
                    nombre, resto, direccion_datos, numero, etiquetas_pendientes, comentario
                )
                etiquetas_pendientes = []
            else:
                if nombre.startswith("."):
                    raise ErrorMIPS(f"directiva '{nombre}' fuera de .data", numero)
                if nombre not in INSTRUCCIONES:
                    raise ErrorMIPS(f"instrucción desconocida '{nombre}'", numero)
                self.instrucciones.append((nombre, separar_operandos(resto), numero))

        for etiqueta, numero, comentario in etiquetas_pendientes:
            self.etiquetas[etiqueta] = direccion_datos

        for direccion, valor, numero in self.pendientes:
            self.escribir_palabra(direccion, self.valor_inmediato(valor, numero))

        for nombre, operandos, numero in self.instrucciones:
            for operando in operandos:
                for etiqueta in re.findall(r"(?<![$\w.])([A-Za-z_][\w.]*)", operando.split("(")[0]):
                    if etiqueta not in self.etiquetas and not re.fullmatch(r"0x[0-9A-Fa-f]+", etiqueta):
                        raise ErrorMIPS(f"etiqueta no definida '{etiqueta}'", numero)

        if "main" in self.etiquetas:
            self.pc = (self.etiquetas["main"] - BASE_TEXTO) // 4

    def alinear(self, direccion, tamaño):
        return (direccion + tamaño - 1) // tamaño * tamaño

    def directiva(self, nombre, resto, direccion, numero, etiquetas, comentario):
        tamaños = {".word": 4, ".float": 4, ".half": 2, ".byte": 1}
        if nombre in tamaños or nombre == ".double":
            direccion = self.alinear(direccion, 8 if nombre == ".double" else tamaños[nombre])

        for etiqueta, linea_etiqueta, comentario_etiqueta in etiquetas:
            self.etiquetas[etiqueta] = direccion
            self.declaraciones.append(Declaracion(
                etiqueta, nombre, direccion, comentario_etiqueta or comentario, linea_etiqueta
            ))
        if not etiquetas:
            self.declaraciones.append(Declaracion(None, nombre, direccion, comentario, numero))

        if nombre in {".asciiz", ".ascii"}:
            texto = leer_cadena(resto, numero)
            for ch in texto:
                self.memoria[direccion] = ord(ch) & 0xFF
                direccion += 1
            if nombre == ".asciiz":
                self.memoria[direccion] = 0
                direccion += 1
            return direccion

        if nombre == ".space":
            cantidad = self.valor_inmediato(resto, numero)
            for i in range(cantidad):
                self.memoria[direccion + i] = 0
            return direccion + cantidad

        if nombre == ".align":
            return self.alinear(direccion, 2 ** self.valor_inmediato(resto, numero))

        valores = separar_operandos(resto)

        if nombre in {".float", ".double"}:
            for valor in valores:
                try:
                    bits = flotante_a_bits(float(valor))
                except ValueError:
                    raise ErrorMIPS(f"número decimal inválido '{valor}'", numero)
                self.escribir_palabra(direccion, bits)
                direccion += 8 if nombre == ".double" else 4
            return direccion

        if nombre == ".word":
            for valor in valores:
                cantidad = 1
                if ":" in valor:
                    valor, repeticiones = valor.split(":", 1)
                    cantidad = self.valor_inmediato(repeticiones, numero)
                for _ in range(cantidad):
                    self.pendientes.append((direccion, valor.strip(), numero))
                    self.escribir_palabra(direccion, 0)
                    direccion += 4
            return direccion

        if nombre in {".half", ".byte"}:
            tamaño = tamaños[nombre]
            for valor in valores:
                numero_valor = self.valor_inmediato(valor, numero)
                for i in range(tamaño):
                    self.memoria[direccion + i] = (numero_valor >> (8 * i)) & 0xFF
                direccion += tamaño
            return direccion

        raise ErrorMIPS(f"directiva no soportada '{nombre}'", numero)

    # -------------------------------------------------
    # OPERANDOS
    # -------------------------------------------------

    def valor_inmediato(self, texto, linea=None):
        texto = str(texto).strip()
        if re.fullmatch(r"'(\\.|.)'", texto):
            return ord(leer_cadena('"' + texto[1:-1] + '"', linea))
        coincidencia = re.fullmatch(r"([A-Za-z_.$][\w.$]*)\s*([+-]\s*\w+)?", texto)
        if coincidencia and coincidencia.group(1) in self.etiquetas:
            desplazamiento = coincidencia.group(2)
            base = self.etiquetas[coincidencia.group(1)]
            return base + (int(desplazamiento.replace(" ", ""), 0) if desplazamiento else 0)
        try:
            return int(texto, 0)
        except ValueError:
            raise ErrorMIPS(f"valor o etiqueta desconocida '{texto}'", linea)

    def registro(self, texto, linea):
        nombre = texto.strip().lstrip("$")
        if nombre.isdigit() and int(nombre) < 32:
            return int(nombre)
        if nombre in INDICE_REGISTRO:
            return INDICE_REGISTRO[nombre]
        raise ErrorMIPS(f"registro inválido '{texto}'", linea)

    def registro_fp(self, texto, linea):
        coincidencia = re.fullmatch(r"\$f(\d+)", texto.strip())
        if not coincidencia or int(coincidencia.group(1)) > 31:
            raise ErrorMIPS(f"registro de punto flotante inválido '{texto}'", linea)
        return int(coincidencia.group(1))

    def direccion(self, texto, linea):
        """Resuelve etiqueta, etiqueta+n, n($r), ($r) y etiqueta($r)."""
        texto = texto.strip()
        coincidencia = re.fullmatch(r"(.*?)\(\s*(\$\w+)\s*\)", texto)
        if coincidencia:
            base = self.leer_registro(self.registro(coincidencia.group(2), linea))
            desplazamiento = coincidencia.group(1).strip()
            return sin_signo(base + (self.valor_inmediato(desplazamiento, linea) if desplazamiento else 0))
        return sin_signo(self.valor_inmediato(texto, linea))

    def destino(self, texto, linea):
        """Índice de instrucción de una etiqueta de .text."""
        direccion = self.valor_inmediato(texto, linea)
        return (direccion - BASE_TEXTO) // 4

    # -------------------------------------------------
    # MEMORIA Y REGISTROS
    # -------------------------------------------------

    def leer_registro(self, indice):
        return 0 if indice == 0 else self.registros[indice]

    def escribir_registro(self, indice, valor):
        if indice != 0:
            self.registros[indice] = a32(valor)

    def leer_byte(self, direccion):
        return self.memoria.get(sin_signo(direccion), 0)

    def leer_palabra(self, direccion, linea=None):
        direccion = sin_signo(direccion)
        if direccion % 4:
            raise ErrorMIPS(f"dirección 0x{direccion:08x} no alineada a palabra", linea)
        return a32(sum(self.leer_byte(direccion + i) << (8 * i) for i in range(4)))

    def escribir_palabra(self, direccion, valor, linea=None):
        direccion = sin_signo(direccion)
        if direccion % 4:
            raise ErrorMIPS(f"dirección 0x{direccion:08x} no alineada a palabra", linea)
        valor = sin_signo(valor)
        for i in range(4):
            self.memoria[direccion + i] = (valor >> (8 * i)) & 0xFF

    def leer_cadena_memoria(self, direccion, limite=10000):
        caracteres = []
        direccion = sin_signo(direccion)
        while len(caracteres) < limite:
            byte = self.leer_byte(direccion)
            if byte == 0:
                break
            caracteres.append(chr(byte))
            direccion += 1
        return "".join(caracteres)

    def fp(self, indice):
        return bits_a_flotante(self.flotantes[indice])

    def fijar_fp(self, indice, valor):
        self.flotantes[indice] = flotante_a_bits(valor)

    # -------------------------------------------------
    # ENTRADA / SALIDA
    # -------------------------------------------------

    def imprimir(self, texto):
        self.salida.append(texto)

    def texto_salida(self):
        return "".join(self.salida)

    def pedir(self, tipo):
        """Pide un valor a la función de entrada con el texto pendiente como pregunta."""
        pregunta = self.texto_salida().rsplit("\n", 1)[-1]
        valor = self.entrada(tipo, pregunta) if self.entrada else 0
        self.imprimir(f"{valor}\n")
        return valor

    # -------------------------------------------------
    # EJECUCIÓN
    # -------------------------------------------------

    def ejecutar(self):
        """Ejecuta hasta syscall 10/17, el final del código o un error."""
        try:
            while not self.terminado:
                if not 0 <= self.pc < len(self.instrucciones):
                    self.terminado = True
                    break
                if self.pasos >= self.max_pasos:
                    raise ErrorMIPS(
                        f"se alcanzó el límite de {self.max_pasos} instrucciones "
                        "(¿ciclo infinito?)"
                    )
                nombre, operandos, linea = self.instrucciones[self.pc]
                self.pc += 1
                self.pasos += 1
                self.paso(nombre, operandos, linea)
        except ErrorMIPS as error:
            self.error = str(error)
        except (ValueError, IndexError, ZeroDivisionError, OverflowError) as error:
            linea = self.instrucciones[self.pc - 1][2] if self.instrucciones else None
            self.error = str(ErrorMIPS(str(error), linea))
        return self

    def paso(self, nombre, ops, linea):
        r = lambda i: self.leer_registro(self.registro(ops[i], linea))
        w = lambda i, v: self.escribir_registro(self.registro(ops[i], linea), v)
        imm = lambda i: self.valor_inmediato(ops[i], linea)

        def segundo(i):
            """Registro o inmediato (para las pseudoinstrucciones como add $t0, $t1, 5)."""
            return r(i) if ops[i].strip().startswith("$") else imm(i)

        def saltar(i):
            self.pc = self.destino(ops[i], linea)

        def cuantos(n):
            if len(ops) != n:
                raise ErrorMIPS(f"'{nombre}' espera {n} operandos", linea)

        # ---------------- aritmética y lógica entera
        if nombre in {"add", "addu", "addi", "addiu"}:
            cuantos(3); w(0, r(1) + segundo(2))
        elif nombre in {"sub", "subu", "subi", "subiu"}:
            cuantos(3); w(0, r(1) - segundo(2))
        elif nombre in {"mul", "mulo", "mulou"}:
            cuantos(3); w(0, r(1) * segundo(2))
        elif nombre in {"mult", "multu"}:
            a, b = (r(0), r(1)) if nombre == "mult" else (sin_signo(r(0)), sin_signo(r(1)))
            producto = a * b
            self.lo, self.hi = a32(producto), a32(producto >> 32)
        elif nombre in {"div", "divu", "rem", "remu"}:
            if len(ops) == 2 and nombre in {"div", "divu"}:
                a, b = r(0), r(1)
                if nombre == "divu":
                    a, b = sin_signo(a), sin_signo(b)
                if b == 0:
                    raise ErrorMIPS("división entre cero", linea)
                cociente = abs(a) // abs(b) * (1 if (a >= 0) == (b >= 0) else -1)
                self.lo, self.hi = a32(cociente), a32(a - b * cociente)
            else:
                cuantos(3)
                a, b = r(1), segundo(2)
                if nombre in {"divu", "remu"}:
                    a, b = sin_signo(a), sin_signo(b)
                if b == 0:
                    raise ErrorMIPS("división entre cero", linea)
                cociente = abs(a) // abs(b) * (1 if (a >= 0) == (b >= 0) else -1)
                w(0, cociente if nombre in {"div", "divu"} else a - b * cociente)
        elif nombre == "mflo":
            w(0, self.lo)
        elif nombre == "mfhi":
            w(0, self.hi)
        elif nombre == "mtlo":
            self.lo = r(0)
        elif nombre == "mthi":
            self.hi = r(0)
        elif nombre in {"and", "andi"}:
            w(0, r(1) & (segundo(2) & (0xFFFF if nombre == "andi" else 0xFFFFFFFF)))
        elif nombre in {"or", "ori"}:
            w(0, r(1) | (segundo(2) & (0xFFFF if nombre == "ori" else 0xFFFFFFFF)))
        elif nombre in {"xor", "xori"}:
            w(0, r(1) ^ (segundo(2) & (0xFFFF if nombre == "xori" else 0xFFFFFFFF)))
        elif nombre == "nor":
            w(0, ~(r(1) | r(2)))
        elif nombre == "not":
            w(0, ~r(1))
        elif nombre in {"neg", "negu"}:
            w(0, -r(1))
        elif nombre == "abs":
            w(0, abs(r(1)))
        elif nombre in {"sll", "sllv"}:
            w(0, sin_signo(r(1)) << (segundo(2) & 31))
        elif nombre in {"srl", "srlv"}:
            w(0, sin_signo(r(1)) >> (segundo(2) & 31))
        elif nombre in {"sra", "srav"}:
            w(0, r(1) >> (segundo(2) & 31))
        elif nombre in {"slt", "slti"}:
            w(0, int(r(1) < segundo(2)))
        elif nombre in {"sltu", "sltiu"}:
            w(0, int(sin_signo(r(1)) < sin_signo(segundo(2))))
        elif nombre == "seq":
            w(0, int(r(1) == segundo(2)))
        elif nombre == "sne":
            w(0, int(r(1) != segundo(2)))
        elif nombre == "sgt":
            w(0, int(r(1) > segundo(2)))
        elif nombre == "sge":
            w(0, int(r(1) >= segundo(2)))
        elif nombre == "sle":
            w(0, int(r(1) <= segundo(2)))
        elif nombre == "li":
            cuantos(2); w(0, imm(1))
        elif nombre == "la":
            cuantos(2); w(0, self.direccion(ops[1], linea))
        elif nombre == "lui":
            w(0, (imm(1) & 0xFFFF) << 16)
        elif nombre == "move":
            cuantos(2); w(0, r(1))
        elif nombre == "nop":
            pass

        # ---------------- memoria
        elif nombre == "lw":
            w(0, self.leer_palabra(self.direccion(ops[1], linea), linea))
        elif nombre == "sw":
            self.escribir_palabra(self.direccion(ops[1], linea), r(0), linea)
        elif nombre in {"lb", "lbu"}:
            byte = self.leer_byte(self.direccion(ops[1], linea))
            w(0, byte - 256 if nombre == "lb" and byte & 0x80 else byte)
        elif nombre == "sb":
            self.memoria[self.direccion(ops[1], linea)] = r(0) & 0xFF
        elif nombre in {"lh", "lhu"}:
            direccion = self.direccion(ops[1], linea)
            media = self.leer_byte(direccion) | (self.leer_byte(direccion + 1) << 8)
            w(0, media - 65536 if nombre == "lh" and media & 0x8000 else media)
        elif nombre == "sh":
            direccion = self.direccion(ops[1], linea)
            valor = r(0)
            self.memoria[direccion] = valor & 0xFF
            self.memoria[direccion + 1] = (valor >> 8) & 0xFF

        # ---------------- saltos
        elif nombre in {"j", "b"}:
            saltar(0)
        elif nombre == "jal":
            self.escribir_registro(31, BASE_TEXTO + 4 * self.pc)
            saltar(0)
        elif nombre == "jr":
            self.pc = (sin_signo(r(0)) - BASE_TEXTO) // 4
        elif nombre == "jalr":
            destino = r(0) if len(ops) == 1 else r(1)
            self.escribir_registro(31 if len(ops) == 1 else self.registro(ops[0], linea),
                                   BASE_TEXTO + 4 * self.pc)
            self.pc = (sin_signo(destino) - BASE_TEXTO) // 4
        elif nombre in {"beq", "bne", "blt", "ble", "bgt", "bge", "bltu", "bleu", "bgtu", "bgeu"}:
            cuantos(3)
            a, b = r(0), segundo(1)
            if nombre.endswith("u"):
                a, b = sin_signo(a), sin_signo(b)
            base = nombre[:-1] if nombre.endswith("u") and nombre not in {"bne"} else nombre
            condicion = {
                "beq": a == b, "bne": a != b, "blt": a < b, "ble": a <= b,
                "bgt": a > b, "bge": a >= b,
            }[base]
            if condicion:
                saltar(2)
        elif nombre in {"beqz", "bnez", "bgez", "bgtz", "blez", "bltz"}:
            a = r(0)
            condicion = {
                "beqz": a == 0, "bnez": a != 0, "bgez": a >= 0,
                "bgtz": a > 0, "blez": a <= 0, "bltz": a < 0,
            }[nombre]
            if condicion:
                saltar(1)

        # ---------------- coprocesador 1 (punto flotante)
        elif nombre == "mtc1":
            self.flotantes[self.registro_fp(ops[1], linea)] = sin_signo(r(0))
        elif nombre == "mfc1":
            w(0, self.flotantes[self.registro_fp(ops[1], linea)])
        elif nombre in {"lwc1", "l.s"}:
            self.flotantes[self.registro_fp(ops[0], linea)] = sin_signo(
                self.leer_palabra(self.direccion(ops[1], linea), linea)
            )
        elif nombre in {"swc1", "s.s"}:
            self.escribir_palabra(
                self.direccion(ops[1], linea), self.flotantes[self.registro_fp(ops[0], linea)], linea
            )
        elif nombre == "li.s":
            self.fijar_fp(self.registro_fp(ops[0], linea), float(ops[1]))
        elif nombre in {"add.s", "sub.s", "mul.s", "div.s"}:
            a = self.fp(self.registro_fp(ops[1], linea))
            b = self.fp(self.registro_fp(ops[2], linea))
            if nombre == "div.s":
                resultado = a / b if b else (math.copysign(math.inf, a) if a else math.nan)
            else:
                resultado = {"add.s": a + b, "sub.s": a - b, "mul.s": a * b}[nombre]
            self.fijar_fp(self.registro_fp(ops[0], linea), resultado)
        elif nombre in {"neg.s", "abs.s", "mov.s", "sqrt.s"}:
            a = self.fp(self.registro_fp(ops[1], linea))
            resultado = {
                "neg.s": -a, "abs.s": abs(a), "mov.s": a,
                "sqrt.s": math.sqrt(a) if a >= 0 else math.nan,
            }[nombre]
            self.fijar_fp(self.registro_fp(ops[0], linea), resultado)
        elif nombre == "cvt.s.w":
            entero = a32(self.flotantes[self.registro_fp(ops[1], linea)])
            self.fijar_fp(self.registro_fp(ops[0], linea), float(entero))
        elif nombre in {"cvt.w.s", "trunc.w.s", "round.w.s", "floor.w.s", "ceil.w.s"}:
            a = self.fp(self.registro_fp(ops[1], linea))
            if math.isnan(a) or math.isinf(a) or abs(a) >= 2 ** 31:
                entero = 0x7FFFFFFF
            else:
                entero = {
                    "trunc.w.s": math.trunc, "floor.w.s": math.floor,
                    "ceil.w.s": math.ceil, "round.w.s": round, "cvt.w.s": round,
                }[nombre](a)
            self.flotantes[self.registro_fp(ops[0], linea)] = sin_signo(entero)
        elif nombre in {"c.eq.s", "c.lt.s", "c.le.s"}:
            indice = 0
            if len(ops) == 3:
                indice, ops = imm(0), ops[1:]
            a = self.fp(self.registro_fp(ops[0], linea))
            b = self.fp(self.registro_fp(ops[1], linea))
            self.bandera_fp[indice] = {"c.eq.s": a == b, "c.lt.s": a < b, "c.le.s": a <= b}[nombre]
        elif nombre in {"bc1t", "bc1f"}:
            indice = imm(0) if len(ops) == 2 else 0
            if self.bandera_fp[indice] == (nombre == "bc1t"):
                saltar(len(ops) - 1)

        # ---------------- llamadas al sistema
        elif nombre == "syscall":
            self.syscall(linea)

        else:
            raise ErrorMIPS(f"instrucción no soportada '{nombre}'", linea)

    def syscall(self, linea):
        codigo = self.leer_registro(INDICE_REGISTRO["v0"])
        a0 = self.leer_registro(INDICE_REGISTRO["a0"])

        if codigo == 1:
            self.imprimir(str(a0))
        elif codigo in {2, 3}:
            self.imprimir(formato_flotante(self.fp(12)))
        elif codigo == 4:
            self.imprimir(self.leer_cadena_memoria(a0))
        elif codigo == 5:
            self.escribir_registro(INDICE_REGISTRO["v0"], int(self.pedir("entero")))
        elif codigo in {6, 7}:
            self.fijar_fp(0, float(self.pedir("decimal")))
        elif codigo == 8:
            texto = str(self.pedir("texto"))
            limite = max(0, self.leer_registro(INDICE_REGISTRO["a1"]) - 1)
            for i, ch in enumerate(texto[:limite]):
                self.memoria[sin_signo(a0 + i)] = ord(ch) & 0xFF
            self.memoria[sin_signo(a0 + min(len(texto), limite))] = 0
        elif codigo in {10, 17}:
            self.terminado = True
        elif codigo == 11:
            self.imprimir(chr(a0 & 0xFF))
        else:
            raise ErrorMIPS(f"llamada al sistema {codigo} no soportada", linea)

    # -------------------------------------------------
    # CONSULTAS
    # -------------------------------------------------

    def palabra(self, etiqueta, desplazamiento=0):
        return self.leer_palabra(self.etiquetas[etiqueta] + desplazamiento)


# =====================================================
# ESTADO DE UN PROGRAMA MILPA
# =====================================================

def extraer_estado(sim):
    """
    Lee las zonas y variables de un .asm generado por MILPA.

    Zonas: etiquetas "zona_X" con el registro nombre/cultivo/humedad_min/riego_max.
    Variables: etiquetas "var_X"; el tipo sale del comentario (# entero, # decimal...)
    o, si no hay comentario, de la directiva (.float = decimal, .word = entero).
    """

    zonas = []
    variables = {}

    declaraciones = sim.declaraciones
    for indice, declaracion in enumerate(declaraciones):
        etiqueta = declaracion.etiqueta
        if not etiqueta:
            continue
        direccion = declaracion.direccion
        comentario = declaracion.comentario.strip().lower()

        if etiqueta.startswith("zona_"):
            try:
                nombre = sim.leer_cadena_memoria(sim.leer_palabra(direccion)) or decodificar_nombre(etiqueta[5:])
                zona = {
                    "nombre": nombre,
                    "cultivo": sim.leer_cadena_memoria(sim.leer_palabra(direccion + 4)),
                    "humedad_min": bits_a_flotante(sim.leer_palabra(direccion + 8)),
                    "riego_max": sim.leer_palabra(direccion + 12),
                    "fila": 0,
                    "columna": 0,
                }
                # Los .asm actuales traen fila y columna (+16, +20); los anteriores no.
                siguientes = [d.comentario.strip().lower() for d in declaraciones[indice + 4:indice + 6]]
                if siguientes == ["fila", "columna"]:
                    zona["fila"] = sim.leer_palabra(direccion + 16)
                    zona["columna"] = sim.leer_palabra(direccion + 20)
                zonas.append(zona)
            except ErrorMIPS:
                continue

        elif etiqueta.startswith("var_"):
            nombre = decodificar_nombre(etiqueta[4:])
            tipo = comentario.split()[0] if comentario else (
                "decimal" if declaracion.directiva == ".float" else "entero"
            )
            palabra = sim.leer_palabra(direccion)
            if tipo == "decimal":
                valor = bits_a_flotante(palabra)
            elif tipo == "texto":
                valor = sim.leer_cadena_memoria(palabra)
            elif tipo == "booleano":
                valor = palabra != 0
            elif tipo == "zona":
                valor = sim.leer_cadena_memoria(sim.leer_palabra(palabra)) if palabra else ""
            else:
                valor = palabra
            variables[nombre] = (tipo, valor)

    return {"zonas": zonas, "variables": variables}
