"""
Dibujo gráfico del AST de MILPA en un tk.Canvas.

El árbol se recorre de forma genérica con vars(nodo): un atributo que es
otro nodo, o una lista de nodos, se dibuja como hijo; un str/int/float/bool
se muestra como dato dentro del óvalo.

El acomodo usa contornos por nivel: cada subárbol guarda el extremo izquierdo
y derecho que ocupa en cada profundidad, y el siguiente hermano se recorre
lo justo para no tocarlo. Así ningún óvalo ni etiqueta se enciman, aunque un
padre sea más ancho que sus hijos.

Uso:
    canvas = crear_vista_arbol(marco)
    dibujar_arbol(canvas, arbol)                 # dibuja el AST
    dibujar_arbol(canvas, None, "Sin árbol")     # muestra un mensaje
"""

import sys
import tkinter as tk
from tkinter import font as tkfont

from gui.config.colors import COLORS
from gui.config.fonts import FONTS

ES_MAC = sys.platform == "darwin"

# Atributos que no forman parte del árbol: posición en el código y las
# anotaciones que el semántico agrega después (tipo_sem, val_const, magnitud).
IGNORADOS = {"linea", "columna", "tipo_sem", "val_const", "magnitud"}

# Nombres de las aristas de una operación binaria.
ARISTAS_BINARIAS = {"izquierda": "izq", "derecha": "der"}

# Relleno suave por tipo de nodo.
RELLENOS = {
    "Programa": "#E3ECFA",
    "DeclaracionVariable": "#E4F4E4",
    "DeclaracionConstante": "#D9F0EA",
    "DeclaracionZona": "#F6EBD9",
    "CampoZona": "#FBF3E4",
    "Asignacion": "#E8F6D8",
    "Condicional": "#FBE3E3",
    "CicloMientras": "#EEE3F8",
    "CicloParaCada": "#F3E1F1",
    "LlamadaFuncion": "#DDF1F6",
    "OperacionBinaria": "#FFF4CC",
    "OperacionUnaria": "#FFEBCC",
    "Literal": "#F1F1F1",
    "Identificador": "#E6EEF7",
    "AccesoCampo": "#E9E7F7",
}
RELLENO_POR_DEFECTO = "#EFEFEF"

# Medidas base (en píxeles, antes del zoom).
SEPARACION_X = 18           # espacio mínimo entre subárboles vecinos
SEPARACION_Y = 70           # espacio vertical entre niveles
MARGEN = 40                 # margen alrededor del árbol
ETIQUETA_SOBRE_HIJO = 16    # distancia del centro de la etiqueta al nivel del hijo

ZOOM_MIN = 0.4
ZOOM_MAX = 2.5
PASO_ZOOM = 1.15


# =========================================================
# RECORRIDO GENÉRICO DEL AST
# =========================================================

def es_nodo(valor):
    return hasattr(valor, "__dict__") and not isinstance(valor, type)


def es_dato(valor):
    return isinstance(valor, (str, int, float, bool))


def formatear_valor(valor):
    if isinstance(valor, bool):
        return "verdadero" if valor else "falso"
    if isinstance(valor, str):
        return f'"{valor}"'
    return str(valor)


def describir(nodo):
    """Devuelve (lineas_de_texto, es_operador, [(etiqueta, hijo), ...])."""
    clase = type(nodo).__name__
    atributos = {k: v for k, v in vars(nodo).items() if k not in IGNORADOS}

    hijos = []
    datos = []
    for nombre, valor in atributos.items():
        if es_nodo(valor):
            hijos.append((ARISTAS_BINARIAS.get(nombre, nombre), valor))
        elif isinstance(valor, list) and any(es_nodo(v) for v in valor):
            hijos.extend((nombre, v) for v in valor if es_nodo(v))
        elif isinstance(valor, list) and valor:
            datos.append(f"{nombre}: [{', '.join(str(v) for v in valor)}]")
        elif es_dato(valor) and valor != "":
            datos.append(f"{nombre}: {valor}")

    if clase in ("OperacionBinaria", "OperacionUnaria"):
        operador = atributos.get("operador", "?")
        return [str(operador)], True, hijos
    if clase == "Identificador":
        return [str(atributos.get("nombre", ""))], False, hijos
    if clase == "Literal":
        valor = atributos.get("valor")
        texto = formatear_valor(valor)
        return [texto, f"({atributos.get('tipo', '')})"], False, hijos
    return [clase] + datos, False, hijos


# =========================================================
# MEDIDAS Y ACOMODO
# =========================================================

class Fuentes:
    """Fuentes del dibujo escaladas al zoom actual."""

    def __init__(self, canvas, zoom):
        familia = FONTS["normal"][0]
        base = FONTS["normal"][1]

        def fuente(factor, peso="normal"):
            tamaño = max(6, round(base * factor * zoom))
            return tkfont.Font(root=canvas, family=familia, size=tamaño, weight=peso)

        self.titulo = fuente(1.0, "bold")
        self.dato = fuente(0.92)
        self.operador = fuente(1.7, "bold")
        self.etiqueta = fuente(0.78)


class NodoDibujo:
    """Datos de un nodo ya medido y acomodado."""

    def __init__(self, nodo, etiqueta, fuentes, zoom):
        self.nodo = nodo
        self.clase = type(nodo).__name__
        self.etiqueta = etiqueta
        lineas, self.es_operador, hijos = describir(nodo)
        self.hijos = [NodoDibujo(h, e, fuentes, zoom) for e, h in hijos]

        # Cada línea con su fuente: la primera de los nodos compuestos va en negrita.
        self.lineas = []
        for i, linea in enumerate(lineas):
            if self.es_operador:
                f = fuentes.operador
            elif i == 0 and self.clase not in ("Literal", "Identificador"):
                f = fuentes.titulo
            elif i == 0:
                f = fuentes.titulo if self.clase == "Identificador" else fuentes.dato
            else:
                f = fuentes.dato
            self.lineas.append((linea, f))

        ancho_texto = max(f.measure(t) for t, f in self.lineas)
        alto_texto = sum(f.metrics("linespace") for _, f in self.lineas)

        # Una elipse con semiejes (w/2)·√2 y (h/2)·√2 contiene el rectángulo w×h.
        self.ancho = ancho_texto * 1.42 + 16 * zoom
        self.alto = alto_texto * 1.42 + 10 * zoom
        # Nunca más angosto que alto: los textos cortos quedan en un círculo.
        self.ancho = max(self.ancho, self.alto)
        if self.es_operador:
            self.alto = self.ancho

        self.ancho_etiqueta = fuentes.etiqueta.measure(etiqueta) + 8 * zoom if etiqueta else 0
        self.alto_etiqueta = fuentes.etiqueta.metrics("linespace") + 2 * zoom
        self.x = 0.0
        self.y = 0.0
        self.profundidad = 0


def ancho_efectivo(nodo, proporcion_etiqueta):
    """
    Ancho que reserva un nodo en su nivel.

    La etiqueta de la arista queda un poco arriba del hijo, sobre la línea;
    entre dos hermanos la separación ahí es (1 - p) veces la de sus centros,
    así que el hueco del nodo se agranda en esa proporción.
    """
    return max(nodo.ancho, nodo.ancho_etiqueta / (1 - proporcion_etiqueta))


def acomodar(nodo, separacion, proporcion):
    """
    Acomoda el subárbol con el nodo en x = 0.
    Devuelve su contorno: [(izquierda, derecha)] por profundidad relativa.
    """
    medio = ancho_efectivo(nodo, proporcion) / 2
    if not nodo.hijos:
        return [(-medio, medio)]

    contorno_hijos = None
    for hijo in nodo.hijos:
        contorno = acomodar(hijo, separacion, proporcion)
        if contorno_hijos is None:
            contorno_hijos = contorno
            continue
        # Recorre al hijo lo justo para que no toque ningún nivel en común.
        desplazamiento = max(
            der + separacion - izq
            for (_, der), (izq, _) in zip(contorno_hijos, contorno)
        )
        mover(hijo, desplazamiento)
        contorno = [(i + desplazamiento, d + desplazamiento) for i, d in contorno]
        contorno_hijos = [
            (min(a[0], b[0]), max(a[1], b[1])) for a, b in zip(contorno_hijos, contorno)
        ] + contorno_hijos[len(contorno):] + contorno[len(contorno_hijos):]

    # El padre queda centrado sobre el primer y el último hijo.
    centro = (nodo.hijos[0].x + nodo.hijos[-1].x) / 2
    for hijo in nodo.hijos:
        mover(hijo, -centro)
    contorno_hijos = [(i - centro, d - centro) for i, d in contorno_hijos]
    return [(-medio, medio)] + contorno_hijos


def mover(nodo, dx):
    nodo.x += dx
    for hijo in nodo.hijos:
        mover(hijo, dx)


def recorrer(nodo, profundidad=0):
    nodo.profundidad = profundidad
    yield nodo
    for hijo in nodo.hijos:
        yield from recorrer(hijo, profundidad + 1)


# =========================================================
# DIBUJO
# =========================================================

def dibujar_arbol(canvas, ast, mensaje=None):
    """Dibuja el AST en el canvas, o un mensaje si no hay árbol."""
    canvas._arbol_ast = ast
    canvas._arbol_mensaje = mensaje
    if not hasattr(canvas, "_arbol_zoom"):
        canvas._arbol_zoom = 1.0
    canvas.delete("all")

    if ast is None or not es_nodo(ast):
        _dibujar_mensaje(canvas, mensaje or "No hay árbol para mostrar.")
        return

    try:
        _dibujar(canvas, ast, canvas._arbol_zoom)
    except Exception as error:      # el dibujo nunca debe tumbar la interfaz
        canvas.delete("all")
        _dibujar_mensaje(canvas, f"No se pudo dibujar el árbol:\n{error}")


def _dibujar_mensaje(canvas, texto):
    canvas.update_idletasks()
    ancho = max(canvas.winfo_width(), 400)
    alto = max(canvas.winfo_height(), 300)
    canvas.create_text(
        ancho / 2, alto / 2, text=texto, justify="center", width=ancho - 60,
        fill=COLORS["text_secondary"] if "text_secondary" in COLORS else "#666666",
        font=FONTS["normal"], tags=("mensaje",),
    )
    canvas.configure(scrollregion=(0, 0, ancho, alto))
    canvas.xview_moveto(0)
    canvas.yview_moveto(0)


def _dibujar(canvas, ast, zoom):
    fuentes = Fuentes(canvas, zoom)
    raiz = NodoDibujo(ast, "", fuentes, zoom)
    nodos = list(recorrer(raiz))

    # Altura de cada nivel: todos los centros de un nivel quedan alineados.
    niveles = {}
    for n in nodos:
        niveles[n.profundidad] = max(niveles.get(n.profundidad, 0), n.alto)
    alto_etiqueta = raiz.alto_etiqueta
    separacion_y = SEPARACION_Y * zoom + alto_etiqueta
    tope = {}
    y = MARGEN * zoom
    for profundidad in sorted(niveles):
        tope[profundidad] = y
        y += niveles[profundidad] + separacion_y
    for n in nodos:
        n.y = tope[n.profundidad] + niveles[n.profundidad] / 2

    # Las aristas van de centro a centro, así todas las de un nivel tienen el
    # mismo alto y la etiqueta cae en la misma fracción de cada una. El acomodo
    # usa la fracción mayor para que ninguna etiqueta toque a la de al lado.
    distancia_etiqueta = ETIQUETA_SOBRE_HIJO * zoom + alto_etiqueta / 2
    centros = {p: tope[p] + niveles[p] / 2 for p in niveles}
    proporcion = max(
        [
            (centros[p] - (tope[p] - distancia_etiqueta)) / (centros[p] - centros[p - 1])
            for p in niveles if p > 0
        ],
        default=0.0,
    )
    acomodar(raiz, SEPARACION_X * zoom, proporcion)

    izquierda = min(n.x - ancho_efectivo(n, proporcion) / 2 for n in nodos)
    derecha = max(n.x + ancho_efectivo(n, proporcion) / 2 for n in nodos)
    mover(raiz, MARGEN * zoom - izquierda)
    ancho_total = derecha - izquierda + 2 * MARGEN * zoom
    alto_total = y - separacion_y + MARGEN * zoom

    # 1) Líneas (quedan detrás de todo).
    grosor = max(1, round(1.3 * zoom))
    etiquetas = []
    for padre in nodos:
        x0, y0 = padre.x, padre.y
        for hijo in padre.hijos:
            x1, y1 = hijo.x, hijo.y
            canvas.create_line(x0, y0, x1, y1, fill="#555555", width=grosor)
            if hijo.etiqueta:
                ye = tope[hijo.profundidad] - distancia_etiqueta
                t = (ye - y0) / (y1 - y0)
                etiquetas.append((x0 + (x1 - x0) * t, ye, hijo))

    # 2) Etiquetas de las aristas, con fondo blanco.
    for x, ye, hijo in etiquetas:
        medio = hijo.ancho_etiqueta / 2
        canvas.create_rectangle(
            x - medio, ye - hijo.alto_etiqueta / 2, x + medio, ye + hijo.alto_etiqueta / 2,
            fill="white", outline="",
        )
        canvas.create_text(x, ye, text=hijo.etiqueta, font=fuentes.etiqueta, fill="#444444")

    # 3) Óvalos y texto.
    for n in nodos:
        canvas.create_oval(
            n.x - n.ancho / 2, n.y - n.alto / 2, n.x + n.ancho / 2, n.y + n.alto / 2,
            fill=RELLENOS.get(n.clase, RELLENO_POR_DEFECTO), outline="black",
            width=grosor,
        )
        alto_texto = sum(f.metrics("linespace") for _, f in n.lineas)
        y = n.y - alto_texto / 2
        for texto, f in n.lineas:
            paso = f.metrics("linespace")
            canvas.create_text(n.x, y + paso / 2, text=texto, font=f, fill="black")
            y += paso

    canvas.configure(scrollregion=(0, 0, ancho_total, alto_total))
    canvas._arbol_fuentes = fuentes     # evita que Tk libere las fuentes


# =========================================================
# VISTA CON SCROLL, ARRASTRE Y ZOOM
# =========================================================

def crear_vista_arbol(padre):
    """Crea el canvas con barras de scroll y controles; devuelve el canvas."""
    contenedor = tk.Frame(padre, bg="white")
    contenedor.pack(fill="both", expand=True)
    contenedor.rowconfigure(0, weight=1)
    contenedor.columnconfigure(0, weight=1)

    canvas = tk.Canvas(
        contenedor, bg="white", highlightthickness=0, bd=0,
        xscrollincrement=1, yscrollincrement=1,
    )
    barra_y = tk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    barra_x = tk.Scrollbar(contenedor, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=barra_x.set, yscrollcommand=barra_y.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    barra_y.grid(row=0, column=1, sticky="ns")
    barra_x.grid(row=1, column=0, sticky="ew")

    canvas._arbol_zoom = 1.0
    canvas._arbol_ast = None
    canvas._arbol_mensaje = None

    # Controles de zoom flotando en la esquina superior derecha.
    controles = tk.Frame(contenedor, bg="white", highlightbackground="#CCCCCC",
                         highlightthickness=1)
    for texto, factor in (("−", 1 / PASO_ZOOM), ("1:1", None), ("+", PASO_ZOOM)):
        etiqueta = tk.Label(controles, text=texto, bg="white", fg="#333333",
                            font=FONTS["button_bold"], padx=8, pady=2, cursor="hand2")
        etiqueta.pack(side="left")
        etiqueta.bind("<Button-1>", lambda _e, f=factor: _zoom(canvas, f))
    controles.place(relx=1.0, x=-24, y=8, anchor="ne")

    # Arrastrar con el mouse.
    canvas.bind("<ButtonPress-1>", lambda e: canvas.scan_mark(e.x, e.y))
    canvas.bind("<B1-Motion>", lambda e: canvas.scan_dragto(e.x, e.y, gain=1))

    # Rueda / trackpad.
    canvas.bind("<MouseWheel>", lambda e: _desplazar(canvas, e, "y"))
    canvas.bind("<Shift-MouseWheel>", lambda e: _desplazar(canvas, e, "x"))
    canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-40, "units"))
    canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(40, "units"))
    canvas.bind("<Shift-Button-4>", lambda e: canvas.xview_scroll(-40, "units"))
    canvas.bind("<Shift-Button-5>", lambda e: canvas.xview_scroll(40, "units"))
    canvas.bind("<Control-MouseWheel>", lambda e: _zoom_rueda(canvas, e))
    canvas.bind("<Control-Button-4>", lambda e: _zoom(canvas, PASO_ZOOM, e))
    canvas.bind("<Control-Button-5>", lambda e: _zoom(canvas, 1 / PASO_ZOOM, e))
    if ES_MAC:
        canvas.bind("<Command-MouseWheel>", lambda e: _zoom_rueda(canvas, e))
    # Tk 9 manda los gestos del trackpad como <TouchpadScroll>.
    try:
        canvas.bind("<TouchpadScroll>", lambda e: _touchpad(canvas, e))
    except tk.TclError:
        pass

    # El mensaje se mantiene centrado al cambiar el tamaño.
    canvas.bind("<Configure>", lambda _e: _recentrar_mensaje(canvas))
    return canvas


def _pasos_rueda(evento):
    if abs(evento.delta) >= 120:        # Windows: múltiplos de 120
        return evento.delta / 120 * 40
    return evento.delta * 8             # macOS: valores pequeños y continuos


def _desplazar(canvas, evento, eje):
    pasos = int(-_pasos_rueda(evento)) or (-1 if evento.delta > 0 else 1)
    (canvas.yview_scroll if eje == "y" else canvas.xview_scroll)(pasos, "units")


def _touchpad(canvas, evento):
    # delta empaqueta dx (16 bits altos) y dy (16 bits bajos), con signo.
    dx = (evento.delta >> 16) & 0xFFFF
    dy = evento.delta & 0xFFFF
    dx = dx - 0x10000 if dx & 0x8000 else dx
    dy = dy - 0x10000 if dy & 0x8000 else dy
    if evento.state & 0x4 or (ES_MAC and evento.state & 0x8):
        if dy:
            _zoom(canvas, PASO_ZOOM if dy > 0 else 1 / PASO_ZOOM, evento)
        return
    if dx:
        canvas.xview_scroll(-dx, "units")
    if dy:
        canvas.yview_scroll(-dy, "units")


def _zoom_rueda(canvas, evento):
    _zoom(canvas, PASO_ZOOM if evento.delta > 0 else 1 / PASO_ZOOM, evento)
    return "break"


def _zoom(canvas, factor, evento=None):
    """Cambia el zoom y redibuja; conserva el punto bajo el cursor."""
    if canvas._arbol_ast is None:
        return
    anterior = canvas._arbol_zoom
    nuevo = 1.0 if factor is None else min(ZOOM_MAX, max(ZOOM_MIN, anterior * factor))
    if nuevo == anterior:
        return

    if evento is not None and hasattr(evento, "x"):
        px, py = evento.x, evento.y
    else:
        px, py = canvas.winfo_width() / 2, canvas.winfo_height() / 2
    cx, cy = canvas.canvasx(px), canvas.canvasy(py)

    canvas._arbol_zoom = nuevo
    dibujar_arbol(canvas, canvas._arbol_ast, canvas._arbol_mensaje)

    region = canvas.cget("scrollregion").split()
    if len(region) == 4:
        ancho, alto = float(region[2]), float(region[3])
        razon = nuevo / anterior
        if ancho > 0:
            canvas.xview_moveto((cx * razon - px) / ancho)
        if alto > 0:
            canvas.yview_moveto((cy * razon - py) / alto)


def _recentrar_mensaje(canvas):
    if canvas._arbol_ast is None and canvas.find_withtag("mensaje"):
        dibujar_arbol(canvas, None, canvas._arbol_mensaje)
