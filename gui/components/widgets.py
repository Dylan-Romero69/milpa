# =====================================================
# MILPA IDE - WIDGETS VISUALES
# =====================================================
#
# tk.Button ignora bg/fg en macOS y ttk.Notebook no permite pestañas
# compactas ni redondeadas, así que estos controles se dibujan sobre un
# Canvas. Solo cambian la apariencia: los comandos que reciben son los
# mismos callbacks de siempre y las pestañas delegan en el Notebook real.

import tkinter as tk
from tkinter import font as tkfont

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


_CACHE_FUENTES = {}


def _fuente(descripcion):
    clave = tuple(descripcion)
    if clave not in _CACHE_FUENTES:
        _CACHE_FUENTES[clave] = tkfont.Font(font=descripcion)
    return _CACHE_FUENTES[clave]


def medir(descripcion, texto):
    return _fuente(descripcion).measure(texto)


def alto_linea(descripcion):
    return _fuente(descripcion).metrics("linespace")


def rect_redondeado(canvas, x1, y1, x2, y2, radio, **opciones):
    """Dibuja un rectángulo con esquinas redondeadas (polígono suavizado)."""

    r = max(0, min(radio, (x2 - x1) / 2, (y2 - y1) / 2))
    puntos = (
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r,
        x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r,
        x1, y1,
    )
    return canvas.create_polygon(puntos, smooth=True, **opciones)


# =====================================================
# BOTÓN
# =====================================================

class Boton(tk.Canvas):

    VARIANTES = {
        "primario": {
            "fondo": COLORS["primary"],
            "hover": COLORS["primary_dark"],
            "presion": COLORS["primary_pressed"],
            "texto": COLORS["white"],
            "icono": COLORS["white"],
            "borde": "",
            "fuente": "button_bold",
        },
        "secundario": {
            "fondo": None,
            "hover": COLORS["hover"],
            "presion": COLORS["pressed"],
            "texto": COLORS["text"],
            "icono": COLORS["text_secondary"],
            "borde": "",
            "fuente": "button",
        },
        "contorno": {
            "fondo": COLORS["white"],
            "hover": COLORS["hover"],
            "presion": COLORS["pressed"],
            "texto": COLORS["text"],
            "icono": COLORS["text_secondary"],
            "borde": COLORS["border"],
            "fuente": "button",
        },
    }

    def __init__(
        self,
        parent,
        texto,
        comando,
        icono="",
        variante="secundario",
        radio=8,
        padx=11,
        pady=6
    ):

        self._fondo_padre = parent.cget("bg")

        super().__init__(
            parent,
            bg=self._fondo_padre,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=0
        )

        self.texto = texto
        self.icono = icono
        self.comando = comando
        self.estilo = self.VARIANTES[variante]
        self.radio = radio
        self.padx = padx
        self.pady = pady
        self._estado = "normal"

        self._dibujar()

        self.bind("<Enter>", lambda _e: self._cambiar("hover"))
        self.bind("<Leave>", lambda _e: self._cambiar("normal"))
        self.bind("<ButtonPress-1>", lambda _e: self._cambiar("presion"))
        self.bind("<ButtonRelease-1>", self._soltar)

    def _dibujar(self):

        fuente = FONTS[self.estilo["fuente"]]
        alto_texto = alto_linea(fuente)
        ancho_icono = alto_texto if self.icono else 0
        separacion = 7 if self.icono else 0

        ancho = (
            self.padx * 2 + ancho_icono + separacion
            + medir(fuente, self.texto)
        )
        alto = alto_texto + self.pady * 2

        self.configure(width=ancho, height=alto)
        self.delete("all")

        relleno = {
            "normal": self.estilo["fondo"],
            "hover": self.estilo["hover"],
            "presion": self.estilo["presion"],
        }[self._estado] or self._fondo_padre

        rect_redondeado(
            self, 0.5, 0.5, ancho - 0.5, alto - 0.5, self.radio,
            fill=relleno, outline=self.estilo["borde"]
        )

        x = self.padx
        if self.icono:
            self.create_text(
                x + ancho_icono / 2, alto / 2,
                text=self.icono,
                fill=self.estilo["icono"],
                font=FONTS["icon"]
            )
            x += ancho_icono + separacion

        self.create_text(
            x, alto / 2,
            text=self.texto,
            anchor="w",
            fill=self.estilo["texto"],
            font=fuente
        )

    def _cambiar(self, estado):
        self._estado = estado
        self._dibujar()

    def _soltar(self, evento):
        dentro = (
            0 <= evento.x <= self.winfo_width()
            and 0 <= evento.y <= self.winfo_height()
        )
        self._cambiar("hover" if dentro else "normal")
        if dentro and self.comando:
            self.comando()


# =====================================================
# ELEMENTO DE NAVEGACIÓN LATERAL
# =====================================================

class ItemNavegacion(tk.Canvas):

    def __init__(self, parent, icono, texto, comando, alto=34):

        self._fondo_padre = parent.cget("bg")

        super().__init__(
            parent,
            bg=self._fondo_padre,
            height=alto,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=0
        )

        self.icono = icono
        self.texto = texto
        self.comando = comando
        self.activo = False
        self._hover = False

        self.bind("<Configure>", lambda _e: self._dibujar())
        self.bind("<Enter>", lambda _e: self._marcar_hover(True))
        self.bind("<Leave>", lambda _e: self._marcar_hover(False))
        self.bind("<ButtonRelease-1>", self._soltar)

    def establecer_activo(self, activo):
        self.activo = activo
        self._dibujar()

    def _marcar_hover(self, valor):
        self._hover = valor
        self._dibujar()

    def _soltar(self, evento):
        if 0 <= evento.x <= self.winfo_width() and 0 <= evento.y <= self.winfo_height():
            self.comando()

    def _dibujar(self):

        ancho = self.winfo_width()
        alto = self.winfo_height()
        if ancho < 10:
            return

        self.delete("all")

        if self.activo:
            relleno = COLORS["green_light"]
        elif self._hover:
            relleno = COLORS["hover"]
        else:
            relleno = None

        if relleno:
            rect_redondeado(
                self, 0.5, 0.5, ancho - 0.5, alto - 0.5, 8,
                fill=relleno, outline=""
            )

        if self.activo:
            # Indicador vertical discreto a la izquierda
            rect_redondeado(
                self, 0, alto * 0.28, 3, alto * 0.72, 1.5,
                fill=COLORS["primary"], outline=""
            )

        caja_icono = 22
        self.create_text(
            14 + caja_icono / 2, alto / 2,
            text=self.icono,
            fill=COLORS["primary"] if self.activo else COLORS["text_secondary"],
            font=FONTS["icon"]
        )

        self.create_text(
            14 + caja_icono + 10, alto / 2,
            text=self.texto,
            anchor="w",
            fill=COLORS["primary_dark"] if self.activo else COLORS["text"],
            font=FONTS["sidebar_active"] if self.activo else FONTS["sidebar"]
        )


# =====================================================
# BARRA DE PESTAÑAS
# =====================================================

class BarraPestanas(tk.Canvas):
    """
    Pestañas dibujadas a mano que controlan un ttk.Notebook existente.

    El Notebook conserva sus páginas, select(), tabs() y el evento
    <<NotebookTabChanged>>; esta barra solo lo refleja y llama a
    notebook.select() al hacer clic.

    variante="segmentos": control segmentado compacto (vistas principales).
    variante="chips": pestañas tipo chip que se reparten en varias filas
    cuando no caben (fases del compilador).
    """

    def __init__(self, parent, notebook, variante="segmentos", bg=None):

        fondo = bg or parent.cget("bg")

        super().__init__(
            parent,
            bg=fondo,
            height=30,
            highlightthickness=0,
            bd=0,
            takefocus=0
        )

        self.notebook = notebook
        self.variante = variante
        self._fondo = fondo
        self._zonas = []
        self._hover = None

        self.notebook.bind(
            "<<NotebookTabChanged>>",
            lambda _e: self._dibujar(),
            add="+"
        )
        self.bind("<Configure>", lambda _e: self._dibujar())
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda _e: self._fijar_hover(None))
        self.bind("<ButtonRelease-1>", self._clic)

        self.after_idle(self._dibujar)

    # -------------------------------------------------

    def _pestanas(self):
        return [
            (pestana, self.notebook.tab(pestana, "text"))
            for pestana in self.notebook.tabs()
        ]

    def _zona_en(self, x, y):
        for x1, y1, x2, y2, pestana in self._zonas:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return pestana
        return None

    def _mover(self, evento):
        pestana = self._zona_en(evento.x, evento.y)
        self.configure(cursor="hand2" if pestana else "")
        self._fijar_hover(pestana)

    def _fijar_hover(self, pestana):
        if pestana != self._hover:
            self._hover = pestana
            self._dibujar()

    def _clic(self, evento):
        pestana = self._zona_en(evento.x, evento.y)
        if pestana and pestana != self.notebook.select():
            self.notebook.select(pestana)

    def _dibujar(self):
        if self.variante == "chips":
            self._dibujar_chips()
        else:
            self._dibujar_segmentos()

    # -------------------------------------------------

    def _dibujar_segmentos(self):

        fuente = FONTS["tab"]
        fuente_activa = FONTS["tab_active"]
        margen, padx = 3, 16
        alto_item = alto_linea(fuente) + 10
        alto = alto_item + margen * 2

        pestanas = self._pestanas()
        anchos = [medir(fuente_activa, texto) + padx * 2 for _p, texto in pestanas]
        ancho = sum(anchos) + margen * 2

        if self.winfo_reqwidth() != ancho or self.winfo_reqheight() != alto:
            self.configure(width=ancho, height=alto)

        self.delete("all")
        self._zonas = []

        rect_redondeado(
            self, 0, 0, ancho, alto, 9,
            fill=COLORS["track"], outline=""
        )

        actual = self.notebook.select()
        x = margen

        for (pestana, texto), ancho_item in zip(pestanas, anchos):

            x2 = x + ancho_item
            seleccionada = pestana == actual

            if seleccionada:
                rect_redondeado(
                    self, x, margen, x2, margen + alto_item, 7,
                    fill=COLORS["white"], outline=COLORS["border"]
                )

            if seleccionada:
                color = COLORS["primary"]
            elif pestana == self._hover:
                color = COLORS["text"]
            else:
                color = COLORS["text_secondary"]

            self.create_text(
                (x + x2) / 2, alto / 2,
                text=texto,
                fill=color,
                font=fuente_activa if seleccionada else fuente
            )

            self._zonas.append((x, margen, x2, margen + alto_item, pestana))
            x = x2

    def _dibujar_chips(self):

        fuente = FONTS["tab"]
        fuente_activa = FONTS["tab_active"]
        padx, separacion = 10, 4
        alto_item = alto_linea(fuente) + 10

        disponible = self.winfo_width()
        if disponible < 50:
            return

        self.delete("all")
        self._zonas = []

        actual = self.notebook.select()
        x, y = 0, 0

        for pestana, texto in self._pestanas():

            ancho_item = medir(fuente_activa, texto) + padx * 2

            if x > 0 and x + ancho_item > disponible:
                x = 0
                y += alto_item + separacion

            x2, y2 = x + ancho_item, y + alto_item
            seleccionada = pestana == actual

            if seleccionada:
                relleno = COLORS["green_light"]
            elif pestana == self._hover:
                relleno = COLORS["hover"]
            else:
                relleno = None

            if relleno:
                rect_redondeado(
                    self, x, y, x2, y2, 7,
                    fill=relleno, outline=""
                )

            self.create_text(
                (x + x2) / 2, (y + y2) / 2,
                text=texto,
                fill=COLORS["primary"] if seleccionada else COLORS["text_secondary"],
                font=fuente_activa if seleccionada else fuente
            )

            self._zonas.append((x, y, x2, y2, pestana))
            x = x2 + separacion

        alto_total = y + alto_item
        if self.winfo_reqheight() != alto_total:
            self.configure(height=alto_total)


# =====================================================
# AUXILIARES
# =====================================================

def separador(parent, orientacion="horizontal", color=None, **pack):
    """Línea de 1 px para separar zonas sin usar bordes pesados."""

    linea = tk.Frame(
        parent,
        bg=color or COLORS["border_soft"],
        height=1 if orientacion == "horizontal" else 18,
        width=1 if orientacion == "vertical" else 1
    )
    if pack:
        linea.pack(**pack)
    return linea
