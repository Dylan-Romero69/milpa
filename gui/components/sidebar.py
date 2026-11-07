
# =====================================================
# MILPA IDE - SIDEBAR
# =====================================================

import tkinter as tk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


OPCIONES = [
    ("⌂", "Inicio"),
    ("＋", "Nuevo programa"),
    ("▧", "Ejemplos"),
    ("◉", "Simulador"),
    ("⌘", "Configuración"),
]


class Sidebar:

    def __init__(self, parent, on_navigate):

        self.parent = parent
        self.on_navigate = on_navigate

        self.frame = tk.Frame(
            parent,
            bg=COLORS["sidebar"],
            width=220
        )

        self.frame.pack(side="left", fill="y")
        self.frame.pack_propagate(False)

        self.buttons = {}

        self._crear_contenido()

    def _crear_contenido(self):

        tk.Label(
            self.frame,
            text="ESPACIO DE TRABAJO",
            bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
            font=("Aptos", 8, "bold"),
            anchor="w"
        ).pack(fill="x", padx=18, pady=(20, 12))

        for icono, nombre in OPCIONES:

            boton = tk.Button(
                self.frame,
                text=f"   {icono}     {nombre}",
                anchor="w",
                command=lambda n=nombre: self.navegar(n),
                bg=COLORS["primary"] if nombre == "Inicio"
                else COLORS["sidebar"],
                fg=COLORS["white"] if nombre == "Inicio"
                else COLORS["text"],
                activebackground=COLORS["green_light"],
                activeforeground=COLORS["primary"],
                font=FONTS["sidebar"],
                relief="flat",
                bd=0,
                padx=10,
                pady=13,
                cursor="hand2"
            )

            boton.pack(fill="x", padx=8, pady=3)

            self.buttons[nombre] = boton

        tk.Frame(
            self.frame,
            bg=COLORS["border"],
            height=1
        ).pack(fill="x", padx=15, pady=20)

        tk.Label(
            self.frame,
            text="MILPA\n\nCuidando tus cultivos\ncon tecnología",
            bg=COLORS["sidebar"],
            fg=COLORS["primary"],
            font=("Aptos", 12, "italic"),
            justify="center"
        ).pack(side="bottom", pady=30)

    def navegar(self, nombre):
        self.marcar_activo(nombre)
        self.on_navigate(nombre)

    def marcar_activo(self, nombre):
        for opcion, boton in self.buttons.items():
            seleccionado = opcion == nombre
            boton.configure(
                bg=COLORS["primary"] if seleccionado
                else COLORS["sidebar"],

                fg=COLORS["white"] if seleccionado
                else COLORS["text"]
            )
