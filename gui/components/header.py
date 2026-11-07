
# =====================================================
# MILPA IDE - HEADER
# =====================================================

import tkinter as tk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


def crear_header(
    parent,
    on_save,
    on_open,
    on_run,
    on_clear,
    on_examples,
    on_help
):

    header = tk.Frame(
        parent,
        bg=COLORS["white"],
        height=105
    )

    header.pack(fill="x")
    header.pack_propagate(False)

    # -----------------------------------------------
    # IDENTIDAD DE MILPA
    # -----------------------------------------------

    logo = tk.Frame(
        header,
        bg=COLORS["white"]
    )

    logo.pack(side="left", padx=28)

    tk.Label(
        logo,
        text="◆ Milpa",
        bg=COLORS["white"],
        fg=COLORS["primary_dark"],
        font=FONTS["logo"]
    ).pack(side="left")

    tk.Label(
        logo,
        text="Programa, diseña y simula tu huerto",
        bg=COLORS["white"],
        fg="#423B32",
        font=FONTS["subtitle"]
    ).pack(side="left", padx=18, pady=(15, 0))

    # -----------------------------------------------
    # BOTONES
    # -----------------------------------------------

    acciones = tk.Frame(
        header,
        bg=COLORS["white"]
    )

    acciones.pack(
        side="right",
        padx=25,
        pady=20
    )

    _crear_boton(
        acciones,
        "▱\nAbrir",
        on_open
    )

    _crear_boton(
        acciones,
        "▣\nGuardar",
        on_save
    )

    _crear_boton(
        acciones,
        "▷\nEjecutar",
        on_run,
        principal=True
    )

    _crear_boton(
        acciones,
        "⌫\nLimpiar",
        on_clear
    )

    _crear_boton(
        acciones,
        "▤\nEjemplos",
        on_examples
    )

    _crear_boton(
        acciones,
        "? \nAyuda",
        on_help
    )

    return header


def _crear_boton(parent, texto, comando, principal=False):

    background = (
        COLORS["primary"]
        if principal
        else COLORS["white"]
    )

    foreground = (
        COLORS["white"]
        if principal
        else COLORS["text"]
    )

    boton = tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=background,
        fg=foreground,
        activebackground=COLORS["primary_light"],
        activeforeground=COLORS["white"],
        font=FONTS["button"],
        relief="flat",
        bd=0,
        padx=15,
        pady=7,
        cursor="hand2"
    )

    boton.pack(side="left", padx=3)

    return boton
