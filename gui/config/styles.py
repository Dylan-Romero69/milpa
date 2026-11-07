
# =====================================================
# MILPA IDE - ESTILOS TKINTER
# =====================================================

from tkinter import ttk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


def configurar_estilos():

    style = ttk.Style()
    style.theme_use("clam")

    # -----------------------------------------------
    # PESTAÑAS
    # -----------------------------------------------

    style.configure(
        "TNotebook",
        background=COLORS["white"],
        borderwidth=0
    )

    style.configure(
        "TNotebook.Tab",
        background=COLORS["green_soft"],
        foreground=COLORS["text"],
        padding=(14, 9),
        font=FONTS["small"],
        borderwidth=0
    )

    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", COLORS["white"])
        ],
        foreground=[
            ("selected", COLORS["primary"])
        ]
    )

    # -----------------------------------------------
    # TABLAS
    # -----------------------------------------------

    style.configure(
        "Treeview",
        background=COLORS["white"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["white"],
        rowheight=30,
        font=FONTS["small"],
        borderwidth=0
    )

    style.configure(
        "Treeview.Heading",
        background=COLORS["green_light"],
        foreground=COLORS["primary_dark"],
        font=FONTS["small"],
        relief="flat"
    )

    style.map(
        "Treeview",
        background=[
            ("selected", COLORS["green_light"])
        ],
        foreground=[
            ("selected", COLORS["text"])
        ]
    )

    # -----------------------------------------------
    # SCROLLBAR
    # -----------------------------------------------

    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["green_light"],
        troughcolor=COLORS["white"],
        borderwidth=0,
        arrowsize=12
    )

    style.configure(
        "Horizontal.TScrollbar",
        background=COLORS["green_light"],
        troughcolor=COLORS["white"],
        borderwidth=0,
        arrowsize=12
    )

    return style
