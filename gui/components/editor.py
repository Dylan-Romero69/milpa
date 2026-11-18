
# =====================================================
# MILPA IDE - EDITOR DE CODIGO
# =====================================================

import tkinter as tk
from tkinter import ttk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


class CodeEditor:

    def __init__(self, parent):

        self.frame = tk.Frame(
            parent,
            bg=COLORS["white"],
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["border"],
            highlightthickness=1
        )

        self._crear_interfaz()
        self._configurar_eventos()

    # -------------------------------------------------
    # INTERFAZ
    # -------------------------------------------------

    def _crear_interfaz(self):

        encabezado = tk.Frame(
            self.frame,
            bg=COLORS["white"],
            height=42
        )

        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text="</>",
            bg=COLORS["white"],
            fg=COLORS["primary"],
            font=FONTS["console"]
        ).pack(side="left", padx=(16, 8))

        tk.Label(
            encabezado,
            text="Editor de código",
            bg=COLORS["white"],
            fg=COLORS["text"],
            font=FONTS["heading"],
            anchor="w"
        ).pack(side="left")

        tk.Label(
            encabezado,
            text=" .milpa ",
            bg=COLORS["green_light"],
            fg=COLORS["primary"],
            font=FONTS["tiny"]
        ).pack(side="right", padx=16)

        tk.Frame(
            self.frame,
            bg=COLORS["border_soft"],
            height=1
        ).pack(fill="x")

        contenido = tk.Frame(
            self.frame,
            bg=COLORS["white"]
        )

        contenido.pack(
            fill="both",
            expand=True
        )

        # Números de línea
        self.lineas = tk.Text(
            contenido,
            width=4,
            bg=COLORS["gutter"],
            fg=COLORS["gutter_text"],
            font=FONTS["editor"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            state="disabled",
            padx=10,
            pady=12,
            spacing1=2,
            spacing3=2,
            takefocus=0,
            cursor="arrow",
            wrap="none"
        )

        self.lineas.pack(side="left", fill="y")
        self.lineas.tag_configure("derecha", justify="right")

        # Separación sutil entre números y código
        tk.Frame(
            contenido,
            bg=COLORS["border_soft"],
            width=1
        ).pack(side="left", fill="y")

        # Scrollbar
        self.scroll = ttk.Scrollbar(
            contenido,
            orient="vertical",
            style="Vertical.TScrollbar"
        )

        self.scroll.pack(side="right", fill="y", padx=(0, 3), pady=4)

        # Editor
        self.text = tk.Text(
            contenido,
            bg=COLORS["editor"],
            fg=COLORS["code"],
            insertbackground=COLORS["primary"],
            insertwidth=2,
            selectbackground=COLORS["selection"],
            selectforeground=COLORS["text"],
            inactiveselectbackground=COLORS["green_light"],
            font=FONTS["editor"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=12,
            spacing1=2,
            spacing3=2,
            undo=True,
            wrap="none"
        )

        self.text.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.scroll.configure(command=self.text.yview)

        self.text.tag_configure(
            "linea_actual",
            background=COLORS["current_line"]
        )
        self.text.tag_raise("sel")

        self.text.configure(
            yscrollcommand=self._sincronizar_scroll
        )

        self.actualizar_lineas()

    # -------------------------------------------------
    # EVENTOS
    # -------------------------------------------------

    def _configurar_eventos(self):

        self.text.bind(
            "<KeyRelease>",
            lambda event: self.actualizar_lineas()
        )

        self.text.bind(
            "<MouseWheel>",
            lambda event: self.frame.after(
                10,
                self.actualizar_lineas
            )
        )

        self.text.bind(
            "<Button-1>",
            lambda event: self.frame.after(
                10,
                self.actualizar_lineas
            )
        )

        # Resaltado de la línea actual (solo visual)
        for evento in ("<KeyRelease>", "<ButtonRelease-1>", "<FocusIn>"):
            self.text.bind(
                evento,
                lambda event: self._resaltar_linea_actual(),
                add="+"
            )

    def _resaltar_linea_actual(self):

        self.text.tag_remove("linea_actual", "1.0", "end")
        self.text.tag_add(
            "linea_actual",
            "insert linestart",
            "insert lineend+1c"
        )

    # -------------------------------------------------
    # NUMEROS DE LINEA
    # -------------------------------------------------

    def actualizar_lineas(self):

        contenido = self.text.get("1.0", "end-1c")

        cantidad = contenido.count("\n") + 1

        self.lineas.configure(state="normal")
        self.lineas.delete("1.0", "end")

        numeros = "\n".join(
            str(i) for i in range(1, cantidad + 1)
        )

        self.lineas.insert("1.0", numeros, "derecha")

        self.lineas.configure(state="disabled")

        self.lineas.yview_moveto(
            self.text.yview()[0]
        )

    def _sincronizar_scroll(self, *args):

        self.scroll.set(*args)

        self.lineas.yview_moveto(
            self.text.yview()[0]
        )

    # -------------------------------------------------
    # OPERACIONES DEL EDITOR
    # -------------------------------------------------

    def obtener_codigo(self):

        return self.text.get("1.0", "end-1c")

    def establecer_codigo(self, codigo):

        self.text.delete("1.0", "end")
        self.text.insert("1.0", codigo)

        self.actualizar_lineas()

    def reemplazar_codigo(self, codigo):
        """
        Cambia solo la parte del texto que es distinta, para conservar el
        cursor, la posición de la vista y el historial de deshacer.
        """
        actual = self.obtener_codigo()
        if codigo == actual:
            return

        inicio = 0
        limite = min(len(actual), len(codigo))
        while inicio < limite and actual[inicio] == codigo[inicio]:
            inicio += 1

        fin_actual, fin_nuevo = len(actual), len(codigo)
        while (
            fin_actual > inicio and fin_nuevo > inicio
            and actual[fin_actual - 1] == codigo[fin_nuevo - 1]
        ):
            fin_actual -= 1
            fin_nuevo -= 1

        vista = self.text.yview()[0]
        # Borrar + insertar cuentan como un solo paso de deshacer.
        self.text.configure(autoseparators=False)
        self.text.edit_separator()
        self.text.delete(f"1.0 + {inicio} chars", f"1.0 + {fin_actual} chars")
        self.text.insert(f"1.0 + {inicio} chars", codigo[inicio:fin_nuevo])
        self.text.edit_separator()
        self.text.configure(autoseparators=True)
        self.text.yview_moveto(vista)

        self.actualizar_lineas()

    def limpiar(self):

        self.text.delete("1.0", "end")
        self.actualizar_lineas()

    def insertar(self, codigo):

        self.text.insert("insert", codigo)
        self.actualizar_lineas()

    def seleccionar_todo(self):

        self.text.tag_add("sel", "1.0", "end-1c")
        self.text.mark_set("insert", "1.0")
        self.text.see("insert")
