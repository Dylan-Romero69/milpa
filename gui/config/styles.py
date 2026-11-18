# =====================================================
# MILPA IDE - ESTILOS TKINTER
# =====================================================
#
# Se usa el tema "clam" porque, a diferencia de "aqua", respeta colores,
# bordes y paddings en macOS. Sobre él se redefinen los layouts para
# quitar bordes gruesos, anillos de foco y flechas de las scrollbars.

from tkinter import font as tkfont
from tkinter import ttk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS, ajustar_fuentes


def configurar_estilos():

    style = ttk.Style()
    root = style.master

    ajustar_fuentes(root)
    style.theme_use("clam")

    # -----------------------------------------------
    # BASE
    # -----------------------------------------------

    style.configure(
        ".",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["normal"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["background"],
        darkcolor=COLORS["background"],
        troughcolor=COLORS["track"],
        focuscolor=COLORS["primary_light"],
        selectbackground=COLORS["selection"],
        selectforeground=COLORS["text"],
        insertcolor=COLORS["primary"],
        borderwidth=1,
        relief="flat"
    )

    style.configure("TFrame", background=COLORS["background"])
    style.configure(
        "TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"]
    )

    # -----------------------------------------------
    # PESTAÑAS
    # -----------------------------------------------

    style.configure(
        "TNotebook",
        background=COLORS["white"],
        borderwidth=0,
        tabmargins=(0, 0, 0, 0)
    )

    style.configure(
        "TNotebook.Tab",
        background=COLORS["white"],
        foreground=COLORS["text_secondary"],
        padding=(12, 5),
        font=FONTS["tab"],
        borderwidth=0,
        bordercolor=COLORS["white"],
        lightcolor=COLORS["white"],
        focuscolor=COLORS["white"]
    )

    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", COLORS["green_light"]),
            ("active", COLORS["hover"])
        ],
        foreground=[
            ("selected", COLORS["primary"])
        ]
    )

    # Notebook sin pestañas nativas ni borde: la barra de pestañas
    # se dibuja con BarraPestanas (gui/components/widgets.py) y el
    # notebook solo se encarga de mostrar la página seleccionada.
    style.layout("Plano.TNotebook", [
        ("Notebook.client", {"sticky": "nswe"})
    ])
    style.layout("Plano.TNotebook.Tab", [])
    style.configure(
        "Plano.TNotebook",
        background=COLORS["background"],
        borderwidth=0,
        padding=0
    )
    style.configure(
        "Tarjeta.TNotebook",
        background=COLORS["white"],
        borderwidth=0,
        padding=0
    )
    style.layout("Tarjeta.TNotebook", [
        ("Notebook.client", {"sticky": "nswe"})
    ])
    style.layout("Tarjeta.TNotebook.Tab", [])

    # -----------------------------------------------
    # BOTONES
    # -----------------------------------------------

    style.configure(
        "TButton",
        background=COLORS["white"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["white"],
        darkcolor=COLORS["white"],
        focuscolor=COLORS["white"],
        font=FONTS["button"],
        padding=(14, 6),
        relief="flat",
        anchor="center"
    )

    style.map(
        "TButton",
        background=[
            ("pressed", COLORS["pressed"]),
            ("active", COLORS["hover"])
        ],
        lightcolor=[
            ("pressed", COLORS["pressed"]),
            ("active", COLORS["hover"])
        ],
        darkcolor=[
            ("pressed", COLORS["pressed"]),
            ("active", COLORS["hover"])
        ],
        bordercolor=[
            ("focus", COLORS["primary_light"])
        ],
        relief=[("pressed", "flat")]
    )

    style.configure(
        "Accent.TButton",
        background=COLORS["primary"],
        foreground=COLORS["white"],
        bordercolor=COLORS["primary"],
        lightcolor=COLORS["primary"],
        darkcolor=COLORS["primary"],
        focuscolor=COLORS["primary"],
        font=FONTS["button_bold"]
    )

    style.map(
        "Accent.TButton",
        background=[
            ("pressed", COLORS["primary_pressed"]),
            ("active", COLORS["primary_dark"])
        ],
        lightcolor=[
            ("pressed", COLORS["primary_pressed"]),
            ("active", COLORS["primary_dark"])
        ],
        darkcolor=[
            ("pressed", COLORS["primary_pressed"]),
            ("active", COLORS["primary_dark"])
        ],
        bordercolor=[
            ("pressed", COLORS["primary_pressed"]),
            ("active", COLORS["primary_dark"])
        ],
        foreground=[("disabled", COLORS["green_light"])]
    )

    # Selector segmentado (herramientas del huerto)
    style.configure(
        "Segmento.Toolbutton",
        background=COLORS["white"],
        foreground=COLORS["text_secondary"],
        bordercolor=COLORS["white"],
        lightcolor=COLORS["white"],
        darkcolor=COLORS["white"],
        focuscolor=COLORS["white"],
        font=FONTS["button"],
        padding=(12, 5),
        relief="flat"
    )

    style.map(
        "Segmento.Toolbutton",
        background=[
            ("selected", COLORS["green_light"]),
            ("active", COLORS["hover"])
        ],
        lightcolor=[
            ("selected", COLORS["green_light"]),
            ("active", COLORS["hover"])
        ],
        darkcolor=[
            ("selected", COLORS["green_light"]),
            ("active", COLORS["hover"])
        ],
        bordercolor=[
            ("selected", COLORS["selection"]),
            ("active", COLORS["hover"])
        ],
        foreground=[
            ("selected", COLORS["primary"]),
            ("active", COLORS["text"])
        ],
        relief=[("selected", "flat"), ("pressed", "flat")]
    )

    # -----------------------------------------------
    # CAMPOS DE TEXTO
    # -----------------------------------------------

    for campo in ("TEntry", "TCombobox", "TSpinbox"):

        style.configure(
            campo,
            fieldbackground=COLORS["white"],
            background=COLORS["white"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["white"],
            darkcolor=COLORS["white"],
            arrowcolor=COLORS["text_secondary"],
            insertcolor=COLORS["primary"],
            padding=(8, 5)
        )

        style.map(
            campo,
            bordercolor=[("focus", COLORS["primary_light"])],
            lightcolor=[("focus", COLORS["green_light"])],
            darkcolor=[("focus", COLORS["green_light"])],
            fieldbackground=[("readonly", COLORS["white"])],
            background=[
                ("active", COLORS["hover"]),
                ("readonly", COLORS["white"])
            ],
            arrowcolor=[("active", COLORS["primary"])]
        )

    root.option_add("*TCombobox*Listbox.background", COLORS["white"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["green_light"])
    root.option_add("*TCombobox*Listbox.selectForeground", COLORS["primary_dark"])
    root.option_add("*TCombobox*Listbox.font", FONTS["normal"])
    root.option_add("*TCombobox*Listbox.relief", "flat")

    # -----------------------------------------------
    # TABLAS
    # -----------------------------------------------

    alto_fila = tkfont.Font(root=root, font=FONTS["small"]).metrics("linespace") + 12

    style.layout("Treeview", [
        ("Treeview.treearea", {"sticky": "nswe"})
    ])

    style.configure(
        "Treeview",
        background=COLORS["white"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["white"],
        rowheight=alto_fila,
        font=FONTS["small"],
        borderwidth=0,
        relief="flat",
        indent=18
    )

    style.map(
        "Treeview",
        background=[
            ("selected", COLORS["green_light"])
        ],
        foreground=[
            ("selected", COLORS["primary_dark"])
        ]
    )

    style.configure(
        "Treeview.Heading",
        background=COLORS["panel"],
        foreground=COLORS["text_secondary"],
        font=FONTS["label"],
        relief="flat",
        borderwidth=1,
        bordercolor=COLORS["border_soft"],
        lightcolor=COLORS["panel"],
        darkcolor=COLORS["border_soft"],
        padding=(10, 7)
    )

    style.map(
        "Treeview.Heading",
        background=[("active", COLORS["hover"])],
        lightcolor=[("active", COLORS["hover"])],
        relief=[("pressed", "flat")]
    )

    # -----------------------------------------------
    # SCROLLBAR (delgada y sin flechas)
    # -----------------------------------------------

    for orientacion, pegado in (("Vertical", "ns"), ("Horizontal", "ew")):

        nombre = f"{orientacion}.TScrollbar"

        style.layout(nombre, [
            (f"{orientacion}.Scrollbar.trough", {
                "sticky": pegado,
                "children": [
                    (f"{orientacion}.Scrollbar.thumb", {
                        "expand": "1",
                        "sticky": "nswe"
                    })
                ]
            })
        ])

        style.configure(
            nombre,
            background=COLORS["scroll_thumb"],
            troughcolor=COLORS["white"],
            bordercolor=COLORS["white"],
            lightcolor=COLORS["scroll_thumb"],
            darkcolor=COLORS["scroll_thumb"],
            gripcount=0,
            arrowsize=9,
            borderwidth=0,
            relief="flat"
        )

        style.map(
            nombre,
            background=[
                ("pressed", COLORS["scroll_thumb_hover"]),
                ("active", COLORS["scroll_thumb_hover"])
            ],
            lightcolor=[
                ("pressed", COLORS["scroll_thumb_hover"]),
                ("active", COLORS["scroll_thumb_hover"])
            ],
            darkcolor=[
                ("pressed", COLORS["scroll_thumb_hover"]),
                ("active", COLORS["scroll_thumb_hover"])
            ]
        )

    return style
