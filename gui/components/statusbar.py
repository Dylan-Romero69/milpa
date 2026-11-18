
# =====================================================
# MILPA IDE - BARRA DE ESTADO
# =====================================================

import tkinter as tk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


class StatusBar:

    def __init__(self, parent):

        self.frame = tk.Frame(
            parent,
            bg=COLORS["white"],
            height=28
        )

        self.frame.pack(
            side="bottom",
            fill="x"
        )

        self.frame.pack_propagate(False)

        self.estado = tk.StringVar(
            value="MILPA listo"
        )

        self.posicion = tk.StringVar(
            value="Línea 1 | Columna 1"
        )

        self.lenguaje = tk.StringVar(
            value="MILPA | Python | MIPS32"
        )

        self._crear_interfaz()

    def _crear_interfaz(self):

        tk.Frame(
            self.frame,
            bg=COLORS["border"],
            height=1
        ).pack(side="top", fill="x")

        tk.Label(
            self.frame,
            text="●",
            bg=COLORS["white"],
            fg=COLORS["success"],
            font=FONTS["tiny"]
        ).pack(side="left", padx=(16, 6))

        tk.Label(
            self.frame,
            textvariable=self.estado,
            bg=COLORS["white"],
            fg=COLORS["text_secondary"],
            font=FONTS["tiny"]
        ).pack(side="left")

        tk.Label(
            self.frame,
            textvariable=self.posicion,
            bg=COLORS["white"],
            fg=COLORS["text_secondary"],
            font=FONTS["tiny"]
        ).pack(side="right", padx=(0, 16))

        tk.Frame(
            self.frame,
            bg=COLORS["border"],
            width=1
        ).pack(side="right", fill="y", pady=8, padx=12)

        tk.Label(
            self.frame,
            textvariable=self.lenguaje,
            bg=COLORS["white"],
            fg=COLORS["text_secondary"],
            font=FONTS["tiny"]
        ).pack(side="right")

    def actualizar_estado(self, mensaje):

        self.estado.set(mensaje)

    def actualizar_posicion(self, linea, columna):

        self.posicion.set(
            f"Línea {linea} | Columna {columna}"
        )

    def actualizar_lenguaje(self, mensaje):

        self.lenguaje.set(mensaje)
