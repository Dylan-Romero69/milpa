# =====================================================
# MILPA IDE - TIPOGRAFÍAS
# =====================================================
#
# Los tamaños se definen en píxeles lógicos y ajustar_fuentes()
# los convierte a puntos según la escala real de Tk. Así la interfaz
# se ve igual en macOS (Tk 8.6 o Tk 9, Retina incluido), Windows y Linux.

import sys
from tkinter import font as tkfont

ES_MAC = sys.platform == "darwin"
ES_WINDOWS = sys.platform.startswith("win")

if ES_MAC:
    CANDIDATAS_UI = [".AppleSystemUIFont", "SF Pro Text", "Helvetica Neue"]
    CANDIDATAS_MONO = ["SF Mono", "JetBrains Mono", "Menlo", "Monaco"]
elif ES_WINDOWS:
    CANDIDATAS_UI = ["Segoe UI Variable Text", "Segoe UI"]
    CANDIDATAS_MONO = ["Cascadia Code", "Cascadia Mono", "Consolas"]
else:
    CANDIDATAS_UI = ["Inter", "Cantarell", "Ubuntu", "Noto Sans", "DejaVu Sans"]
    CANDIDATAS_MONO = ["JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono"]

# clave: (tamaño en píxeles lógicos, monoespaciada, estilos)
_ESPECIFICACION = {
    "logo": (16, False, ("bold",)),
    "title": (17, False, ("bold",)),
    "subtitle": (12, False, ()),
    "heading": (13, False, ("bold",)),
    "normal": (13, False, ()),
    "small": (12, False, ()),
    "tiny": (11, False, ()),
    "label": (10, False, ("bold",)),
    "button": (13, False, ()),
    "button_bold": (13, False, ("bold",)),
    "tab": (12, False, ()),
    "tab_active": (12, False, ("bold",)),
    "sidebar": (13, False, ()),
    "sidebar_active": (13, False, ("bold",)),
    "icon": (14, False, ()),
    "editor": (13, True, ()),
    "console": (12, True, ()),
    "terminal": (11, True, ()),
}


def _construir(familia_ui, familia_mono, factor):
    return {
        clave: (
            familia_mono if mono else familia_ui,
            max(6, int(pixeles * factor + 0.5)),
        ) + estilos
        for clave, (pixeles, mono, estilos) in _ESPECIFICACION.items()
    }


# Valores provisionales hasta que exista la ventana principal.
FONTS = _construir(CANDIDATAS_UI[-1], CANDIDATAS_MONO[-1], 0.75)


def _elegir_familia(root, candidatas, respaldo):
    instaladas = set(tkfont.families(root))
    for familia in candidatas:
        if familia.startswith("."):
            # Fuentes ocultas del sistema (San Francisco en macOS).
            prueba = tkfont.Font(root=root, family=familia, size=10)
            if prueba.actual("family") == familia:
                return familia
        elif familia in instaladas:
            return familia
    return tkfont.nametofont(respaldo, root=root).actual("family")


def ajustar_fuentes(root):
    """Elige las fuentes del sistema y adapta los tamaños a la pantalla."""

    familia_ui = _elegir_familia(root, CANDIDATAS_UI, "TkDefaultFont")
    familia_mono = _elegir_familia(root, CANDIDATAS_MONO, "TkFixedFont")

    if ES_MAC:
        # En macOS los puntos son lógicos: Tk 8.6 usa escala 1.0 y Tk 9 usa 1.33.
        factor = 1 / float(root.tk.call("tk", "scaling"))
    else:
        # En Windows/Linux los puntos ya escalan con los DPI del monitor.
        factor = 0.75

    FONTS.update(_construir(familia_ui, familia_mono, factor))
