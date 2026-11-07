
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from gui.config.colors import COLORS
from gui.config.fonts import FONTS
from gui.config.styles import configurar_estilos

from gui.components.header import crear_header
from gui.components.sidebar import Sidebar

from gui.components.editor import CodeEditor
from gui.components.console import ConsolePanel

from gui.components.statusbar import StatusBar

# =========================================================
# MILPA IDE - PALETA VISUAL
# =========================================================

C = {
    "fondo": COLORS["background"],
    "blanco": COLORS["white"],
    "verde": COLORS["primary"],
    "verde2": COLORS["primary_light"],
    "verde_claro": COLORS["green_light"],
    "verde_suave": COLORS["green_soft"],
    "texto": COLORS["text"],
    "gris": COLORS["text_secondary"],
    "borde": COLORS["border"],
    "editor": COLORS["editor"],
    "codigo": COLORS["code"],
    "azul": COLORS["info"],
    "naranja": COLORS["warning"],
    "rojo": COLORS["error"],
    "sombra": COLORS["shadow"],
}


class MilpaIDE:

    def __init__(self, root):
        self.root = root
        self.archivo_actual = None
        self.seccion_actual = "Inicio"

        self.root.title("MILPA | Programa tu huerto")
        self.root.geometry("1500x900")
        self.root.minsize(1100, 700)
        self.root.configure(bg=C["fondo"])

        self.configurar_estilos()
        self.crear_interfaz()
        self.actualizar_lineas()
        
        self.cargar_ejemplo()

    # =====================================================
    # ESTILOS
    # =====================================================

    def configurar_estilos(self):
        configurar_estilos()

    # =====================================================
    # ESTRUCTURA GENERAL
    # =====================================================

    def crear_interfaz(self):

        self.header = tk.Frame(
            self.root,
            bg=C["blanco"],
            height=105
        )
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.crear_encabezado()

        cuerpo = tk.Frame(self.root, bg=C["fondo"])
        cuerpo.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(
            cuerpo,
            bg="#F0F2E9",
            width=220
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.crear_sidebar()

        contenido = tk.Frame(cuerpo, bg=C["fondo"])
        contenido.pack(
            side="left",
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        self.crear_area_trabajo(contenido)
        self.crear_barra_estado()

    # =====================================================
    # ENCABEZADO
    # =====================================================

    def crear_encabezado(self):
        crear_header(
            self.header,
            on_save=self.guardar,
            on_run=self.compilar,
            on_clear=self.limpiar,
            on_examples=self.cargar_ejemplo,
            on_help=self.ayuda
        )

    def boton_header(self, padre, texto, comando, principal=False):

        bg = C["verde"] if principal else C["blanco"]
        fg = C["blanco"] if principal else C["texto"]

        tk.Button(
            padre,
            text=texto,
            command=comando,
            bg=bg,
            fg=fg,
            activebackground=C["verde2"],
            activeforeground=C["blanco"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=7,
            cursor="hand2"
        ).pack(side="left", padx=3)
        
    # =====================================================
    # BARRA DE ESTADO
    # =====================================================

    def crear_barra_estado(self):

        self.statusbar = StatusBar(self.root)

    # =====================================================
    # BARRA LATERAL
    # =====================================================

    def crear_sidebar(self):
        self.sidebar_component = Sidebar(
            self.sidebar,
            on_navigate=self.navegar
        )

    def navegar(self, nombre):

        self.seccion_actual = nombre

        self.mensaje(
            f"Sección seleccionada: {nombre}"
        )

    # =====================================================
    # AREA DE TRABAJO
    # =====================================================

    def crear_area_trabajo(self, padre):

        columnas = tk.PanedWindow(
            padre,
            orient="horizontal",
            bg=C["fondo"],
            sashwidth=6,
            bd=0
        )
        columnas.pack(fill="both", expand=True)

        izquierda = tk.Frame(columnas, bg=C["fondo"])
        derecha = tk.Frame(columnas, bg=C["fondo"])

        columnas.add(izquierda, minsize=400, width=560)
        columnas.add(derecha, minsize=450)

        self.crear_editor(izquierda)
        self.crear_consola(izquierda)

        self.crear_panel_fases(derecha)
        
        self.crear_registro(derecha)
        
    
    def crear_panel_fases(self, padre):

        tarjeta = self.tarjeta(
            padre,
            "Centro de análisis del compilador",
            "⚙"
        )
        tarjeta.pack(fill="both", expand=True)

        self.notebook_fases = ttk.Notebook(tarjeta)
        self.notebook_fases.pack(
            fill="both",
            expand=True,
            padx=7,
            pady=7
        )

        self.resultados = {}

        fases = [
            "Léxico",
            "Sintáctico",
            "AST",
            "Semántico",
            "Cuádruplos",
            "Optimización",
            "Registros",
            "MIPS",
            "Infija",
            "Prefija",
            "Postfija",
            "Simulador"
        ]

        for fase in fases:

            marco = tk.Frame(
                self.notebook_fases,
                bg=C["blanco"]
            )

            self.notebook_fases.add(
                marco,
                text=fase
            )

            if fase == "Léxico":
                self.crear_tabla_lexica(marco)

            else:
                texto = tk.Text(
                    marco,
                    bg=C["blanco"],
                    fg=C["codigo"],
                    font=("Consolas", 10),
                    relief="flat",
                    padx=12,
                    pady=12,
                    wrap="none"
                )

                texto.pack(
                    fill="both",
                    expand=True
                )

                texto.insert(
                    "1.0",
                    f"Esperando compilación...\n\n"
                    f"Los resultados de {fase} aparecerán aquí."
                )

                texto.configure(state="disabled")

                self.resultados[fase] = texto


    def crear_tabla_lexica(self, padre):

        contenedor = tk.Frame(
            padre,
            bg=C["blanco"]
        )
        contenedor.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        tk.Label(
            contenedor,
            text="Tabla de tokens generados",
            bg=C["blanco"],
            fg=C["verde"],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        columnas = (
            "numero",
            "tipo",
            "lexema",
            "linea",
            "columna"
        )

        tabla = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings"
        )

        encabezados = {
            "numero": "#",
            "tipo": "Tipo de token",
            "lexema": "Lexema",
            "linea": "Línea",
            "columna": "Columna"
        }

        anchos = {
            "numero": 40,
            "tipo": 150,
            "lexema": 140,
            "linea": 60,
            "columna": 70
        }

        for columna in columnas:

            tabla.heading(
                columna,
                text=encabezados[columna]
            )

            tabla.column(
                columna,
                width=anchos[columna],
                anchor="center"
            )

        tabla.pack(
            fill="both",
            expand=True
        )

        self.tabla_tokens = tabla
        self.resultados["Léxico"] = tabla


    def mostrar_texto_fase(self, fase, contenido):

        widget = self.resultados.get(fase)

        if not isinstance(widget, tk.Text):
            return

        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", str(contenido))
        widget.configure(state="disabled")


    def limpiar_resultados(self):

        for fase, widget in self.resultados.items():

            if fase == "Léxico":
                for elemento in widget.get_children():
                    widget.delete(elemento)

            elif isinstance(widget, tk.Text):
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.insert(
                    "1.0",
                    f"Esperando resultados de {fase}..."
                )
                widget.configure(state="disabled")


    # =====================================================
    # TARJETAS
    # =====================================================

    def tarjeta(self, padre, titulo, icono=""):

        contenedor = tk.Frame(
            padre,
            bg=C["blanco"],
            highlightbackground=C["borde"],
            highlightthickness=1
        )

        encabezado = tk.Frame(
            contenedor,
            bg=C["verde_claro"],
            height=43
        )
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text=f"  {icono}  {titulo}",
            bg=C["verde_claro"],
            fg=C["texto"],
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(fill="both", padx=8)

        return contenedor

    # =====================================================
    # EDITOR
    # =====================================================

    def crear_editor(self, padre):
        self.editor_component = CodeEditor(padre)
        self.editor_component.frame.pack(
            fill="both",
            expand=True,
            pady=(0, 10)
        )
        # Referencia compatible con el código anterior
        self.editor = self.editor_component.text

    def actualizar_lineas(self):
        self.editor_component.actualizar_lineas()

    def sincronizar_lineas(self):
        self.editor_component.actualizar_lineas()

    # =====================================================
    # CONSOLA
    # =====================================================

    def crear_consola(self, padre):
        self.console_component = ConsolePanel(padre)

        self.console_component.frame.pack(
            fill="both",
            expand=True
        )

        # Referencia compatible con el código anterior
        self.consola = self.console_component.consola

    def mensaje(self, texto, tipo="normal"):
        if not hasattr(self, "console_component"):
            return

        if tipo == "error":
            self.console_component.error(texto)

        elif tipo == "exito":
            self.console_component.exito(texto)

        elif tipo == "warning":
            self.console_component.advertencia(texto)

        else:
            self.console_component.mensaje(texto)

    # =====================================================
    # SIMULADOR
    # =====================================================

    def crear_simulador(self, padre):

        tarjeta = self.tarjeta(
            padre,
            "Simulación en tiempo real",
            "▶"
        )
        tarjeta.pack(fill="both", expand=True, pady=(0, 10))

        interior = tk.Frame(tarjeta, bg=C["blanco"])
        interior.pack(fill="both", expand=True, padx=10, pady=8)

        self.tabs_simulador = ttk.Notebook(interior)
        self.tabs_simulador.pack(fill="both", expand=True)

        general = tk.Frame(
            self.tabs_simulador,
            bg=C["blanco"]
        )

        sensores = tk.Frame(
            self.tabs_simulador,
            bg=C["blanco"]
        )

        actividades = tk.Frame(
            self.tabs_simulador,
            bg=C["blanco"]
        )

        self.tabs_simulador.add(general, text="Vista general")
        self.tabs_simulador.add(sensores, text="Sensores")
        self.tabs_simulador.add(actividades, text="Actividades")

        # Vista general
        huerto = tk.Frame(general, bg="#EAF4E4")
        huerto.pack(fill="both", expand=True, pady=8)

        tk.Label(
            huerto,
            text="🌳      🌱       🍅\n\n"
                 "      🪴  HUERTO NORTE  🪴\n\n"
                 "🍃      🌿       🌳",
            bg="#EAF4E4",
            fg=C["verde"],
            font=("Segoe UI", 18, "bold"),
            justify="center"
        ).pack(expand=True)

        self.crear_sensor(
            general,
            "💧",
            "Humedad del suelo",
            "35.0 %",
            C["azul"]
        )

        self.crear_sensor(
            general,
            "🌡",
            "Temperatura",
            "24.0 °C",
            C["naranja"]
        )

        self.crear_sensor(
            general,
            "🌧",
            "Lluvia",
            "No está lloviendo",
            C["azul"]
        )

        self.crear_sensor(
            general,
            "🌱",
            "Estado del cultivo",
            "Saludable",
            C["verde2"]
        )

        acciones = tk.Frame(general, bg=C["blanco"])
        acciones.pack(fill="x", pady=8)

        tk.Button(
            acciones,
            text="▶  Ejecutar simulación",
            command=self.ejecutar_simulacion,
            bg=C["verde"],
            fg=C["blanco"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=15,
            pady=10
        ).pack(side="left", padx=4)

        tk.Button(
            acciones,
            text="↻  Reiniciar",
            command=self.reiniciar_simulacion,
            bg=C["blanco"],
            fg=C["verde"],
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            bd=1,
            padx=15,
            pady=9
        ).pack(side="left", padx=4)

        # Pestaña sensores
        tk.Label(
            sensores,
            text="LECTURAS DE SENSORES",
            bg=C["blanco"],
            fg=C["verde"],
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=15, pady=15)

        for texto in [
            "Humedad del suelo: 35.0 %",
            "Temperatura: 24.0 °C",
            "Lluvia: No",
            "Estado: Saludable"
        ]:
            tk.Label(
                sensores,
                text="  •  " + texto,
                bg=C["blanco"],
                fg=C["texto"],
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=15, pady=8)

        # Pestaña actividades
        tk.Label(
            actividades,
            text="Las actividades de ejecución aparecerán aquí.",
            bg=C["blanco"],
            fg=C["gris"],
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=15, pady=20)

    def crear_sensor(self, padre, icono, titulo, valor, color):

        fila = tk.Frame(
            padre,
            bg=C["blanco"],
            highlightbackground=C["borde"],
            highlightthickness=1
        )
        fila.pack(fill="x", pady=3)

        tk.Label(
            fila,
            text=icono,
            bg=C["blanco"],
            fg=color,
            font=("Segoe UI", 19)
        ).pack(side="left", padx=12)

        datos = tk.Frame(fila, bg=C["blanco"])
        datos.pack(side="left", fill="x", expand=True, pady=7)

        tk.Label(
            datos,
            text=titulo,
            bg=C["blanco"],
            fg=C["gris"],
            font=("Segoe UI", 9)
        ).pack(anchor="w")

        tk.Label(
            datos,
            text=valor,
            bg=C["blanco"],
            fg=C["texto"],
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

    # =====================================================
    # REGISTRO DE EJECUCION
    # =====================================================

    def crear_registro(self, padre):

        tarjeta = self.tarjeta(
            padre,
            "Registro de ejecución",
            "☷"
        )
        tarjeta.pack(fill="both", expand=True)

        self.registro = tk.Text(
            tarjeta,
            bg=C["blanco"],
            fg=C["codigo"],
            font=("Consolas", 10),
            relief="flat",
            padx=12,
            pady=10,
            height=10,
            state="disabled"
        )
        self.registro.pack(fill="both", expand=True, padx=5, pady=5)

        self.registrar("[10:00] 🌱 MILPA iniciado.")
        self.registrar("[10:00] 💧 Esperando ejecución del programa.")
        
    def registrar(self, texto):
        if hasattr(self, "console_component"):
            self.console_component.registrar(texto)

        elif hasattr(self, "consola"):
            self.mensaje(texto)

    # =====================================================
    # ACCIONES
    # =====================================================

    def abrir(self):

        ruta = filedialog.askopenfilename(
            filetypes=[
                ("Programas MILPA", "*.milpa"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        try:
            contenido = Path(ruta).read_text(encoding="utf-8")

            self.editor_component.establecer_codigo(contenido)
            self.archivo_actual = Path(ruta)
            self.mensaje(f"Archivo abierto: {ruta}", "exito")

        except OSError as error:
            messagebox.showerror("Error", str(error))

    def guardar(self):

        if self.archivo_actual is None:

            ruta = filedialog.asksaveasfilename(
                defaultextension=".milpa",
                filetypes=[("Programas MILPA", "*.milpa")]
            )

            if not ruta:
                return

            self.archivo_actual = Path(ruta)

        try:
            contenido = self.editor.get("1.0", "end-1c")

            self.archivo_actual.write_text(
                contenido,
                encoding="utf-8"
            )

            self.mensaje("Programa guardado correctamente.", "exito")

        except OSError as error:
            messagebox.showerror("Error", str(error))

    def limpiar(self):

        confirmar = messagebox.askyesno(
            "Limpiar editor",
            "¿Deseas borrar todo el código?"
        )

        if confirmar:
            self.editor_component.limpiar()
            self.mensaje("Editor limpiado.")

    
    def cargar_ejemplo(self):

        ejemplo = (
            'zona huerto_norte {\n'
            '    cultivo: "jitomate"\n'
            '    humedad_min: 40.0\n'
            '}\n'
            '\n'
            'decimal litros_total = 0\n'
            '\n'
            'entero humedad = 35\n'
            'entero limite = 80\n'
            '\n'
            'mientras (humedad < limite) {\n'
            '    regar(1)\n'
            '    humedad = humedad + 5\n'
            '    litros_total = litros_total + 1.5\n'
            '}\n'
            '\n'
            'registrar("Riego completado")\n'
        )

        self.editor_component.establecer_codigo(ejemplo)

        self.mensaje("Ejemplo agrícola cargado correctamente.", "exito")


    def compilar(self):

        from src.frontend.lexer import Lexer
        from src.core.errors import ErrorLog

        self.limpiar_resultados()

        codigo = self.editor_component.obtener_codigo()

        self.mensaje("Iniciando compilación...")
        self.registrar("[10:00] Inicio del análisis léxico.")

        try:

            errores = ErrorLog()

            lexer = Lexer(codigo, errores)
            tokens = lexer.analizar()
            
            self.statusbar.actualizar_estado(
                f"Análisis léxico completado: {len(tokens)} tokens"
            )

            self.mostrar_tokens(tokens)

            if errores.hay_errores():

                self.mensaje(
                    "Se encontraron errores léxicos.",
                    "error"
                )

                self.registrar(
                    "[10:00] Error durante el análisis léxico."
                )

            else:

                self.mensaje(
                    f"Análisis léxico completado: "
                    f"{len(tokens)} tokens.",
                    "exito"
                )

                self.registrar(
                    f"[10:00] Análisis léxico completado. "
                    f"Tokens: {len(tokens)}"
                )

            self.notebook_fases.select(0)

        except Exception as error:

            self.mensaje(
                f"Error durante la compilación: {error}",
                "error"
            )
            
            self.statusbar.actualizar_estado(
                "Error durante la compilación"
            )

            self.registrar(f"[ERROR] {error}")


    def mostrar_tokens(self, tokens):

        self.tabla_tokens.delete(
            *self.tabla_tokens.get_children()
        )

        for numero, token in enumerate(tokens, start=1):

            self.tabla_tokens.insert(
                "",
                "end",
                values=(
                    numero,
                    token.tipo,
                    token.valor,
                    token.linea,
                    token.columna
                )
            )

    def ejecutar_simulacion(self):

        self.mensaje("Solicitud de simulación recibida.")
        self.registrar("[10:01] ▶ Solicitud de ejecución.")

    def reiniciar_simulacion(self):

        self.registro.configure(state="normal")
        self.registro.delete("1.0", "end")
        self.registro.configure(state="disabled")

        self.registrar("[10:00] 🔄 Simulación reiniciada.")

    def ayuda(self):

        messagebox.showinfo(
            "Ayuda MILPA",
            "MILPA es un entorno de desarrollo para "
            "programar y simular actividades agrícolas."
        )


# =========================================================
# INICIO
# =========================================================

def main():

    root = tk.Tk()
    MilpaIDE(root)
    root.mainloop()


if __name__ == "__main__":
    main()
