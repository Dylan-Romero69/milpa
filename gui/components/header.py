# =====================================================
# MILPA IDE - HEADER
# =====================================================

import tkinter as tk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS
from gui.components.widgets import Boton, rect_redondeado, separador


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
        bg=COLORS["white"]
    )

    header.pack(fill="both", expand=True)

    # Línea inferior sutil en lugar de un borde completo
    separador(header, color=COLORS["border"], side="bottom", fill="x")

    # -----------------------------------------------
    # IDENTIDAD DE MILPA
    # -----------------------------------------------

    logo = tk.Frame(
        header,
        bg=COLORS["white"]
    )

    logo.pack(side="left", padx=(18, 0))

    _crear_isotipo(logo).pack(side="left")

    tk.Label(
        logo,
        text="MILPA",
        bg=COLORS["white"],
        fg=COLORS["primary_dark"],
        font=FONTS["logo"]
    ).pack(side="left", padx=(10, 0))

    separador(
        logo, orientacion="vertical", color=COLORS["border"],
        side="left", padx=14
    )

    tk.Label(
        logo,
        text="Programa, diseña y simula tu huerto",
        bg=COLORS["white"],
        fg=COLORS["text_secondary"],
        font=FONTS["subtitle"]
    ).pack(side="left")

    # -----------------------------------------------
    # BOTONES
    # -----------------------------------------------

    acciones = tk.Frame(
        header,
        bg=COLORS["white"]
    )

    acciones.pack(
        side="right",
        padx=(0, 16)
    )

    _crear_boton(acciones, "↥", "Abrir", on_open)
    _crear_boton(acciones, "↧", "Guardar", on_save)

    separador(
        acciones, orientacion="vertical", color=COLORS["border"],
        side="left", padx=8
    )

    _crear_boton(acciones, "⌫", "Limpiar", on_clear)
    _crear_boton(acciones, "▤", "Ejemplos", on_examples)
    _crear_boton(acciones, "?", "Ayuda", on_help)

    # Acción principal, separada y destacada
    _crear_boton(
        acciones, "▶", "Ejecutar", on_run, principal=True
    ).pack_configure(padx=(12, 0))

    return header


def _crear_boton(parent, icono, texto, comando, principal=False):

    boton = Boton(
        parent,
        texto=texto,
        icono=icono,
        comando=comando,
        variante="primario" if principal else "secundario",
        padx=14 if principal else 10
    )

    boton.pack(side="left", padx=1)

    return boton


def _crear_isotipo(parent, tamaño=30):
    """Brote verde dibujado en un cuadro redondeado: agricultura + tecnología."""

    lienzo = tk.Canvas(
        parent,
        width=tamaño,
        height=tamaño,
        bg=COLORS["white"],
        highlightthickness=0,
        bd=0
    )

    rect_redondeado(
        lienzo, 0, 0, tamaño, tamaño, 8,
        fill=COLORS["primary"], outline=""
    )

    centro = tamaño / 2
    lienzo.create_line(
        centro, tamaño * 0.78, centro, tamaño * 0.42,
        fill=COLORS["white"], width=2, capstyle="round"
    )
    lienzo.create_oval(
        centro - tamaño * 0.32, tamaño * 0.30,
        centro - tamaño * 0.02, tamaño * 0.50,
        fill=COLORS["white"], outline=""
    )
    lienzo.create_oval(
        centro + tamaño * 0.02, tamaño * 0.20,
        centro + tamaño * 0.32, tamaño * 0.40,
        fill="#BFE3CF", outline=""
    )

    return lienzo
