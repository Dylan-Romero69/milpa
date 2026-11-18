# =====================================================
# MILPA IDE - SIDEBAR
# =====================================================

import tkinter as tk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS
from gui.components.widgets import ItemNavegacion


OPCIONES = [
    ("⌂", "Inicio"),
    ("+", "Nuevo programa"),
    ("▤", "Ejemplos"),
    ("❀", "Simulador"),
    ("⚙", "Configuración"),
]


class Sidebar:

    def __init__(self, parent, on_navigate):

        self.parent = parent
        self.on_navigate = on_navigate

        self.frame = tk.Frame(
            parent,
            bg=COLORS["sidebar"],
            width=216
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
            fg=COLORS["text_muted"],
            font=FONTS["label"],
            anchor="w"
        ).pack(fill="x", padx=22, pady=(20, 8))

        for icono, nombre in OPCIONES:

            boton = ItemNavegacion(
                self.frame,
                icono=icono,
                texto=nombre,
                comando=lambda n=nombre: self.navegar(n)
            )

            boton.pack(fill="x", padx=10, pady=1)

            self.buttons[nombre] = boton

        self.marcar_activo("Inicio")

        # Nota de identidad al pie, discreta
        pie = tk.Frame(self.frame, bg=COLORS["sidebar"])
        pie.pack(side="bottom", fill="x", padx=22, pady=20)

        tk.Frame(pie, bg=COLORS["border"], height=1).pack(fill="x", pady=(0, 14))

        tk.Label(
            pie,
            text="MILPA",
            bg=COLORS["sidebar"],
            fg=COLORS["primary"],
            font=FONTS["label"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            pie,
            text="Cuidando tus cultivos\ncon tecnología",
            bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
            font=FONTS["tiny"],
            justify="left",
            anchor="w"
        ).pack(fill="x", pady=(3, 0))

    def navegar(self, nombre):
        self.marcar_activo(nombre)
        self.on_navigate(nombre)

    def marcar_activo(self, nombre):
        for opcion, boton in self.buttons.items():
            boton.establecer_activo(opcion == nombre)
