
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
from pathlib import Path

from gui.config.colors import COLORS
from gui.config.fonts import FONTS
from gui.config.styles import configurar_estilos

from gui.components.header import crear_header
from gui.components.sidebar import Sidebar

from gui.components.editor import CodeEditor
from gui.components.console import ConsolePanel

from gui.components.statusbar import StatusBar

# =========================================================
# MILPA IDE - PALETA VISUAL
# =========================================================

C = {
    "fondo": COLORS["background"],
    "blanco": COLORS["white"],
    "verde": COLORS["primary"],
    "verde2": COLORS["primary_light"],
    "verde_claro": COLORS["green_light"],
    "verde_suave": COLORS["green_soft"],
    "texto": COLORS["text"],
    "gris": COLORS["text_secondary"],
    "borde": COLORS["border"],
    "editor": COLORS["editor"],
    "codigo": COLORS["code"],
    "azul": COLORS["info"],
    "naranja": COLORS["warning"],
    "rojo": COLORS["error"],
    "sombra": COLORS["shadow"],
}


class MilpaIDE:

    def __init__(self, root):
        self.root = root
        self.archivo_actual = None
        self.seccion_actual = "Inicio"
        self.familia_fuente = FONTS["normal"][0]
        self.tamaño_fuente = 11
        self.huerto_columnas = 6
        self.huerto_filas = 4
        self.parcelas = {
            (fila, columna): {
                "tierra": False, "cultivo": "", "humedad_min": 35,
                "riego_max": 6, "humedad": 50, "estado": "vacía"
            }
            for fila in range(self.huerto_filas)
            for columna in range(self.huerto_columnas)
        }
        self.herramienta_huerto = tk.StringVar(master=root, value="tierra")
        self.cantidad_agua = tk.IntVar(master=root, value=15)
        self.parcela_seleccionada = None

        self.root.title("MILPA | Programa tu huerto")
        self.root.geometry("1500x900")
        self.root.minsize(1100, 700)
        self.root.configure(bg=C["fondo"])

        self.configurar_estilos()
        self.crear_interfaz()
        self.actualizar_lineas()
        
        self.cargar_ejemplo()

    # =====================================================
    # ESTILOS
    # =====================================================

    def configurar_estilos(self):
        configurar_estilos()

    # =====================================================
    # ESTRUCTURA GENERAL
    # =====================================================

    def crear_interfaz(self):

        self.header = tk.Frame(
            self.root,
            bg=C["blanco"],
            height=105
        )
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.crear_encabezado()

        cuerpo = tk.Frame(self.root, bg=C["fondo"])
        cuerpo.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(
            cuerpo,
            bg="#F0F2E9",
            width=220
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.crear_sidebar()

        contenido = tk.Frame(cuerpo, bg=C["fondo"])
        contenido.pack(
            side="left",
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        self.crear_area_trabajo(contenido)
        self.crear_barra_estado()

    # =====================================================
    # ENCABEZADO
    # =====================================================

    def crear_encabezado(self):
        crear_header(
            self.header,
            on_save=self.guardar,
            on_open=self.abrir,
            on_run=self.compilar,
            on_clear=self.limpiar,
            on_examples=self.mostrar_ejemplos,
            on_help=self.ayuda
        )

    def boton_header(self, padre, texto, comando, principal=False):

        bg = C["verde"] if principal else C["blanco"]
        fg = C["blanco"] if principal else C["texto"]

        tk.Button(
            padre,
            text=texto,
            command=comando,
            bg=bg,
            fg=fg,
            activebackground=C["verde2"],
            activeforeground=C["blanco"],
            font=("Aptos", 10, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=7,
            cursor="hand2"
        ).pack(side="left", padx=3)
        
    # =====================================================
    # BARRA DE ESTADO
    # =====================================================

    def crear_barra_estado(self):

        self.statusbar = StatusBar(self.root)

    # =====================================================
    # BARRA LATERAL
    # =====================================================

    def crear_sidebar(self):
        self.sidebar_component = Sidebar(
            self.sidebar,
            on_navigate=self.navegar
        )

    def navegar(self, nombre):
        self.seccion_actual = nombre
        self.sidebar_component.marcar_activo(nombre)
        acciones = {
            "Inicio": self.mostrar_inicio,
            "Nuevo programa": self.nuevo_programa,
            "Ejemplos": self.mostrar_ejemplos,
            "Simulador": self.mostrar_simulador,
            "Configuración": self.mostrar_configuracion,
        }
        accion = acciones.get(nombre)
        if accion:
            accion()

    # =====================================================
    # AREA DE TRABAJO
    # =====================================================

    def crear_area_trabajo(self, padre):
        self.vistas_principales = ttk.Notebook(padre)
        self.vistas_principales.pack(fill="both", expand=True)
        self.pagina_editor = tk.Frame(self.vistas_principales, bg=C["fondo"])
        self.pagina_ejemplos = tk.Frame(self.vistas_principales, bg=C["fondo"])
        self.pagina_simulador = tk.Frame(self.vistas_principales, bg=C["fondo"])
        self.vistas_principales.add(self.pagina_editor, text="Editor")
        self.vistas_principales.add(self.pagina_ejemplos, text="Biblioteca")
        self.vistas_principales.add(self.pagina_simulador, text="Huerto")

        columnas = tk.PanedWindow(
            self.pagina_editor,
            orient="horizontal",
            bg=C["fondo"],
            sashwidth=6,
            bd=0
        )
        columnas.pack(fill="both", expand=True)

        izquierda = tk.Frame(columnas, bg=C["fondo"])
        derecha = tk.Frame(columnas, bg=C["fondo"])

        columnas.add(izquierda, minsize=400, width=560)
        columnas.add(derecha, minsize=450)

        self.crear_editor(izquierda)
        self.crear_consola(izquierda)

        self.crear_panel_fases(derecha)
        
        self.crear_biblioteca_ejemplos(self.pagina_ejemplos)
        self.crear_panel_huerto(self.pagina_simulador)

    def crear_panel_huerto(self, padre):
        encabezado = tk.Frame(padre, bg=C["fondo"])
        encabezado.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(
            encabezado, text="Diseñador y simulador de huerto",
            bg=C["fondo"], fg=C["texto"], font=FONTS["title"]
        ).pack(side="left")
        ttk.Button(
            encabezado, text="Ver código en el editor",
            command=lambda: self.vistas_principales.select(self.pagina_editor)
        ).pack(side="right")
        tk.Label(
            padre,
            text="Selecciona una herramienta y pulsa una parcela. Verde: saludable; amarillo: seca; rojo: dañada. El código MILPA se sincroniza con el editor.",
            bg=C["fondo"], fg=C["gris"], font=FONTS["normal"], anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 8))

        cuerpo = tk.Frame(padre, bg=C["blanco"], highlightbackground=C["borde"], highlightthickness=1)
        cuerpo.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        lienzo_panel = tk.Frame(cuerpo, bg=C["blanco"])
        lienzo_panel.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        herramientas = tk.Frame(cuerpo, bg=C["verde_suave"], width=280)
        herramientas.pack(side="right", fill="y", padx=(0, 12), pady=12)
        herramientas.pack_propagate(False)

        barra = tk.Frame(lienzo_panel, bg=C["blanco"])
        barra.pack(fill="x", pady=(0, 8))
        for modo, etiqueta, icono in (
            ("tierra", "Tierra", "▧"),
            ("cultivo", "Cultivo", "♧"),
            ("agua", "Agua", "≈"),
            ("borrar", "Borrar", "⌫"),
        ):
            tk.Radiobutton(
                barra, text="{}  {}".format(icono, etiqueta),
                variable=self.herramienta_huerto, value=modo,
                indicatoron=False, relief="flat", padx=11, pady=7,
                bg=C["blanco"], fg=C["texto"], selectcolor=C["verde_claro"],
                activebackground=C["verde_claro"], font=FONTS["button"],
                cursor="hand2"
            ).pack(side="left", padx=(0, 5))

        self.canvas_huerto = tk.Canvas(
            lienzo_panel, bg="#E7EAD9", highlightthickness=0,
            height=520, cursor="crosshair"
        )
        self.canvas_huerto.pack(fill="both", expand=True)
        self.canvas_huerto.bind("<Configure>", lambda _e: self.dibujar_huerto())
        self.canvas_huerto.bind("<Button-1>", self.clic_parcela)

        tk.Label(
            herramientas, text="PARCELA SELECCIONADA", bg=C["verde_suave"],
            fg=C["verde"], font=FONTS["small"]
        ).pack(anchor="w", padx=14, pady=(16, 5))
        self.etiqueta_parcela = tk.Label(
            herramientas, text="Ninguna", bg=C["verde_suave"],
            fg=C["texto"], font=FONTS["heading"]
        )
        self.etiqueta_parcela.pack(anchor="w", padx=14, pady=(0, 14))
        self.detalle_parcela = tk.Label(
            herramientas, text="Elige una parcela para ver su estado.",
            justify="left", anchor="w", wraplength=245,
            bg=C["verde_suave"], fg=C["texto"], font=FONTS["normal"]
        )
        self.detalle_parcela.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Button(
            herramientas, text="Configurar cultivo",
            command=self.configurar_parcela_seleccionada
        ).pack(fill="x", padx=14, pady=(0, 16))
        tk.Label(
            herramientas, text="Agua por riego", bg=C["verde_suave"],
            fg=C["texto"], font=FONTS["normal"]
        ).pack(anchor="w", padx=14)
        tk.Scale(
            herramientas, from_=5, to=50, resolution=5, orient="horizontal",
            variable=self.cantidad_agua, bg=C["verde_suave"],
            highlightthickness=0, troughcolor=C["blanco"], showvalue=True
        ).pack(fill="x", padx=10)
        self.boton_regar = ttk.Button(
            herramientas, text="Añadir agua a parcela",
            command=self.regar_parcela_seleccionada
        )
        self.boton_regar.pack(fill="x", padx=14, pady=(3, 14))
        ttk.Button(
            herramientas, text="Reiniciar huerto",
            command=self.reiniciar_huerto
        ).pack(fill="x", padx=14, pady=(0, 14))
        tk.Label(
            herramientas,
            text="Las plantas se secan si la humedad baja de su mínimo y se dañan si el riego excede el límite.",
            justify="left", wraplength=245, bg=C["verde_suave"],
            fg=C["gris"], font=FONTS["small"]
        ).pack(fill="x", padx=14, pady=(0, 14))
        self.dibujar_huerto()
        self.root.after(3000, self.actualizar_huerto_en_tiempo_real)

    def mostrar_simulador(self):
        self.vistas_principales.select(self.pagina_simulador)
        self.root.after_idle(self.dibujar_huerto)

    def dibujar_huerto(self):
        if not hasattr(self, "canvas_huerto"):
            return
        canvas = self.canvas_huerto
        ancho, alto = canvas.winfo_width(), canvas.winfo_height()
        if ancho < 30 or alto < 30:
            return
        canvas.delete("all")
        margen, separacion = 18, 10
        celda = min(
            (ancho - 2 * margen - (self.huerto_columnas - 1) * separacion) / self.huerto_columnas,
            (alto - 2 * margen - (self.huerto_filas - 1) * separacion) / self.huerto_filas
        )
        celda = max(55, celda)
        ancho_grid = self.huerto_columnas * celda + (self.huerto_columnas - 1) * separacion
        alto_grid = self.huerto_filas * celda + (self.huerto_filas - 1) * separacion
        x0 = max(margen, (ancho - ancho_grid) / 2)
        y0 = max(margen, (alto - alto_grid) / 2)
        self.huerto_celdas = {}
        for fila in range(self.huerto_filas):
            for columna in range(self.huerto_columnas):
                x1 = x0 + columna * (celda + separacion)
                y1 = y0 + fila * (celda + separacion)
                x2, y2 = x1 + celda, y1 + celda
                parcela = self.parcelas[(fila, columna)]
                seleccionado = self.parcela_seleccionada == (fila, columna)
                self.huerto_celdas[(fila, columna)] = (x1, y1, x2, y2)
                fondo = "#805638" if parcela["tierra"] else "#D6DCCB"
                canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fondo,
                    outline=C["verde"] if seleccionado else "#FFFFFF",
                    width=4 if seleccionado else 2
                )
                if parcela["tierra"]:
                    canvas.create_rectangle(
                        x1 + 7, y1 + 7, x2 - 7, y2 - 7,
                        fill="#9A6B45", outline="#71472F", width=1
                    )
                    if parcela["cultivo"]:
                        estado = parcela["estado"]
                        color = {
                            "saludable": "#2E8B45", "seca": "#D0A331",
                            "dañada": "#9D4036"
                        }.get(estado, "#2E8B45")
                        cx, cy = (x1 + x2) / 2, y1 + celda * 0.48
                        canvas.create_line(cx, cy + 16, cx, cy - 10, fill="#3E6835", width=4)
                        canvas.create_oval(cx - 21, cy - 14, cx - 3, cy - 3, fill=color, outline="")
                        canvas.create_oval(cx + 3, cy - 22, cx + 21, cy - 11, fill=color, outline="")
                        canvas.create_oval(cx - 5, cy - 31, cx + 5, cy - 20, fill=color, outline="")
                        canvas.create_text(
                            cx, y2 - 23, text=parcela["cultivo"][:12],
                            fill="#FFFFFF", font=FONTS["tiny"]
                        )
                        canvas.create_oval(
                            x2 - 17, y1 + 9, x2 - 10, y1 + 16,
                            fill="#D8F0FF", outline=""
                        )
                    else:
                        canvas.create_text(
                            (x1 + x2) / 2, (y1 + y2) / 2,
                            text="Tierra", fill="#F7E5C5", font=FONTS["small"]
                        )
                canvas.create_text(
                    x1 + 15, y1 + 14, text="{}:{}".format(fila + 1, columna + 1),
                    fill="#FFFFFF" if parcela["tierra"] else C["gris"],
                    font=FONTS["tiny"]
                )
                if parcela["tierra"]:
                    canvas.create_text(
                        x2 - 22, y2 - 13, text="{}%".format(parcela["humedad"]),
                        fill="#FFFFFF", font=FONTS["tiny"]
                    )

    def clic_parcela(self, evento):
        for posicion, (x1, y1, x2, y2) in getattr(self, "huerto_celdas", {}).items():
            if x1 <= evento.x <= x2 and y1 <= evento.y <= y2:
                self.parcela_seleccionada = posicion
                parcela = self.parcelas[posicion]
                modo = self.herramienta_huerto.get()
                if modo == "tierra":
                    parcela["tierra"] = True
                    self.actualizar_estado_parcela(parcela)
                    self.sincronizar_codigo_huerto()
                elif modo == "cultivo":
                    if not parcela["tierra"]:
                        self.mensaje("Primero prepara la tierra de esa parcela.", "warning")
                    else:
                        self.configurar_parcela_seleccionada()
                elif modo == "agua":
                    if parcela["tierra"]:
                        parcela["humedad"] = min(100, parcela["humedad"] + self.cantidad_agua.get())
                        self.actualizar_estado_parcela(parcela)
                        self.sincronizar_codigo_huerto()
                    else:
                        self.mensaje("Añade tierra antes de regar la parcela.", "warning")
                elif modo == "borrar":
                    parcela.update({
                        "tierra": False, "cultivo": "", "humedad_min": 35,
                        "riego_max": 6, "humedad": 50, "estado": "vacía"
                    })
                    self.sincronizar_codigo_huerto()
                self.actualizar_detalle_parcela()
                self.dibujar_huerto()
                return

    def actualizar_estado_parcela(self, parcela):
        if not parcela["tierra"]:
            parcela["estado"] = "vacía"
        elif not parcela["cultivo"]:
            parcela["estado"] = "tierra"
        elif parcela["humedad"] < parcela["humedad_min"]:
            parcela["estado"] = "seca"
        elif parcela["humedad"] > parcela["humedad_min"] + parcela["riego_max"] * 5:
            parcela["estado"] = "dañada"
        else:
            parcela["estado"] = "saludable"

    def actualizar_detalle_parcela(self):
        posicion = self.parcela_seleccionada
        if posicion is None:
            if hasattr(self, "etiqueta_parcela"):
                self.etiqueta_parcela.configure(text="Ninguna")
                self.detalle_parcela.configure(
                    text="Elige una parcela para ver su estado."
                )
            return
        fila, columna = posicion
        parcela = self.parcelas[posicion]
        self.etiqueta_parcela.configure(
            text="Parcela {}:{}".format(fila + 1, columna + 1)
        )
        if not parcela["tierra"]:
            texto = "Sin preparar. Selecciona Tierra y pulsa este cubo."
        else:
            texto = (
                "Cultivo: {}\nHumedad actual: {}%\nMínimo requerido: {}%\n"
                "Riego máximo: {} L\nEstado: {}"
            ).format(
                parcela["cultivo"] or "sin cultivo", parcela["humedad"],
                parcela["humedad_min"], parcela["riego_max"], parcela["estado"]
            )
        self.detalle_parcela.configure(text=texto)

    def configurar_parcela_seleccionada(self):
        posicion = self.parcela_seleccionada
        if posicion is None:
            self.mensaje("Selecciona una parcela primero.", "warning")
            return
        parcela = self.parcelas[posicion]
        if not parcela["tierra"]:
            self.mensaje("Prepara la tierra antes de asignar un cultivo.", "warning")
            return
        fila, columna = posicion
        ventana = tk.Toplevel(self.root)
        ventana.title("Configurar parcela {}:{}".format(fila + 1, columna + 1))
        ventana.configure(bg=C["blanco"])
        ventana.resizable(False, False)
        ventana.transient(self.root)
        tk.Label(
            ventana, text="Cultivo y requerimientos",
            bg=C["blanco"], fg=C["texto"], font=FONTS["heading"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 12))
        campos = (
            ("Cultivo", tk.StringVar(value=parcela["cultivo"] or "tomate")),
            ("Humedad mínima (%)", tk.StringVar(value=str(parcela["humedad_min"]))),
            ("Riego máximo (L)", tk.StringVar(value=str(parcela["riego_max"]))),
        )
        entradas = {}
        for indice, (etiqueta, variable) in enumerate(campos, start=1):
            tk.Label(
                ventana, text=etiqueta, bg=C["blanco"],
                fg=C["gris"], font=FONTS["normal"]
            ).grid(row=indice, column=0, sticky="w", padx=18, pady=5)
            entrada = ttk.Entry(ventana, textvariable=variable, width=24)
            entrada.grid(row=indice, column=1, padx=(8, 18), pady=5)
            entradas[etiqueta] = variable
        tk.Label(
            ventana,
            text="El cultivo se daña al superar el mínimo + riego máximo × 5.",
            bg=C["blanco"], fg=C["gris"], font=FONTS["small"]
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=18, pady=(8, 3))

        def centrar_modal():
            ventana.update_idletasks()
            ancho, alto = ventana.winfo_width(), ventana.winfo_height()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - ancho) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - alto) // 2
            ventana.geometry("{}x{}+{}+{}".format(ancho, alto, x, y))
            ventana.grab_set()

        def aplicar():
            nombre = entradas["Cultivo"].get().strip()
            try:
                minimo = int(entradas["Humedad mínima (%)"].get())
                maximo = int(entradas["Riego máximo (L)"].get())
                if not nombre or not 0 <= minimo <= 100 or maximo <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Valores inválidos",
                    "Escribe un cultivo, humedad entre 0 y 100, y riego máximo mayor que 0.",
                    parent=ventana
                )
                return
            parcela.update({
                "cultivo": nombre.replace('"', ""),
                "humedad_min": minimo, "riego_max": maximo
            })
            self.actualizar_estado_parcela(parcela)
            self.actualizar_detalle_parcela()
            self.dibujar_huerto()
            self.sincronizar_codigo_huerto()
            ventana.destroy()

        ttk.Button(ventana, text="Aplicar", command=aplicar).grid(
            row=5, column=1, sticky="e", padx=18, pady=(10, 16)
        )
        ventana.after(0, centrar_modal)

    def regar_parcela_seleccionada(self):
        if self.parcela_seleccionada is None:
            self.mensaje("Selecciona una parcela primero.", "warning")
            return
        parcela = self.parcelas[self.parcela_seleccionada]
        if not parcela["tierra"]:
            self.mensaje("Añade tierra antes de regar la parcela.", "warning")
            return
        parcela["humedad"] = min(100, parcela["humedad"] + self.cantidad_agua.get())
        self.actualizar_estado_parcela(parcela)
        self.actualizar_detalle_parcela()
        self.dibujar_huerto()
        self.sincronizar_codigo_huerto()

    def reiniciar_huerto(self):
        for parcela in self.parcelas.values():
            parcela.update({
                "tierra": False, "cultivo": "", "humedad_min": 35,
                "riego_max": 6, "humedad": 50, "estado": "vacía"
            })
        self.parcela_seleccionada = None
        self.sincronizar_codigo_huerto()
        self.actualizar_detalle_parcela()
        self.dibujar_huerto()
        self.mensaje("Huerto reiniciado.", "exito")

    def sincronizar_codigo_huerto(self):
        lineas = []
        for (fila, columna), parcela in self.parcelas.items():
            if not parcela["tierra"]:
                continue
            nombre = "parcela_{}_{}".format(fila + 1, columna + 1)
            cultivo = (parcela["cultivo"] or "sin cultivo").replace('"', "")
            lineas.extend([
                "zona {} {{".format(nombre),
                '    cultivo: "{}",'.format(cultivo),
                "    humedad_min: {},".format(parcela["humedad_min"]),
                "    riego_max: {}".format(parcela["riego_max"]),
                "}",
                "entero humedad_actual_{}_{} = {}".format(
                    fila + 1, columna + 1, parcela["humedad"]
                ),
                'texto estado_cultivo_{}_{} = "{}"'.format(
                    fila + 1, columna + 1, parcela["estado"]
                ),
                ""
            ])
        if not lineas:
            lineas = ['registrar("Prepara tierra y añade cultivos en el simulador")']
        self.editor_component.establecer_codigo("\n".join(lineas).rstrip() + "\n")
        self.archivo_actual = None
        self.statusbar.actualizar_estado("Código del huerto sincronizado con el editor")

    def actualizar_huerto_en_tiempo_real(self):
        cambio = False
        simulador_visible = (
            self.vistas_principales.select() == str(self.pagina_simulador)
        )
        if simulador_visible:
            for parcela in self.parcelas.values():
                if parcela["tierra"] and parcela["cultivo"] and parcela["humedad"] > 0:
                    parcela["humedad"] = max(0, parcela["humedad"] - 1)
                    self.actualizar_estado_parcela(parcela)
                    cambio = True
        if cambio:
            self.dibujar_huerto()
            self.actualizar_detalle_parcela()
            self.sincronizar_codigo_huerto()
        self.root.after(3000, self.actualizar_huerto_en_tiempo_real)

    def crear_biblioteca_ejemplos(self, padre):
        tarjeta = self.tarjeta(padre, "Biblioteca de programas MILPA", "▤")
        tarjeta.pack(fill="both", expand=True)
        tk.Label(
            tarjeta,
            text="Explora las carpetas y abre un archivo con doble clic para cargarlo en el editor.",
            bg=C["blanco"], fg=C["gris"], font=FONTS["normal"], anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 6))

        contenedor = tk.Frame(tarjeta, bg=C["blanco"])
        contenedor.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.arbol_ejemplos = ttk.Treeview(
            contenedor, columns=("descripcion",), show="tree headings"
        )
        self.arbol_ejemplos.heading("#0", text="Carpetas y programas")
        self.arbol_ejemplos.heading("descripcion", text="Descripción")
        self.arbol_ejemplos.column("#0", width=300, anchor="w")
        self.arbol_ejemplos.column("descripcion", width=600, anchor="w")
        scroll = ttk.Scrollbar(
            contenedor, orient="vertical", command=self.arbol_ejemplos.yview
        )
        self.arbol_ejemplos.configure(yscrollcommand=scroll.set)
        self.arbol_ejemplos.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.rutas_ejemplos = {}
        self.cargar_archivos_ejemplo()
        self.arbol_ejemplos.bind("<Double-1>", self.abrir_ejemplo_seleccionado)

    def cargar_archivos_ejemplo(self):
        raiz = Path(__file__).resolve().parent.parent / "examples"
        descripciones = {
            "01_saludo.milpa": "Primer programa y salida en consola",
            "02_variables_y_operadores.milpa": "Variables, tipos y expresiones",
            "03_condicional.milpa": "Decisiones con si y si_no",
            "04_riego_con_bucle.milpa": "Ciclo mientras y riego",
            "05_zonas_de_cultivo.milpa": "Zonas, campos y recorrido",
            "06_conversion_y_sensores.milpa": "Sensores, conversiones y texto",
            "01_tipo_incompatible.milpa": "Error semántico: tipos incompatibles",
            "02_variable_no_declarada.milpa": "Error semántico: variable inexistente",
            "03_identificador_duplicado.milpa": "Error semántico: nombre repetido",
            "04_condicion_no_booleana.milpa": "Error semántico: condición inválida",
        }
        for carpeta in ("Funcionales", "Con errores"):
            nodo = self.arbol_ejemplos.insert(
                "", "end", text=carpeta, open=True, values=("Programas de prueba",)
            )
            for archivo in sorted((raiz / carpeta).glob("*.milpa")):
                elemento = self.arbol_ejemplos.insert(
                    nodo, "end", text=archivo.stem.replace("_", " "),
                    values=(descripciones.get(archivo.name, "Programa MILPA"),)
                )
                self.rutas_ejemplos[elemento] = archivo

    def mostrar_ejemplos(self):
        self.vistas_principales.select(self.pagina_ejemplos)
        self.mensaje("Biblioteca de ejemplos lista. Abre un programa con doble clic.")

    def mostrar_fase(self, nombre):
        self.vistas_principales.select(self.pagina_editor)
        self.seleccionar_fase(nombre)

    def mostrar_inicio(self):
        self.mostrar_fase("Léxico")

    def abrir_ejemplo_seleccionado(self, evento=None):
        seleccion = self.arbol_ejemplos.selection()
        if not seleccion:
            return
        ruta = self.rutas_ejemplos.get(seleccion[0])
        if ruta is None:
            self.arbol_ejemplos.item(seleccion[0], open=True)
            return
        try:
            self.editor_component.establecer_codigo(ruta.read_text(encoding="utf-8"))
        except OSError as error:
            messagebox.showerror("No se pudo abrir el ejemplo", str(error))
            return
        self.archivo_actual = None
        self.vistas_principales.select(self.pagina_editor)
        self.seleccionar_fase("Léxico")
        self.mensaje("Ejemplo cargado: {}".format(ruta.name), "exito")
        self.statusbar.actualizar_estado("Ejemplo cargado: {}".format(ruta.name))
        
    
    def crear_panel_fases(self, padre):

        tarjeta = self.tarjeta(
            padre,
            "Centro de análisis del compilador",
            "⌘"
        )
        tarjeta.pack(fill="both", expand=True)

        self.notebook_fases = ttk.Notebook(tarjeta)
        self.notebook_fases.pack(
            fill="both",
            expand=True,
            padx=7,
            pady=7
        )

        self.resultados = {}

        fases = [
            "Léxico",
            "Sintáctico",
            "AST",
            "Semántico",
            "Cuádruplos",
            "Optimización",
            "Registros",
            "MIPS",
            "Infija",
            "Prefija",
            "Postfija",
            "Simulador"
        ]

        for fase in fases:

            marco = tk.Frame(
                self.notebook_fases,
                bg=C["blanco"]
            )

            self.notebook_fases.add(
                marco,
                text=fase
            )

            if fase == "Léxico":
                self.crear_tabla_lexica(marco)

            else:
                texto = tk.Text(
                    marco,
                    bg=C["blanco"],
                    fg=C["codigo"],
                    font=("Cascadia Code", 10),
                    relief="flat",
                    padx=12,
                    pady=12,
                    wrap="none"
                )

                texto.pack(
                    fill="both",
                    expand=True
                )

                texto.insert(
                    "1.0",
                    f"Esperando compilación...\n\n"
                    f"Los resultados de {fase} aparecerán aquí."
                )

                texto.configure(state="disabled")

                self.resultados[fase] = texto


    def crear_tabla_lexica(self, padre):

        contenedor = tk.Frame(
            padre,
            bg=C["blanco"]
        )
        contenedor.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        tk.Label(
            contenedor,
            text="Tabla de tokens generados",
            bg=C["blanco"],
            fg=C["verde"],
            font=("Aptos", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        columnas = (
            "numero",
            "tipo",
            "lexema",
            "linea",
            "columna"
        )

        tabla = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings"
        )

        encabezados = {
            "numero": "#",
            "tipo": "Tipo de token",
            "lexema": "Lexema",
            "linea": "Línea",
            "columna": "Columna"
        }

        anchos = {
            "numero": 40,
            "tipo": 150,
            "lexema": 140,
            "linea": 60,
            "columna": 70
        }

        for columna in columnas:

            tabla.heading(
                columna,
                text=encabezados[columna]
            )

            tabla.column(
                columna,
                width=anchos[columna],
                anchor="center"
            )

        tabla.pack(
            fill="both",
            expand=True
        )

        self.tabla_tokens = tabla
        self.resultados["Léxico"] = tabla


    def mostrar_texto_fase(self, fase, contenido):

        widget = self.resultados.get(fase)

        if not isinstance(widget, tk.Text):
            return

        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", str(contenido))
        widget.configure(state="disabled")

    def seleccionar_fase(self, nombre):
        for pestaña in self.notebook_fases.tabs():
            if self.notebook_fases.tab(pestaña, "text") == nombre:
                self.notebook_fases.select(pestaña)
                return


    def limpiar_resultados(self):

        for fase, widget in self.resultados.items():

            if fase == "Léxico":
                for elemento in widget.get_children():
                    widget.delete(elemento)

            elif isinstance(widget, tk.Text):
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.insert(
                    "1.0",
                    f"Esperando resultados de {fase}..."
                )
                widget.configure(state="disabled")


    # =====================================================
    # TARJETAS
    # =====================================================

    def tarjeta(self, padre, titulo, icono=""):

        contenedor = tk.Frame(
            padre,
            bg=C["blanco"],
            highlightbackground=C["borde"],
            highlightthickness=1
        )

        encabezado = tk.Frame(
            contenedor,
            bg=C["verde_claro"],
            height=43
        )
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text=f"  {icono}  {titulo}",
            bg=C["verde_claro"],
            fg=C["texto"],
            font=("Aptos", 12, "bold"),
            anchor="w"
        ).pack(fill="both", padx=8)

        return contenedor

    # =====================================================
    # EDITOR
    # =====================================================

    def crear_editor(self, padre):
        self.editor_component = CodeEditor(padre)
        self.editor_component.frame.pack(
            fill="both",
            expand=True,
            pady=(0, 10)
        )
        # Referencia compatible con el código anterior
        self.editor = self.editor_component.text

    def actualizar_lineas(self):
        self.editor_component.actualizar_lineas()

    def sincronizar_lineas(self):
        self.editor_component.actualizar_lineas()

    # =====================================================
    # CONSOLA
    # =====================================================

    def crear_consola(self, padre):
        self.console_component = ConsolePanel(padre)

        self.console_component.frame.pack(
            fill="both",
            expand=True
        )

        # Referencia compatible con el código anterior
        self.consola = self.console_component.consola

    def mensaje(self, texto, tipo="normal"):
        if not hasattr(self, "console_component"):
            return

        if tipo == "error":
            self.console_component.error(texto)

        elif tipo == "exito":
            self.console_component.exito(texto)

        elif tipo == "warning":
            self.console_component.advertencia(texto)

        else:
            self.console_component.mensaje(texto)

    # =====================================================
    # REGISTRO DE EJECUCION
    # =====================================================

    def registrar(self, texto):
        if hasattr(self, "console_component"):
            self.console_component.registrar(texto)

        elif hasattr(self, "consola"):
            self.mensaje(texto)

    # =====================================================
    # ACCIONES
    # =====================================================

    def abrir(self):

        ruta = filedialog.askopenfilename(
            filetypes=[
                ("Programas MILPA", "*.milpa"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        try:
            contenido = Path(ruta).read_text(encoding="utf-8")

            self.editor_component.establecer_codigo(contenido)
            self.archivo_actual = Path(ruta)
            self.vistas_principales.select(self.pagina_editor)
            self.mensaje(f"Archivo abierto: {ruta}", "exito")

        except OSError as error:
            messagebox.showerror("Error", str(error))

    def guardar(self):

        if self.archivo_actual is None:

            ruta = filedialog.asksaveasfilename(
                defaultextension=".milpa",
                filetypes=[("Programas MILPA", "*.milpa")]
            )

            if not ruta:
                return

            self.archivo_actual = Path(ruta)

        try:
            contenido = self.editor.get("1.0", "end-1c")

            self.archivo_actual.write_text(
                contenido,
                encoding="utf-8"
            )

            self.mensaje("Programa guardado correctamente.", "exito")

        except OSError as error:
            messagebox.showerror("Error", str(error))

    def limpiar(self):

        confirmar = messagebox.askyesno(
            "Limpiar editor",
            "¿Deseas borrar todo el código?"
        )

        if confirmar:
            self.editor_component.limpiar()
            self.mensaje("Editor limpiado.")

    
    def cargar_ejemplo(self):

        ejemplo = (
            'zona huerto_norte {\n'
            '    cultivo: "jitomate"\n'
            '    humedad_min: 40.0\n'
            '}\n'
            '\n'
            'decimal litros_total = 0\n'
            '\n'
            'entero humedad = 35\n'
            'entero limite = 80\n'
            '\n'
            'mientras (humedad < limite) {\n'
            '    regar(1)\n'
            '    humedad = humedad + 5\n'
            '    litros_total = litros_total + 1.5\n'
            '}\n'
            '\n'
            'registrar("Riego completado")\n'
        )

        self.editor_component.establecer_codigo(ejemplo)

        self.mensaje("Ejemplo agrícola cargado correctamente.", "exito")


    def compilar(self):
        from src.core.errors import ErrorLog
        from src.frontend.lexer import Lexer
        from src.parser import Parser
        from src.frontend.semantic import AnalizadorSemantico
        from src.frontend.ast_nodes import imprimir_ast
        from src.intermediate import GeneradorIntermedio
        from src.optimizer import Optimizador
        from src.regalloc import AsignadorRegistros
        from src.codegen_mips import GeneradorMIPS
        from src.notation import a_postfija, a_prefija
        import contextlib
        import io

        self.vistas_principales.select(self.pagina_editor)
        self.limpiar_resultados()
        errores = ErrorLog()
        codigo = self.editor_component.obtener_codigo()
        self.mensaje("Iniciando compilación completa.")
        self.statusbar.actualizar_estado("Compilando...")

        def mostrar_errores():
            errores_por_fase = {}
            for error in errores.obtener_errores():
                fase = {
                    "léxico": "Léxico",
                    "Lexico": "Léxico",
                    "sintáctico": "Sintáctico",
                    "Sintactico": "Sintáctico",
                    "Semantico": "Semántico",
                }.get(error.fase, "Semántico")
                errores_por_fase.setdefault(fase, []).append(str(error))
                self.mensaje(str(error), "error")
                self.registrar(str(error))
            for fase, mensajes in errores_por_fase.items():
                if fase != "Léxico":
                    self.mostrar_texto_fase(fase, "\n".join(mensajes))
            fase_actual = next(iter(errores_por_fase), "Semántico")
            self.seleccionar_fase(fase_actual)
            self.statusbar.actualizar_estado(
                "Compilación detenida: {} error(es)".format(
                    len(errores.obtener_errores())
                )
            )
        try:
            lexer = Lexer(codigo, errores)
            tokens = lexer.analizar()
            self.mostrar_tokens(tokens)
            if errores.hay_errores():
                mostrar_errores()
                return

            arbol = Parser(tokens, errores).analizar()
            if arbol is None or errores.hay_errores():
                mostrar_errores()
                return
            salida = io.StringIO()
            with contextlib.redirect_stdout(salida):
                imprimir_ast(arbol)
            self.mostrar_texto_fase(
                "Sintáctico", "Análisis sintáctico correcto.\nAST construido correctamente."
            )
            self.mostrar_texto_fase("AST", salida.getvalue())

            semantico = AnalizadorSemantico(errores)
            semantico.analizar(arbol)
            if errores.hay_errores():
                mostrar_errores()
                return
            simbolos = semantico.tabla.obtener_todos()
            tabla = "NOMBRE\tTIPO\tCATEGORÍA\tVALOR\n" + "-" * 50 + "\n"
            tabla += "\n".join(
                "{}\t{}\t{}\t{}".format(x.nombre, x.tipo, x.categoria, x.valor)
                for x in simbolos
            )
            self.mostrar_texto_fase(
                "Semántico",
                "Análisis semántico correcto.\n\n" +
                (tabla if simbolos else "Sin símbolos declarados.")
            )

            generador = GeneradorIntermedio()
            cuadruplos = generador.generar(arbol)
            original = "\n".join(str(x) for x in cuadruplos) or "Sin instrucciones."
            self.mostrar_texto_fase("Cuádruplos", original)

            optimizador = Optimizador()
            optimizados = optimizador.optimizar(cuadruplos)
            metricas = "\n".join(
                "{}: {}".format(k, v) for k, v in optimizador.metricas.items()
            )
            texto_opt = "CUÁDRUPLOS OPTIMIZADOS\n{}\n\nMÉTRICAS\n{}".format(
                "\n".join(str(x) for x in optimizados) or "Sin instrucciones.",
                metricas
            )
            self.mostrar_texto_fase("Optimización", texto_opt)

            asignador = AsignadorRegistros(optimizados)
            ubicaciones = asignador.asignar()
            asignaciones = "\n".join(
                "{}: {}".format(k, v) for k, v in ubicaciones.items()
            ) or "Sin temporales."
            self.mostrar_texto_fase(
                "Registros",
                "ASIGNACIONES\n{}\n\nDERRAMAS\n{}".format(
                    asignaciones, asignador.derramas
                )
            )

            generador_mips = GeneradorMIPS(optimizados, asignador)
            ensamblador = generador_mips.generar()
            self.mostrar_texto_fase("MIPS", ensamblador)
            ruta_salida = (
                self.archivo_actual.with_suffix(".asm")
                if self.archivo_actual else Path.cwd() / "salida.asm"
            )
            generador_mips.guardar(ruta_salida)

            expresiones = [
                "{} {} {}".format(c.argumento1, c.operador, c.argumento2)
                for c in cuadruplos
                if c.operador in {"+", "-", "*", "/", "%", "<", ">", "<=", ">=", "==", "!="}
            ]
            infija = expresiones[0] if expresiones else "Sin expresiones aritméticas."
            if expresiones:
                try:
                    post = a_postfija(infija)
                    pre = a_prefija(infija)
                except ValueError:
                    post = pre = "No se pudo convertir automáticamente."
            else:
                post = pre = infija
            self.mostrar_texto_fase("Infija", infija)
            self.mostrar_texto_fase("Prefija", pre)
            self.mostrar_texto_fase("Postfija", post)
            self.mostrar_texto_fase(
                "Simulador", "Traza del programa compilado\n\n" + original
            )

            self.mensaje(
                "Compilación correcta. MIPS guardado en {}".format(ruta_salida),
                "exito"
            )
            self.registrar(
                "Compilación terminada correctamente. Salida: {}".format(ruta_salida)
            )
            self.statusbar.actualizar_estado("Compilación correcta")
            self.seleccionar_fase("MIPS")
        except Exception as error:
            self.mensaje("Error durante la compilación: {}".format(error), "error")
            self.registrar("Error de compilación: {}".format(error))
            self.statusbar.actualizar_estado("Error durante la compilación")

    def nuevo_programa(self):
        self.editor_component.limpiar()
        self.archivo_actual = None
        self.vistas_principales.select(self.pagina_editor)
        self.notebook_fases.select(0)
        self.mensaje("Editor listo para un programa nuevo.")

    def mostrar_configuracion(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Configuración de MILPA")
        ventana.configure(bg=C["blanco"])
        ventana.resizable(False, False)
        ventana.transient(self.root)
        tk.Label(
            ventana, text="Preferencias de MILPA",
            bg=C["blanco"], fg=C["texto"], font=FONTS["heading"]
        ).pack(anchor="w", padx=22, pady=(20, 12))
        tk.Label(
            ventana, text="Familia tipográfica",
            bg=C["blanco"], fg=C["gris"], font=FONTS["normal"]
        ).pack(anchor="w", padx=22)
        fuentes_instaladas = sorted(set(tkfont.families(self.root)))
        preferidas = [
            "Aptos", "Aptos Display", "Segoe UI", "Arial",
            "Calibri", "Cascadia Code", "Consolas", "Georgia"
        ]
        opciones_fuente = [f for f in preferidas if f in fuentes_instaladas]
        opciones_fuente += [f for f in fuentes_instaladas if f not in opciones_fuente]
        familia = tk.StringVar(value=self.familia_fuente)
        selector = ttk.Combobox(
            ventana, textvariable=familia, values=opciones_fuente,
            state="readonly", width=34
        )
        selector.pack(fill="x", padx=22, pady=(5, 12))
        tk.Label(
            ventana, text="Tamaño de letra",
            bg=C["blanco"], fg=C["gris"], font=FONTS["normal"]
        ).pack(anchor="w", padx=22)
        tamaño = tk.IntVar(value=self.tamaño_fuente)
        ttk.Spinbox(
            ventana, from_=8, to=24, textvariable=tamaño, width=8
        ).pack(anchor="w", padx=22, pady=(5, 12))
        muestra = tk.Label(
            ventana, text="MILPA  ·  Cultivo saludable",
            bg=C["blanco"], fg=C["verde"], font=(familia.get(), 13, "bold")
        )
        muestra.pack(fill="x", padx=22, pady=(0, 10))
        selector.bind(
            "<<ComboboxSelected>>",
            lambda _e: muestra.configure(font=(familia.get(), 13, "bold"))
        )

        def centrar_modal():
            ventana.update_idletasks()
            ancho, alto = ventana.winfo_width(), ventana.winfo_height()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - ancho) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - alto) // 2
            ventana.geometry("{}x{}+{}+{}".format(ancho, alto, x, y))
            ventana.grab_set()

        def aplicar():
            self.familia_fuente = familia.get()
            self.tamaño_fuente = tamaño.get()
            nueva_familia = self.familia_fuente
            nuevo_tamaño = self.tamaño_fuente
            base_tamaño = FONTS["normal"][1]
            for clave, fuente in FONTS.items():
                nuevo_tamaño_fuente = max(
                    6, round(fuente[1] * nuevo_tamaño / base_tamaño)
                )
                FONTS[clave] = (
                    nueva_familia, nuevo_tamaño_fuente
                ) + tuple(fuente[2:])
            self.aplicar_fuente_a_widget(self.root, nueva_familia, nuevo_tamaño)
            estilo = ttk.Style(self.root)
            estilo.configure(".", font=(nueva_familia, nuevo_tamaño))
            estilo.configure("Treeview", font=(nueva_familia, nuevo_tamaño))
            estilo.configure(
                "Treeview.Heading", font=(nueva_familia, nuevo_tamaño, "bold")
            )
            self.dibujar_huerto()
            ventana.destroy()
            self.mensaje("Tipografía actualizada.", "exito")

        ttk.Button(ventana, text="Aplicar", command=aplicar).pack(
            anchor="e", padx=22, pady=(0, 20)
        )
        ventana.after(0, centrar_modal)

    def aplicar_fuente_a_widget(self, widget, familia, tamaño):
        try:
            actual = tkfont.Font(root=self.root, font=widget.cget("font")).actual()
            tamaño_anterior = max(1, abs(int(actual["size"])))
            tamaño_escalado = max(6, round(tamaño_anterior * tamaño / 10))
            widget.configure(font=(
                familia, tamaño_escalado, actual["weight"], actual["slant"],
                actual["underline"], actual["overstrike"]
            ))
        except (tk.TclError, TypeError, ValueError):
            pass
        for hijo in widget.winfo_children():
            self.aplicar_fuente_a_widget(hijo, familia, tamaño)

    def mostrar_tokens(self, tokens):

        self.tabla_tokens.delete(
            *self.tabla_tokens.get_children()
        )

        for numero, token in enumerate(tokens, start=1):

            self.tabla_tokens.insert(
                "",
                "end",
                values=(
                    numero,
                    token.tipo,
                    token.valor,
                    token.linea,
                    token.columna
                )
            )

    def ayuda(self):

        messagebox.showinfo(
            "Ayuda MILPA",
            "MILPA es un entorno de desarrollo para "
            "programar y simular actividades agrícolas."
        )


# =========================================================
# INICIO
# =========================================================

def main():

    root = tk.Tk()
    MilpaIDE(root)
    root.mainloop()


if __name__ == "__main__":
    main()
