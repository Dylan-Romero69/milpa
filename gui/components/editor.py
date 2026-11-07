
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
            bg=COLORS["green_light"],
            height=43
        )

        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text="  </>  Editor de código",
            bg=COLORS["green_light"],
            fg=COLORS["text"],
            font=FONTS["heading"],
            anchor="w"
        ).pack(fill="both", padx=8)

        contenido = tk.Frame(
            self.frame,
            bg=COLORS["white"]
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=5
        )

        # Números de línea
        self.lineas = tk.Text(
            contenido,
            width=4,
            bg="#F4F6F3",
            fg="#858D88",
            font=FONTS["editor"],
            relief="flat",
            state="disabled",
            padx=8,
            pady=10,
            takefocus=0,
            wrap="none"
        )

        self.lineas.pack(side="left", fill="y")

        # Editor
        self.text = tk.Text(
            contenido,
            bg=COLORS["editor"],
            fg=COLORS["code"],
            insertbackground=COLORS["primary"],
            selectbackground=COLORS["green_light"],
            font=FONTS["editor"],
            relief="flat",
            padx=10,
            pady=10,
            undo=True,
            wrap="none"
        )

        self.text.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar
        self.scroll = ttk.Scrollbar(
            contenido,
            orient="vertical",
            command=self.text.yview,
            style="Vertical.TScrollbar"
        )

        self.scroll.pack(side="right", fill="y")

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

        self.lineas.insert("1.0", numeros)

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
