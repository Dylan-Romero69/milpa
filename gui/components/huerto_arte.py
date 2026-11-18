# =====================================================
# MILPA IDE - ILUSTRACIONES DEL HUERTO
# =====================================================
#
# Tk no muestra SVG sin librerías externas, así que los cultivos, la tierra
# y el agua se dibujan como vectores directamente en el Canvas. En macOS
# el Canvas se suaviza con CoreGraphics, por lo que escalan nítidos.
#
# Unidades: cada planta se dibuja desde su base (x, y) sobre el surco,
# creciendo hacia arriba, con "s" como unidad de tamaño (~media anchura).

import math
import random
import unicodedata

from gui.config.colors import COLORS
from gui.config.fonts import FONTS
from gui.components.widgets import alto_linea, medir, rect_redondeado


# =====================================================
# COLORES Y AUXILIARES
# =====================================================

FONDO_PRADO = "#E3EAD3"

PALETAS = {
    "saludable": {"hoja": "#46A253", "hoja2": "#2F7F3F", "tallo": "#3B7D34"},
    "seca": {"hoja": "#C3B152", "hoja2": "#A3913E", "tallo": "#8E8443"},
    "dañada": {"hoja": "#8D6E4A", "hoja2": "#6F533A", "tallo": "#6A563B"},
}

# Grados que se inclinan las hojas hacia abajo según el estado.
CAIDA = {"saludable": 0, "seca": 20, "dañada": 36}

COLOR_ESTADO = {
    "saludable": "#34A35F",
    "seca": "#E0A526",
    "dañada": "#D24B4B",
}


def mezclar(color1, color2, t):
    t = max(0.0, min(1.0, t))
    a = [int(color1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#{:02X}{:02X}{:02X}".format(
        *(round(x + (y - x) * t) for x, y in zip(a, b))
    )


def _paleta(estado):
    return PALETAS.get(estado, PALETAS["saludable"])


def _fruto(color, estado):
    if estado == "seca":
        return mezclar(color, "#CDBB8E", 0.45)
    if estado == "dañada":
        return mezclar(color, "#5B4232", 0.55)
    return color


def _borde(color, cantidad=0.22):
    return mezclar(color, "#000000", cantidad)


def _caer(angulo, estado):
    caida = CAIDA.get(estado, 0)
    if angulo < 90:
        return angulo - caida
    if angulo > 90:
        return angulo + caida
    return angulo


def _ancho(valor, minimo=1.0):
    return max(minimo, valor)


def ovalo(c, x, y, rx, ry, **opciones):
    return c.create_oval(x - rx, y - ry, x + rx, y + ry, **opciones)


def hoja(c, x, y, largo, angulo, ancho, color, nervio=True):
    """Hoja puntiaguda que nace en (x, y). 90° apunta hacia arriba."""

    a = math.radians(angulo)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    mx, my = x + dx * largo * 0.45, y + dy * largo * 0.45
    tx, ty = x + dx * largo, y + dy * largo

    c.create_polygon(
        x, y, x, y,
        mx + px * ancho, my + py * ancho,
        tx, ty, tx, ty,
        mx - px * ancho, my - py * ancho,
        smooth=True, fill=color, outline=""
    )

    if nervio and largo > 9:
        c.create_line(
            x, y, x + dx * largo * 0.8, y + dy * largo * 0.8,
            fill=mezclar(color, "#FFFFFF", 0.25), width=1
        )


def _normalizar(texto):
    sin_acentos = unicodedata.normalize("NFD", texto.lower())
    return "".join(ch for ch in sin_acentos if unicodedata.category(ch) != "Mn")


# =====================================================
# CULTIVOS
# =====================================================

def _tomate(c, x, y, s, est, _v):
    t = _paleta(est)
    c.create_line(
        x, y, x, y - 2.0 * s,
        fill=t["tallo"], width=_ancho(s * 0.14, 1.5), capstyle="round"
    )
    for i, (h, ang) in enumerate(((0.45, 150), (0.8, 30), (1.15, 155), (1.5, 25), (1.85, 135))):
        hoja(c, x, y - h * s, s * 0.8, _caer(ang, est), s * 0.28,
             t["hoja"] if i % 2 else t["hoja2"])

    rojo = _fruto("#E4432D", est)
    for fx, fy, r in ((-0.42, 0.85, 0.30), (0.45, 1.25, 0.28), (-0.15, 1.62, 0.24)):
        cx, cy, radio = x + fx * s, y - fy * s, r * s
        ovalo(c, cx, cy, radio, radio * 0.92, fill=rojo, outline=_borde(rojo))
        ovalo(c, cx - radio * 0.35, cy - radio * 0.35, radio * 0.28, radio * 0.2,
              fill=mezclar(rojo, "#FFFFFF", 0.5), outline="")
        c.create_line(cx - radio * 0.45, cy - radio * 0.85, cx + radio * 0.45,
                      cy - radio * 0.85, fill=t["hoja2"], width=_ancho(s * 0.08))


def _maiz(c, x, y, s, est, _v):
    t = _paleta(est)
    alto = 2.7 * s
    c.create_line(x, y, x, y - alto, fill=t["tallo"],
                  width=_ancho(s * 0.2, 2), capstyle="round")
    for h, ang in ((0.4, 160), (0.8, 20), (1.3, 155), (1.8, 28), (2.2, 150)):
        hoja(c, x, y - h * s, s * 1.3, _caer(ang, est), s * 0.16, t["hoja"])

    amarillo = _fruto("#F2C14E", est)
    cx, cy = x + s * 0.24, y - 1.45 * s
    ovalo(c, cx, cy, s * 0.2, s * 0.46, fill=amarillo, outline=_borde(amarillo, 0.25))
    for k in (-0.2, 0.05, 0.3):
        c.create_line(cx - s * 0.16, cy + k * s, cx + s * 0.16, cy + k * s,
                      fill=_borde(amarillo, 0.12), width=1)
    hoja(c, cx, cy + s * 0.45, s * 0.85, 78, s * 0.16, t["hoja2"], nervio=False)
    hoja(c, cx, cy + s * 0.45, s * 0.75, 100, s * 0.14, t["hoja"], nervio=False)

    espiga = _fruto("#D8B45C", est)
    for ang in (55, 75, 90, 105, 125):
        a = math.radians(ang)
        c.create_line(x, y - alto, x + math.cos(a) * s * 0.5,
                      y - alto - math.sin(a) * s * 0.5,
                      fill=espiga, width=_ancho(s * 0.07), capstyle="round")


def _frijol(c, x, y, s, est, _v):
    t = _paleta(est)
    alto = 2.3 * s
    c.create_line(x, y + 0.1 * s, x, y - alto, fill="#A07E57",
                  width=_ancho(s * 0.12, 1.5), capstyle="round")
    puntos = []
    for k in range(9):
        puntos += [x + math.sin(k * 1.4) * s * 0.22, y - k * alto / 8]
    c.create_line(puntos, smooth=True, fill=t["tallo"], width=_ancho(s * 0.08))
    for k, (h, ang) in enumerate(((0.5, 140), (0.9, 35), (1.35, 150), (1.75, 30), (2.1, 120))):
        hoja(c, x, y - h * s, s * 0.7, _caer(ang, est), s * 0.38,
             t["hoja"] if k % 2 else t["hoja2"])

    vaina = _fruto("#7CBF4A", est)
    for fx, fy in ((0.25, 1.1), (-0.3, 1.5), (0.3, 1.9)):
        x0, y0 = x + fx * s, y - fy * s
        c.create_line(x0, y0, x0 + fx * s * 0.6, y0 + s * 0.35,
                      x0 + fx * s * 0.45, y0 + s * 0.75, smooth=True,
                      fill=vaina, width=_ancho(s * 0.17, 2), capstyle="round")


def _calabaza(c, x, y, s, est, _v):
    t = _paleta(est)
    for ang, largo in ((160, 1.0), (20, 1.0), (125, 0.85), (55, 0.85), (92, 0.8)):
        hoja(c, x, y - 0.2 * s, s * largo, _caer(ang, est), s * 0.5,
             t["hoja2"] if ang == 92 else t["hoja"])
    naranja = _fruto("#EC8A2E", est)
    cx, cy = x, y - 0.32 * s
    for dx, rx in ((-0.34, 0.42), (0.34, 0.42), (0.0, 0.44)):
        ovalo(c, cx + dx * s, cy, rx * s, 0.4 * s, fill=naranja, outline=_borde(naranja))
    ovalo(c, cx - 0.2 * s, cy - 0.18 * s, 0.12 * s, 0.07 * s,
          fill=mezclar(naranja, "#FFFFFF", 0.4), outline="")
    c.create_line(cx, cy - 0.38 * s, cx + 0.1 * s, cy - 0.62 * s, fill="#6B4E2E",
                  width=_ancho(s * 0.14, 2), capstyle="round")


def _lechuga(c, x, y, s, est, _v):
    t = _paleta(est)
    externa = "#64B24C" if est == "saludable" else t["hoja"]
    interna = mezclar(externa, "#E8F5C8", 0.5)
    cy = y - 0.42 * s
    for k in range(7):
        a = math.radians(k * 360 / 7 + 10)
        ovalo(c, x + math.cos(a) * 0.42 * s, cy + math.sin(a) * 0.24 * s,
              0.42 * s, 0.32 * s, fill=externa, outline=_borde(externa, 0.18))
    for k in range(4):
        a = math.radians(k * 90 + 45)
        ovalo(c, x + math.cos(a) * 0.18 * s, cy - 0.06 * s + math.sin(a) * 0.12 * s,
              0.28 * s, 0.22 * s, fill=interna, outline=_borde(interna, 0.15))
    ovalo(c, x, cy - 0.08 * s, 0.2 * s, 0.16 * s,
          fill=mezclar(interna, "#FFFFFF", 0.3), outline=_borde(interna, 0.12))


def _raiz(c, x, y, s, est, variante):
    t = _paleta(est)
    color_base, redonda = variante
    for ang in (62, 76, 90, 104, 118):
        hoja(c, x, y - 0.15 * s, s * 1.25, _caer(ang, est), s * 0.12,
             t["hoja"], nervio=False)
    color = _fruto(color_base, est)
    if redonda:
        ovalo(c, x, y - 0.05 * s, 0.32 * s, 0.28 * s, fill=color, outline=_borde(color))
        c.create_line(x, y + 0.22 * s, x, y + 0.42 * s, fill=_borde(color), width=1)
    else:
        c.create_polygon(
            x - 0.26 * s, y - 0.2 * s, x + 0.26 * s, y - 0.2 * s,
            x + 0.08 * s, y + 0.3 * s, x, y + 0.46 * s, x - 0.08 * s, y + 0.3 * s,
            smooth=True, fill=color, outline=_borde(color)
        )
    ovalo(c, x - 0.1 * s, y - 0.1 * s, 0.07 * s, 0.05 * s,
          fill=mezclar(color, "#FFFFFF", 0.45), outline="")


def _chile(c, x, y, s, est, _v):
    t = _paleta(est)
    c.create_line(x, y, x, y - 1.6 * s, fill=t["tallo"],
                  width=_ancho(s * 0.13, 1.5), capstyle="round")
    for i, (h, ang) in enumerate(((0.5, 145), (0.8, 35), (1.1, 150), (1.4, 30), (1.6, 105))):
        hoja(c, x, y - h * s, s * 0.65, _caer(ang, est), s * 0.22,
             t["hoja"] if i % 2 else t["hoja2"])
    for fx, fy, color in ((-0.35, 1.05, "#D93A2B"), (0.38, 1.3, "#D93A2B"), (0.06, 0.8, "#3E9A3A")):
        x0, y0 = x + fx * s, y - fy * s
        fruto = _fruto(color, est)
        c.create_line(x0, y0, x0 + 0.06 * s, y0 + 0.35 * s, x0 - 0.08 * s, y0 + 0.62 * s,
                      smooth=True, fill=fruto, width=_ancho(s * 0.18, 2), capstyle="round")
        ovalo(c, x0, y0, 0.09 * s, 0.06 * s, fill=t["hoja2"], outline="")


def _fresa(c, x, y, s, est, _v):
    t = _paleta(est)
    for i, ang in enumerate((150, 112, 68, 30)):
        hoja(c, x, y - 0.1 * s, s * 0.85, _caer(ang, est), s * 0.36,
             t["hoja"] if i % 2 else t["hoja2"])
    if est != "dañada":
        fx, fy = x + 0.05 * s, y - 0.95 * s
        for k in range(5):
            a = math.radians(k * 72 + 90)
            ovalo(c, fx + math.cos(a) * 0.12 * s, fy - math.sin(a) * 0.12 * s,
                  0.1 * s, 0.1 * s, fill="#FFFFFF", outline="")
        ovalo(c, fx, fy, 0.06 * s, 0.06 * s, fill="#F4C542", outline="")

    roja = _fruto("#E0313F", est)
    for fx in (-0.45, 0.42):
        cx, cy, r = x + fx * s, y - 0.1 * s, 0.3 * s
        c.create_polygon(
            cx - r, cy - r * 0.55, cx - r * 0.2, cy - r * 0.9,
            cx + r * 0.2, cy - r * 0.9, cx + r, cy - r * 0.55,
            cx, cy + r * 1.05,
            smooth=True, fill=roja, outline=_borde(roja)
        )
        for sx, sy in ((-0.35, -0.3), (0.3, -0.25), (0.0, 0.0), (-0.15, 0.4), (0.2, 0.35)):
            ovalo(c, cx + sx * r, cy + sy * r, _ancho(s * 0.03, 0.7), _ancho(s * 0.03, 0.7),
                  fill="#F6D86B", outline="")
        hoja(c, cx, cy - r * 0.75, r * 0.7, 150, r * 0.25, t["hoja2"], nervio=False)
        hoja(c, cx, cy - r * 0.75, r * 0.7, 30, r * 0.25, t["hoja2"], nervio=False)


def _bulbo(c, x, y, s, est, color_bulbo):
    t = _paleta(est)
    caida = CAIDA.get(est, 0) / 40
    for ang, largo in ((78, 1.5), (92, 1.7), (106, 1.45)):
        a = math.radians(ang)
        x0, y0 = x, y - 0.45 * s
        x2 = x0 + math.cos(a) * largo * s + math.cos(a) * caida * s
        y2 = y0 - math.sin(a) * largo * s + caida * largo * s * 0.9
        xm = (x0 + x2) / 2
        ym = y0 - math.sin(a) * largo * s * 0.6
        c.create_line(x0, y0, xm, ym, x2, y2, smooth=True, fill=t["hoja"],
                      width=_ancho(s * 0.13, 1.5), capstyle="round")
    color = _fruto(color_bulbo, est)
    ovalo(c, x, y - 0.25 * s, 0.34 * s, 0.3 * s, fill=color, outline=_borde(color))
    ovalo(c, x - 0.12 * s, y - 0.33 * s, 0.08 * s, 0.1 * s,
          fill=mezclar(color, "#FFFFFF", 0.4), outline="")


def _papa(c, x, y, s, est, _v):
    t = _paleta(est)
    ovalo(c, x + 0.3 * s, y + 0.02 * s, 0.22 * s, 0.14 * s, fill="#C9A26B", outline="#9C7A4A")
    for k, ang in enumerate((165, 140, 115, 90, 65, 40, 15)):
        hoja(c, x, y - 0.25 * s, s * (0.75 if k % 2 else 0.95), _caer(ang, est),
             s * 0.3, t["hoja"] if k % 2 else t["hoja2"])
    if est != "dañada":
        for fx, fy in ((-0.32, 1.0), (0.26, 1.08), (-0.02, 1.25)):
            ovalo(c, x + fx * s, y - fy * s, 0.12 * s, 0.12 * s, fill="#F7F3FA", outline="")
            ovalo(c, x + fx * s, y - fy * s, 0.05 * s, 0.05 * s, fill="#F4C542", outline="")


def _melon(c, x, y, s, est, variante):
    t = _paleta(est)
    color_base, raya = variante
    for ang, largo in ((150, 0.8), (35, 0.85), (100, 0.7)):
        hoja(c, x, y - 0.15 * s, s * largo, _caer(ang, est), s * 0.42, t["hoja"])
    color = _fruto(color_base, est)
    cx, cy, rx, ry = x + 0.1 * s, y - 0.3 * s, 0.62 * s, 0.4 * s
    ovalo(c, cx, cy, rx, ry, fill=color, outline=_borde(color))
    if raya:
        raya = _fruto(raya, est)
        for k in (-0.55, -0.18, 0.18, 0.55):
            c.create_line(cx + k * rx, cy - ry * 0.92, cx + k * rx * 1.18, cy,
                          cx + k * rx, cy + ry * 0.92, smooth=True,
                          fill=raya, width=_ancho(s * 0.08))
    else:
        red = mezclar(color, "#FFFFFF", 0.35)
        for k in (-0.4, 0.0, 0.4):
            c.create_line(cx + k * rx - rx * 0.3, cy - ry * 0.7, cx + k * rx + rx * 0.3,
                          cy + ry * 0.7, fill=red, width=1)
    ovalo(c, cx - rx * 0.4, cy - ry * 0.45, rx * 0.25, ry * 0.15,
          fill=mezclar(color, "#FFFFFF", 0.35), outline="")


def _pepino(c, x, y, s, est, _v):
    t = _paleta(est)
    for ang, largo in ((150, 0.85), (40, 0.8), (105, 0.9)):
        hoja(c, x, y - 0.2 * s, s * largo, _caer(ang, est), s * 0.44, t["hoja"])
    verde = _fruto("#3F8F3C", est)
    c.create_line(x - 0.45 * s, y - 0.18 * s, x + 0.45 * s, y - 0.42 * s,
                  fill=verde, width=_ancho(s * 0.3, 3), capstyle="round")
    claro = mezclar(verde, "#FFFFFF", 0.4)
    for k in (-0.25, 0.05, 0.3):
        ovalo(c, x + k * s, y - 0.3 * s - k * 0.24 * s, 0.03 * s + 0.5, 0.03 * s + 0.5,
              fill=claro, outline="")
    if est != "dañada":
        ovalo(c, x + 0.58 * s, y - 0.48 * s, 0.11 * s, 0.11 * s, fill="#F4C542", outline="")


def _cabeza(c, x, y, s, est, tipo):
    t = _paleta(est)
    for ang, largo in ((160, 1.0), (20, 1.0), (130, 0.85), (50, 0.85)):
        hoja(c, x, y - 0.15 * s, s * largo, _caer(ang, est), s * 0.38, t["hoja2"])
    if tipo == "col":
        color = _fruto("#A8D27A", est)
        ovalo(c, x, y - 0.5 * s, 0.55 * s, 0.48 * s, fill=color, outline=_borde(color, 0.18))
        for dx in (-0.25, 0.25):
            c.create_arc(x + dx * s - 0.4 * s, y - 0.95 * s, x + dx * s + 0.4 * s,
                         y - 0.05 * s, start=60 if dx < 0 else 0, extent=60,
                         style="arc", outline=_borde(color, 0.15))
        return

    color = _fruto("#4F8F3A" if tipo == "brocoli" else "#F1ECD6", est)
    c.create_line(x, y, x, y - 0.5 * s, fill=_fruto("#8DBA6A", est),
                  width=_ancho(s * 0.22, 2), capstyle="round")
    for fx, fy in ((-0.32, 0.65), (0.32, 0.65), (0.0, 0.95), (-0.18, 0.8), (0.18, 0.82), (0.0, 0.7)):
        ovalo(c, x + fx * s, y - fy * s, 0.27 * s, 0.25 * s, fill=color, outline=_borde(color, 0.2))


def _girasol(c, x, y, s, est, _v):
    t = _paleta(est)
    alto = 2.5 * s
    c.create_line(x, y, x, y - alto, fill=t["tallo"],
                  width=_ancho(s * 0.16, 1.5), capstyle="round")
    hoja(c, x, y - 0.8 * s, s * 0.8, _caer(150, est), s * 0.38, t["hoja"])
    hoja(c, x, y - 1.3 * s, s * 0.8, _caer(30, est), s * 0.38, t["hoja2"])
    amarillo = _fruto("#F6C431", est)
    cy = y - alto
    for k in range(12):
        a = math.radians(k * 30)
        ovalo(c, x + math.cos(a) * 0.4 * s, cy + math.sin(a) * 0.4 * s,
              0.19 * s, 0.19 * s, fill=amarillo, outline=_borde(amarillo, 0.15))
    ovalo(c, x, cy, 0.3 * s, 0.3 * s, fill="#6B3F1F", outline="#4E2C14")


def _brote(c, x, y, s, est, _v):
    t = _paleta(est)
    c.create_line(x, y, x, y - 0.9 * s, fill=t["tallo"],
                  width=_ancho(s * 0.12, 1.5), capstyle="round")
    hoja(c, x, y - 0.8 * s, s * 0.6, _caer(150, est), s * 0.26, t["hoja"])
    hoja(c, x, y - 0.8 * s, s * 0.6, _caer(30, est), s * 0.26, t["hoja2"])


# (palabras clave, función, variante, plantas por surco, escala)
# El orden importa: las palabras más específicas van primero.
CULTIVOS = [
    (("jitomate", "tomate"), _tomate, None, 3, 1.0),
    (("maiz", "elote", "milpa"), _maiz, None, 3, 0.78),
    (("frijol", "ejote", "haba", "chicharo"), _frijol, None, 3, 0.85),
    (("calabacita", "pepino", "zucchini"), _pepino, None, 2, 1.1),
    (("calabaza",), _calabaza, None, 2, 1.1),
    (("lechuga", "espinaca", "acelga"), _lechuga, None, 3, 1.05),
    (("zanahoria",), _raiz, ("#EE7D2B", False), 3, 1.0),
    (("rabano",), _raiz, ("#D6455A", True), 3, 1.0),
    (("betabel", "remolacha"), _raiz, ("#7E2348", True), 3, 1.0),
    (("chile", "pimiento", "jalapeno"), _chile, None, 3, 1.0),
    (("fresa", "frutilla"), _fresa, None, 3, 1.0),
    (("ajo",), _bulbo, "#EFE9DA", 3, 1.0),
    (("cebolla", "puerro"), _bulbo, "#9B4F96", 3, 1.0),
    (("papa", "patata"), _papa, None, 3, 1.0),
    (("sandia",), _melon, ("#3F8F3A", "#24622A"), 2, 1.1),
    (("melon",), _melon, ("#D9C46C", None), 2, 1.1),
    (("brocoli",), _cabeza, "brocoli", 2, 1.1),
    (("coliflor",), _cabeza, "coliflor", 2, 1.1),
    (("col", "repollo"), _cabeza, "col", 2, 1.1),
    (("girasol",), _girasol, None, 3, 0.8),
]

# Sugerencias para el diálogo de "Configurar cultivo".
CULTIVOS_SUGERIDOS = [
    "tomate", "maíz", "frijol", "calabaza", "calabacita", "lechuga",
    "zanahoria", "rábano", "betabel", "chile", "fresa", "cebolla", "ajo",
    "papa", "sandía", "melón", "pepino", "brócoli", "coliflor", "col",
    "espinaca", "girasol",
]


def resolver_cultivo(nombre):
    clave = _normalizar(nombre)
    for palabras, funcion, variante, por_surco, escala in CULTIVOS:
        if any(palabra in clave for palabra in palabras):
            return funcion, variante, por_surco, escala
    return _brote, None, 3, 1.0


# =====================================================
# ESCENA
# =====================================================

def dibujar_fondo(c, ancho, alto):
    """Prado suave con matas de pasto (siempre en las mismas posiciones)."""

    rnd = random.Random(11)
    for _ in range(int(ancho * alto / 3200)):
        x, y = rnd.uniform(0, ancho), rnd.uniform(0, alto)
        h = rnd.uniform(3, 6)
        color = rnd.choice(("#CFDCB8", "#C6D5AD", "#D6E1C2"))
        c.create_line(x - 2, y, x - 3.5, y - h, fill=color, width=1)
        c.create_line(x, y, x, y - h - 1.5, fill=color, width=1)
        c.create_line(x + 2, y, x + 3.5, y - h, fill=color, width=1)


def dibujar_parcela_vacia(c, x1, y1, x2, y2, etiqueta, seleccionada):
    radio = min(x2 - x1, y2 - y1) * 0.1
    rect_redondeado(
        c, x1, y1, x2, y2, radio,
        fill="#DCE5CB", outline="#B5C49B", dash=(4, 3), width=1.2
    )
    c.create_text(x1 + 9, y1 + 8, text=etiqueta, anchor="nw",
                  fill="#8C9A78", font=FONTS["tiny"])
    cx, cy, brazo = (x1 + x2) / 2, (y1 + y2) / 2, min(x2 - x1, y2 - y1) * 0.07
    c.create_line(cx - brazo, cy, cx + brazo, cy, fill="#AFC092", width=2, capstyle="round")
    c.create_line(cx, cy - brazo, cx, cy + brazo, fill="#AFC092", width=2, capstyle="round")
    if seleccionada:
        _marcar_seleccion(c, x1, y1, x2, y2, radio)


def _marcar_seleccion(c, x1, y1, x2, y2, radio):
    rect_redondeado(
        c, x1 - 4, y1 - 4, x2 + 4, y2 + 4, radio + 4,
        fill="", outline=COLORS["primary"], width=2.5
    )


def _gota(c, x, y, r, color, **opciones):
    """Gota de agua con la punta hacia arriba."""

    c.create_polygon(
        x, y - r * 1.9, x, y - r * 1.9,
        x + r, y - r * 0.1, x + r * 0.7, y + r * 0.75,
        x, y + r, x - r * 0.7, y + r * 0.75, x - r, y - r * 0.1,
        smooth=True, fill=color, outline="", **opciones
    )


def dibujar_cama(c, x1, y1, x2, y2, parcela, etiqueta, seleccionada, semilla):
    """Cama de cultivo: marco de madera, tierra con surcos y plantas."""

    rnd = random.Random(semilla)
    ancho, alto = x2 - x1, y2 - y1
    radio = min(ancho, alto) * 0.1
    estado = parcela["estado"]
    humedad = parcela["humedad"] / 100

    # Sombra y marco de madera
    rect_redondeado(c, x1 + 1, y1 + 4, x2 + 1, y2 + 4, radio, fill="#C6D1AF", outline="")
    rect_redondeado(c, x1, y1, x2, y2, radio, fill="#A27A54", outline="#7D5A3C")

    riel = max(18, alto * 0.17)
    margen = max(5, min(ancho, alto) * 0.06)
    sx1, sy1, sx2, sy2 = x1 + margen, y1 + riel, x2 - margen, y2 - margen

    c.create_line(x1 + radio, y2 - margen / 2, x2 - radio, y2 - margen / 2,
                  fill="#B48C64", width=1)

    # Tierra: más clara si está seca, más oscura si está húmeda
    tierra = mezclar("#C9A57E", "#5B3A23", humedad)
    rect_redondeado(c, sx1, sy1, sx2, sy2, radio * 0.5,
                    fill=mezclar(tierra, "#000000", 0.14), outline="")

    cultivo = resolver_cultivo(parcela["cultivo"]) if parcela["cultivo"] else None
    surcos = 3
    paso = (sy2 - sy1) / surcos

    for i in range(surcos):
        cy = sy1 + paso * (i + 0.55)

        # Sombra del surco, lomo y brillo superior
        rect_redondeado(c, sx1 + 3, cy - paso * 0.12, sx2 - 3, cy + paso * 0.32,
                        paso * 0.22, fill=mezclar(tierra, "#000000", 0.28), outline="")
        rect_redondeado(c, sx1 + 3, cy - paso * 0.3, sx2 - 3, cy + paso * 0.2,
                        paso * 0.25, fill=mezclar(tierra, "#FFFFFF", 0.1), outline="")
        c.create_line(sx1 + paso * 0.35, cy - paso * 0.21, sx2 - paso * 0.35,
                      cy - paso * 0.21, fill=mezclar(tierra, "#FFFFFF", 0.24), width=1)

        # Piedritas y grumos de tierra
        for _ in range(5):
            px = rnd.uniform(sx1 + 7, sx2 - 7)
            py = rnd.uniform(cy - paso * 0.18, cy + paso * 0.12)
            ovalo(c, px, py, 1.3, 0.9, fill=mezclar(tierra, "#FFFFFF", 0.35), outline="")

        # Entre surcos: grietas si está seca, charcos si hay exceso de riego
        if i < surcos - 1:
            vy = cy + paso * 0.45
            if estado == "seca" or humedad < 0.25:
                x = rnd.uniform(sx1 + 6, sx1 + (sx2 - sx1) * 0.4)
                puntos = []
                for k in range(5):
                    puntos += [x + k * paso * 0.28, vy + (1.6 if k % 2 else -1.6)]
                c.create_line(puntos, fill=mezclar(tierra, "#000000", 0.4), width=1)
            if estado == "dañada":
                px = rnd.uniform(sx1 + paso, sx2 - paso)
                ovalo(c, px, vy, paso * 0.6, paso * 0.11, fill="#8DBBD6", outline="#6FA3C4")
                c.create_line(px - paso * 0.3, vy - 1, px, vy - 1, fill="#D4EAF5", width=1)

        # Plantas sembradas a lo largo del surco
        if cultivo:
            funcion, variante, por_surco, escala = cultivo
            s = paso * 0.47 * escala
            # En camas anchas cabe una planta más por surco.
            por_surco = max(por_surco, int((sx2 - sx1) / (s * 2.6)))
            for j in range(por_surco):
                px = sx1 + (sx2 - sx1) * (j + 0.5) / por_surco
                px += rnd.uniform(-1.5, 1.5)
                funcion(c, px, cy - paso * 0.05, s, estado, variante)

    _dibujar_rotulo(c, x1, y1, x2, riel, margen, parcela, etiqueta)

    if seleccionada:
        _marcar_seleccion(c, x1, y1, x2, y2, radio)


def _dibujar_rotulo(c, x1, y1, x2, riel, margen, parcela, etiqueta):
    """Letreros del marco: estado + cultivo a la izquierda, humedad a la derecha."""

    fuente = FONTS["tiny"]
    cy = y1 + riel / 2 + 1
    alto = alto_linea(fuente) + 2
    madera = "#7A573A"
    texto_color = "#FFF7EC"

    # Derecha: humedad
    porcentaje = "{}%".format(parcela["humedad"])
    der2 = x2 - margen + 2
    der1 = der2 - medir(fuente, porcentaje) - 12
    rect_redondeado(c, der1, cy - alto / 2, der2, cy + alto / 2, alto / 2,
                    fill=madera, outline="")
    c.create_text((der1 + der2) / 2, cy, text=porcentaje, fill="#CDEBFA", font=fuente)

    # Izquierda: punto de estado + cultivo (o la posición si aún no hay cultivo)
    con_estado = bool(parcela["cultivo"])
    texto = parcela["cultivo"].strip().capitalize() or etiqueta
    izq1 = x1 + margen - 2
    sangria = 15 if con_estado else 7
    disponible = der1 - 3 - izq1 - sangria - 6
    if medir(fuente, texto) > disponible:
        while len(texto) > 1 and medir(fuente, texto + "…") > disponible:
            texto = texto[:-1]
        texto += "…"
    rect_redondeado(c, izq1, cy - alto / 2, izq1 + sangria + medir(fuente, texto) + 7,
                    cy + alto / 2, alto / 2, fill=madera, outline="")
    if con_estado:
        color = COLOR_ESTADO.get(parcela["estado"], COLOR_ESTADO["saludable"])
        ovalo(c, izq1 + 8, cy, 3.2, 3.2, fill=color, outline="")
    c.create_text(izq1 + sangria, cy, text=texto, anchor="w", fill=texto_color, font=fuente)


# =====================================================
# ANIMACIÓN DE RIEGO
# =====================================================

class AnimacionRiego:
    """
    Una regadera se inclina sobre la parcela y deja caer gotas que forman
    ondas al tocar la tierra. Se dibuja encima de la escena con su propia
    etiqueta, así que sobrevive a los redibujados del huerto.
    """

    _contador = 0
    CUADROS = 40
    INTERVALO = 30

    def __init__(self, canvas, obtener_celda):
        AnimacionRiego._contador += 1
        self.tag = "riego_{}".format(AnimacionRiego._contador)
        self.canvas = canvas
        self.obtener_celda = obtener_celda
        self.cuadro = 0
        rnd = random.Random()
        self.gotas = [
            (rnd.uniform(5, 21), rnd.uniform(0.15, 0.9), rnd.uniform(0.35, 0.92))
            for _ in range(26)
        ]
        canvas.after(10, self._avanzar)

    def _avanzar(self):
        c = self.canvas
        try:
            c.delete(self.tag)
        except Exception:
            return
        celda = self.obtener_celda()
        if celda is None or self.cuadro > self.CUADROS:
            return

        x1, y1, x2, y2 = celda
        ancho, alto = x2 - x1, y2 - y1
        f = self.cuadro

        inclinacion = 38 * max(0, min(1, f / 6, (self.CUADROS - f) / 6))
        boquilla = self._regadera(x1 + ancho * 0.2, y1 + alto * 0.3, ancho * 0.16, inclinacion)

        for inicio, fx, fy in self.gotas:
            t = (f - inicio) / 9
            destino = (x1 + ancho * fx, y1 + alto * fy)
            if 0 <= t < 1:
                avance = t ** 1.4
                x = boquilla[0] + (destino[0] - boquilla[0]) * avance
                y = boquilla[1] + (destino[1] - boquilla[1]) * avance
                r = max(1.6, ancho * 0.022)
                _gota(c, x, y, r, "#4FA3D9", tags=self.tag)
                ovalo(c, x - r * 0.3, y - r * 0.3, r * 0.25, r * 0.35,
                      fill="#D9EEFA", outline="", tags=self.tag)
            elif 1 <= t < 1.9:
                k = (t - 1) / 0.9
                rx = ancho * (0.02 + 0.06 * k)
                ovalo(c, destino[0], destino[1], rx, rx * 0.4, fill="",
                      outline=mezclar("#BFE3F7", "#7A5A40", k), width=1.5, tags=self.tag)

        self.cuadro += 1
        c.after(self.INTERVALO, self._avanzar)

    def _regadera(self, cx, cy, u, angulo):
        """Dibuja la regadera girada y devuelve la posición de la boquilla."""

        a = math.radians(angulo)
        cos_a, sin_a = math.cos(a), math.sin(a)

        def girar(*puntos):
            resultado = []
            for i in range(0, len(puntos), 2):
                x, y = puntos[i] * u, puntos[i + 1] * u
                resultado += [cx + x * cos_a - y * sin_a, cy + x * sin_a + y * cos_a]
            return resultado

        verde, borde = "#2E8B68", "#1E6B4E"
        c = self.canvas
        c.create_line(girar(-0.42, -0.35, -0.55, -0.85, 0.1, -0.9, 0.22, -0.35),
                      smooth=True, fill=borde, width=max(2, u * 0.12),
                      capstyle="round", tags=self.tag)
        c.create_line(girar(0.3, 0.15, 1.05, -0.45), fill=verde,
                      width=max(2, u * 0.14), capstyle="round", tags=self.tag)
        c.create_polygon(girar(-0.5, -0.35, 0.35, -0.35, 0.45, 0.45, -0.6, 0.45),
                         fill=verde, outline=borde, tags=self.tag)
        c.create_line(girar(-0.52, -0.12, 0.38, -0.12), fill="#56B08A",
                      width=max(1, u * 0.08), tags=self.tag)
        rosa = girar(1.1, -0.5)
        ovalo(c, rosa[0], rosa[1], u * 0.13, u * 0.13, fill=borde, outline="", tags=self.tag)
        return rosa[0], rosa[1]
