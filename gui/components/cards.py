
# =====================================================
# MILPA IDE - TARJETAS REUTILIZABLES
# =====================================================

import tkinter as tk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


class Card:

    def __init__(self, parent, title, icon=""):

        self.frame = tk.Frame(
            parent,
            bg=COLORS["white"],
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["border"],
            highlightthickness=1
        )

        self.header = tk.Frame(
            self.frame,
            bg=COLORS["white"],
            height=44
        )

        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        if icon:
            tk.Label(
                self.header,
                text=icon,
                bg=COLORS["white"],
                fg=COLORS["primary"],
                font=FONTS["icon"]
            ).pack(side="left", padx=(16, 8))

        tk.Label(
            self.header,
            text=title,
            bg=COLORS["white"],
            fg=COLORS["text"],
            font=FONTS["heading"],
            anchor="w"
        ).pack(side="left", padx=(0 if icon else 16, 0))

        tk.Frame(
            self.frame,
            bg=COLORS["border_soft"],
            height=1
        ).pack(fill="x")

        self.body = tk.Frame(
            self.frame,
            bg=COLORS["white"]
        )

        self.body.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=8
        )

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def contenido(self):
        return self.body

    def destruir(self):
        self.frame.destroy()


def crear_tarjeta(
    parent,
    title,
    icon="",
    padding=10
):

    card = Card(parent, title, icon)

    card.body.configure(
        padx=padding,
        pady=padding
    )

    return card
