
import re

from src.regalloc import AsignadorRegistros


class GeneradorMIPS:
    """Traduce cuádruplos de MILPA a código MIPS32 para MARS."""

    def __init__(self, cuadruplos, asignador=None):
        self.cuadruplos = cuadruplos
        self.asignador = asignador or AsignadorRegistros(cuadruplos)

        self.ubicaciones = {}
        self.variables = set()
        self.cadenas = {}
        self.codigo = []
        self.datos = []
        self.parametros = []

        self.temporales_memoria = {}

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

    def preparar(self):
        """Prepara registros, variables y cadenas."""

        self.ubicaciones = self.asignador.asignar()

        self.variables.clear()
        self.cadenas.clear()
        self.temporales_memoria.clear()

        for temporal, desplazamiento in self.asignador.derramas.items():
            self.temporales_memoria[temporal] = desplazamiento

        for c in self.cuadruplos:

            # Los parámetros de texto se guardan como cadenas.
            if c.operador == "PARAM":
                valor = c.argumento1

                if valor and not self.es_numero(valor):
                    texto = valor.strip('"')
                    etiqueta = f"cadena_{len(self.cadenas)}"

                    if valor not in self.cadenas:
                        self.cadenas[valor] = etiqueta
                        self.datos.append(
                            f'{etiqueta}: .asciiz "{texto}"'
                        )

                continue

            # Los nombres de funciones no son variables.
            argumentos = (
                (c.argumento1, c.argumento2)
                if c.operador != "CALL"
                else ()
            )

            for argumento in argumentos:
                if not argumento:
                    continue

                if (
                    not self.es_temporal(argumento)
                    and not self.es_numero(argumento)
                    and not self.es_cadena(argumento)
                    and argumento.lower() not in {
                        "verdadero", "falso", "true", "false"
                    }
                ):
                    self.variables.add(argumento)

            if (
                c.resultado
                and not self.es_temporal(c.resultado)
                and not c.resultado.startswith("(")
            ):
                self.variables.add(c.resultado)

            if (
                c.resultado
                and not self.es_temporal(c.resultado)
                and not c.resultado.startswith("(")
            ):
                self.variables.add(c.resultado)

        numero_cadena = 0

        for c in self.cuadruplos:
            if c.operador == "PARAM" and self.es_cadena(c.argumento1):
                texto = c.argumento1[1:-1]
                etiqueta = f"cadena_{numero_cadena}"

                self.cadenas[c.argumento1] = etiqueta
                self.datos.append(
                    f'{etiqueta}: .asciiz "{texto}"'
                )

                numero_cadena += 1

        return self

    def cargar_operando(self, valor, registro):
        """Carga un operando en un registro de trabajo."""

        if self.es_numero(valor):
            self.codigo.append(f"li {registro}, {valor}")
            return

        if valor.lower() in {"verdadero", "true"}:
            self.codigo.append(f"li {registro}, 1")
            return

        if valor.lower() in {"falso", "false"}:
            self.codigo.append(f"li {registro}, 0")
            return

        if self.es_cadena(valor):
            etiqueta = self.cadenas.get(valor)

            if etiqueta:
                self.codigo.append(f"la {registro}, {etiqueta}")
            return

        if self.es_temporal(valor):
            ubicacion = self.ubicaciones.get(valor)

            if ubicacion and ubicacion.startswith("$"):
                if ubicacion != registro:
                    self.codigo.append(
                        f"move {registro}, {ubicacion}"
                    )
            elif ubicacion:
                self.codigo.append(
                    f"lw {registro}, {ubicacion}"
                )

            return

        self.codigo.append(f"lw {registro}, var_{valor}")

    def guardar_resultado(self, destino, registro):
        """Guarda el resultado en un temporal o variable."""

        if not destino:
            return

        if self.es_temporal(destino):
            ubicacion = self.ubicaciones.get(destino)

            if ubicacion and ubicacion.startswith("$"):
                if ubicacion != registro:
                    self.codigo.append(
                        f"move {ubicacion}, {registro}"
                    )
            elif ubicacion:
                self.codigo.append(
                    f"sw {registro}, {ubicacion}"
                )

        else:
            self.codigo.append(
                f"sw {registro}, var_{destino}"
            )

    def generar_aritmetica(self, c):
        """Genera instrucciones aritméticas."""

        operaciones = {
            "+": "add",
            "-": "sub",
            "*": "mul",
            "/": "div",
            "%": "rem",
        }

        self.cargar_operando(c.argumento1, "$k0")
        self.cargar_operando(c.argumento2, "$k1")

        if c.operador == "/":
            self.codigo.append("div $k0, $k1")
            self.codigo.append("mflo $k0")

        elif c.operador == "%":
            self.codigo.append("div $k0, $k1")
            self.codigo.append("mfhi $k0")

        else:
            instruccion = operaciones[c.operador]
            self.codigo.append(
                f"{instruccion} $k0, $k0, $k1"
            )

        self.guardar_resultado(c.resultado, "$k0")

    def generar_relacional(self, c):
        """Genera comparaciones relacionales."""

        a = c.argumento1
        b = c.argumento2
        op = c.operador

        self.cargar_operando(a, "$k0")
        self.cargar_operando(b, "$k1")

        if op == "<":
            self.codigo.append("slt $k0, $k0, $k1")

        elif op == ">":
            self.codigo.append("slt $k0, $k1, $k0")

        elif op == "<=":
            self.codigo.append("slt $k0, $k1, $k0")
            self.codigo.append("xori $k0, $k0, 1")

        elif op == ">=":
            self.codigo.append("slt $k0, $k0, $k1")
            self.codigo.append("xori $k0, $k0, 1")

        elif op == "==":
            self.codigo.append("seq $k0, $k0, $k1")

        elif op == "!=":
            self.codigo.append("sne $k0, $k0, $k1")

        self.guardar_resultado(c.resultado, "$k0")

    def generar_logica(self, c):
        """Genera operaciones lógicas."""

        self.cargar_operando(c.argumento1, "$k0")
        self.cargar_operando(c.argumento2, "$k1")

        if c.operador == "y":
            self.codigo.append("and $k0, $k0, $k1")
        else:
            self.codigo.append("or $k0, $k0, $k1")

        self.guardar_resultado(c.resultado, "$k0")

    def generar_unaria(self, c):
        """Genera operaciones unarias."""

        self.cargar_operando(c.argumento1, "$k0")

        if c.operador == "UNARIO_-":
            self.codigo.append("sub $k0, $zero, $k0")

        elif c.operador == "UNARIO_no":
            self.codigo.append("sltiu $k0, $k0, 1")

        self.guardar_resultado(c.resultado, "$k0")

    def generar_asignacion(self, c):
        self.cargar_operando(c.argumento1, "$k0")
        self.guardar_resultado(c.resultado, "$k0")

    def generar_salto(self, c):
        destino = c.resultado.strip("()")
        self.codigo.append(f"j L{destino}")

    def generar_salto_condicional(self, c):
        destino = c.resultado.strip("()")

        self.cargar_operando(c.argumento1, "$k0")

        self.codigo.append(
            f"beq $k0, $zero, L{destino}"
        )

    def generar_parametro(self, c):
        self.parametros.append(c.argumento1)

    def generar_llamada(self, c):
        nombre = c.argumento1

        if nombre == "registrar":
            if self.parametros:
                valor = self.parametros[-1]

                if self.es_cadena(valor):
                    self.cargar_operando(valor, "$a0")
                    self.codigo.append("li $v0, 4")
                else:
                    self.cargar_operando(valor, "$a0")
                    self.codigo.append("li $v0, 1")

                self.codigo.append("syscall")

        elif nombre == "regar":
            if self.parametros:
                self.cargar_operando(
                    self.parametros[-1], "$a0"
                )

                self.codigo.append(
                    "# Cantidad de agua disponible en $a0"
                )

        elif nombre == "leer":
            self.codigo.append("li $v0, 5")
            self.codigo.append("syscall")

            if c.resultado:
                self.guardar_resultado(
                    c.resultado, "$v0"
                )

        elif nombre == "lloviendo":
            # Primera versión: resultado booleano configurable.
            self.codigo.append("li $v0, 0")

            if c.resultado:
                self.guardar_resultado(
                    c.resultado, "$v0"
                )

        elif nombre == "a_entero":
            if self.parametros:
                self.cargar_operando(
                    self.parametros[-1], "$v0"
                )

            if c.resultado:
                self.guardar_resultado(
                    c.resultado, "$v0"
                )

        self.parametros.clear()

    def generar_instruccion(self, c, numero):
        """Traduce un cuádruplo individual."""

        op = c.operador

        if op == "NOP":
            return

        elif op == "=":
            self.generar_asignacion(c)

        elif op in {"+", "-", "*", "/", "%"}:
            self.generar_aritmetica(c)

        elif op in {"<", ">", "<=", ">=", "==", "!="}:
            self.generar_relacional(c)

        elif op in {"y", "o"}:
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

        elif op == "RET":
            self.codigo.append("li $v0, 10")
            self.codigo.append("syscall")

        elif op in {"LABEL"}:
            self.codigo.append(f"L{c.resultado}:")

    
    def generar(self):
        """Genera el programa MIPS completo."""

        self.preparar()
        self.codigo = []

        # Sección de datos
        salida = [".data"]

        for variable in sorted(self.variables):
            salida.append(f"var_{variable}: .word 0")

        salida.extend(self.datos)

        # Calcular memoria necesaria para temporales derramados
        total_memoria = max(
            self.asignador.derramas.values(),
            default=0
        )

        salida.extend([
            "",
            ".text",
            ".globl main",
            "main:",
            "move $fp, $sp",
        ])

        if total_memoria:
            salida.append(
                f"addi $sp, $sp, -{total_memoria}"
            )

        # Generar instrucciones de cada cuádruplo
        for i, c in enumerate(self.cuadruplos, start=1):
            self.codigo.append(f"L{i}:")
            self.generar_instruccion(c, i)

        # Incorporar las instrucciones MIPS generadas
        salida.extend(self.codigo)

        salida.extend([
            "",
            "# Fin del programa",
            "li $v0, 10",
            "syscall",
        ])

        return "\n".join(salida)


    def guardar(self, ruta):
        """Guarda el código generado en un archivo ASM."""

        contenido = self.generar()

        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)

        return ruta
