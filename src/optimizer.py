import re

class Optimizador:

    OPERACIONES_ARITMETICAS = {"+", "-", "*", "/", "%"}
    OPERACIONES_RELACIONALES = {"<", ">", "<=", ">=", "==", "!="}
    OPERACIONES_PURAS = (
        OPERACIONES_ARITMETICAS
        | OPERACIONES_RELACIONALES
        | {"y", "o", "UNARIO_-", "UNARIO_no"}
    )

    def __init__(self):
        self.cuadruplos = []
        self.metricas = {
            "locales": 0,
            "globales": 0,
            "mirilla": 0,
            "ciclos": 0,
            "total": 0,
        }

    
    def optimizar(self, cuadruplos):
        """Ejecuta todas las optimizaciones."""
        self.cuadruplos = [
            type(c)(
                c.operador,
                c.argumento1,
                c.argumento2,
                c.resultado
            )
            for c in cuadruplos
        ]

        self.metricas = {
            "locales": 0,
            "globales": 0,
            "mirilla": 0,
            "ciclos": 0,
            "total": 0,
        }

        self.optimizar_local()
        self.optimizar_global()
        self.optimizar_mirilla()
        self.optimizar_ciclos()

        # Eliminar instrucciones vacías al terminar
        self.eliminar_nop()

        self.metricas["total"] = sum(
            self.metricas[k]
            for k in ("locales", "globales", "mirilla", "ciclos")
        )

        return self.cuadruplos


    def es_temporal(self, nombre):
        return bool(re.fullmatch(r"t\d+", str(nombre)))

    def es_numero(self, valor):
        try:
            float(valor)
            return True
        except (ValueError, TypeError):
            return False

    def valor_numerico(self, valor):
        numero = float(valor)

        if numero.is_integer():
            return str(int(numero))

        return str(numero)

    def evaluar(self, operador, a, b=""):
        """Resuelve operaciones cuyos operandos son constantes."""
        try:
            if operador in self.OPERACIONES_ARITMETICAS:
                if not self.es_numero(a) or not self.es_numero(b):
                    return None

                x = float(a)
                y = float(b)

                if operador == "+":
                    resultado = x + y
                elif operador == "-":
                    resultado = x - y
                elif operador == "*":
                    resultado = x * y
                elif operador == "/":
                    if y == 0:
                        return None
                    resultado = x / y
                else:
                    if y == 0:
                        return None
                    resultado = x % y

                return self.valor_numerico(resultado)

            if operador in self.OPERACIONES_RELACIONALES:
                # Solo comparar valores numéricos constantes
                if not (
                    self.es_numero(a)
                    and self.es_numero(b)
                ):
                    return None

                x, y = float(a), float(b)

                operaciones = {
                    "<": lambda: x < y, # type: ignore
                    ">": lambda: x > y, # type: ignore
                    "<=": lambda: x <= y, # type: ignore
                    ">=": lambda: x >= y, # type: ignore
                    "==": lambda: x == y,
                    "!=": lambda: x != y,
                }

                return str(operaciones[operador]()).lower()

            if operador == "y":
                return str(
                    a.lower() == "verdadero"
                    and b.lower() == "verdadero"
                ).lower()

            if operador == "o":
                return str(
                    a.lower() == "verdadero"
                    or b.lower() == "verdadero"
                ).lower()

            if operador == "UNARIO_-":
                if self.es_numero(a):
                    return self.valor_numerico(-float(a))

            if operador == "UNARIO_no":
                valores = {
                    "verdadero": "falso",
                    "falso": "verdadero",
                    "true": "false",
                    "false": "true",
                }
                return valores.get(a.lower())

        except (ValueError, TypeError, ZeroDivisionError):
            return None

        return None

    def bloques_basicos(self):
        """Divide el código en bloques considerando los destinos de saltos."""
        lideres = {0}

        # Los destinos de saltos también inician bloques
        for i, c in enumerate(self.cuadruplos):
            if c.operador in {"JUMP", "JUMP_IF_FALSE"}:
                destino = c.resultado.strip("()")

                if destino.isdigit():
                    posicion = int(destino) - 1

                    if 0 <= posicion < len(self.cuadruplos):
                        lideres.add(posicion)

                # La instrucción posterior al salto inicia otro bloque
                if i + 1 < len(self.cuadruplos):
                    lideres.add(i + 1)

            elif c.operador in {"RET", "LABEL"}:
                if i + 1 < len(self.cuadruplos):
                    lideres.add(i + 1)

        lideres = sorted(lideres)
        bloques = []

        for i, inicio in enumerate(lideres):
            fin = (
                lideres[i + 1]
                if i + 1 < len(lideres)
                else len(self.cuadruplos)
            )

            bloques.append((inicio, fin))

        return bloques

    
    
    def optimizar_local(self):
        """Realiza propagación segura y plegado dentro de bloques básicos."""

        for inicio, fin in self.bloques_basicos():
            constantes = {}

            for i in range(inicio, fin):
                c = self.cuadruplos[i]

                if c.operador == "NOP":
                    continue

                # Sustituir únicamente temporales conocidos
                if c.operador not in {
                    "JUMP", "JUMP_IF_FALSE", "LABEL", "RET"
                }:
                    if self.es_temporal(c.argumento1):
                        c.argumento1 = constantes.get(
                            c.argumento1, c.argumento1
                        )

                    if self.es_temporal(c.argumento2):
                        c.argumento2 = constantes.get(
                            c.argumento2, c.argumento2
                        )

                # Plegar operaciones con operandos constantes
                if c.operador in self.OPERACIONES_PURAS:
                    resultado = self.evaluar(
                        c.operador,
                        c.argumento1,
                        c.argumento2
                    )

                    if resultado is not None:
                        c.operador = "="
                        c.argumento1 = resultado
                        c.argumento2 = ""
                        self.metricas["locales"] += 1

                # Guardar constantes únicamente en temporales
                if c.operador == "=":
                    destino = c.resultado
                    valor = c.argumento1

                    if self.es_temporal(destino):
                        if (
                            self.es_numero(valor)
                            or valor.lower() in {
                                "verdadero", "falso", "true", "false"
                            }
                        ):
                            constantes[destino] = valor
                        else:
                            constantes.pop(destino, None)

                # Las llamadas pueden modificar valores
                elif c.operador == "CALL":
                    constantes.clear()

                # Invalidar temporales modificados
                elif c.resultado and self.es_temporal(c.resultado):
                    constantes.pop(c.resultado, None)



    def eliminar_nop(self):
        """Elimina NOP y actualiza los destinos de los saltos."""
        originales = self.cuadruplos
        nuevos = []

        # Conserva únicamente instrucciones reales
        for c in originales:
            if c.operador != "NOP":
                nuevos.append(c)

        # Recalcular destinos de saltos
        for c in nuevos:
            if c.operador not in {"JUMP", "JUMP_IF_FALSE"}:
                continue

            destino = c.resultado.strip("()")

            if not destino.isdigit():
                continue

            posicion_original = int(destino)

            # Contar cuántas instrucciones sobreviven antes
            # de la posición de destino original.
            instrucciones_anteriores = originales[
                :max(0, posicion_original - 1)
            ]

            posicion_nueva = sum(
                1 for instruccion in instrucciones_anteriores
                if instruccion.operador != "NOP"
            ) + 1

            c.resultado = f"({posicion_nueva})"

        self.cuadruplos = nuevos
    
    def optimizar_global(self):
        """Elimina instrucciones que producen temporales sin uso."""
        cambios = True

        while cambios:
            cambios = False
            usos = {}

            # Contar los usos de temporales
            for c in self.cuadruplos:
                if c.operador == "NOP":
                    continue

                for argumento in (c.argumento1, c.argumento2):
                    if self.es_temporal(argumento):
                        usos[argumento] = usos.get(argumento, 0) + 1

            for c in self.cuadruplos:

                if c.operador == "NOP":
                    continue

                # Solo eliminar resultados temporales sin uso
                if (
                    self.es_temporal(c.resultado)
                    and usos.get(c.resultado, 0) == 0
                    and (
                        c.operador in self.OPERACIONES_PURAS
                        or c.operador == "="
                    )
                ):
                    c.operador = "NOP"
                    c.argumento1 = ""
                    c.argumento2 = ""
                    c.resultado = ""

                    self.metricas["globales"] += 1
                    cambios = True


    def optimizar_mirilla(self):
        """Aplica reglas sobre pequeñas ventanas de instrucciones."""
        for c in self.cuadruplos:

            if c.operador not in self.OPERACIONES_ARITMETICAS:
                continue

            a = c.argumento1
            b = c.argumento2
            resultado = None

            # x + 0 = x
            if c.operador == "+" and b == "0":
                resultado = a

            # x - 0 = x
            elif c.operador == "-" and b == "0":
                resultado = a

            # x * 1 = x
            elif c.operador == "*" and b == "1":
                resultado = a

            # x / 1 = x
            elif c.operador == "/" and b == "1":
                resultado = a

            # x * 0 = 0
            elif c.operador == "*" and b == "0":
                resultado = "0"

            if resultado is not None:
                c.operador = "="
                c.argumento1 = resultado
                c.argumento2 = ""
                self.metricas["mirilla"] += 1

    def optimizar_ciclos(self):
        """Elimina cálculos repetidos con operandos invariantes."""
        for i, salto in enumerate(self.cuadruplos):

            if salto.operador != "JUMP":
                continue

            destino = salto.resultado.strip("()")

            if not destino.isdigit():
                continue

            inicio = int(destino) - 1
            fin = i

            # Solo se considera un salto hacia atrás
            if inicio < 0 or inicio >= fin:
                continue

            ciclo = self.cuadruplos[inicio:fin]

            # Variables que reciben asignaciones dentro del ciclo
            modificadas = {
                c.resultado
                for c in ciclo
                if c.operador == "=" and c.resultado
            }

            expresiones = {}

            for c in ciclo:
                if c.operador not in self.OPERACIONES_PURAS:
                    continue

                a = c.argumento1
                b = c.argumento2

                # Solo expresiones con operandos invariantes
                if a in modificadas or b in modificadas:
                    continue

                clave = (c.operador, a, b)

                if clave in expresiones:
                    temporal_anterior = expresiones[clave]

                    c.operador = "="
                    c.argumento1 = temporal_anterior
                    c.argumento2 = ""
                    self.metricas["ciclos"] += 1

                elif self.es_temporal(c.resultado):
                    expresiones[clave] = c.resultado

    def imprimir(self):
        """Muestra el código intermedio optimizado."""
        print("\n========== CODIGO OPTIMIZADO ==========")

        print(
            f"{'N':<5}"
            f"{'OPERADOR':<20}"
            f"{'ARGUMENTO 1':<20}"
            f"{'ARGUMENTO 2':<20}"
            f"{'RESULTADO':<15}"
        )

        print("-" * 80)

        for i, c in enumerate(self.cuadruplos, start=1):
            print(
                f"{i:<5}"
                f"{c.operador:<20}"
                f"{c.argumento1:<20}"
                f"{c.argumento2:<20}"
                f"{c.resultado:<15}"
            )

        print("=" * 80)

    def imprimir_metricas(self):
        """Muestra el resumen de optimizaciones."""
        print("\n========== METRICAS DE OPTIMIZACION ==========")

        print(f"Optimizaciones locales:  {self.metricas['locales']}")
        print(f"Optimizaciones globales: {self.metricas['globales']}")
        print(f"Optimizaciones mirilla:  {self.metricas['mirilla']}")
        print(f"Optimizaciones ciclos:   {self.metricas['ciclos']}")
        print(f"Total de optimizaciones: {self.metricas['total']}")

        print("=" * 48)
