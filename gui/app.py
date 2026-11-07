
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


# ==========================================
# CONFIGURACION VISUAL DE MILPA
# ==========================================

COLORES = {
    "fondo": "#101713",
    "panel": "#17221B",
    "panel_secundario": "#1D2B22",
    "editor": "#111A15",
    "verde": "#65C466",
    "verde_oscuro": "#347A43",
    "texto": "#E1EDE3",
    "texto_secundario": "#91A797",
    "borde": "#304638",
    "error": "#F07178",
    "advertencia": "#E5BD67",
}


class MilpaIDE:

    def __init__(self, ventana):

        self.ventana = ventana
        self.ruta_actual = None

        self.configurar_ventana()
        self.configurar_estilos()
        self.crear_interfaz()
        self.configurar_editor()

    # ==========================================
    # VENTANA
    # ==========================================

    def configurar_ventana(self):

        self.ventana.title("MILPA | Compiler IDE")
        self.ventana.geometry("1250x780")
        self.ventana.minsize(950, 600)
        self.ventana.configure(bg=COLORES["fondo"])

    def configurar_estilos(self):

        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "TNotebook",
            background=COLORES["panel"],
            borderwidth=0
        )

        estilo.configure(
            "TNotebook.Tab",
            background=COLORES["panel_secundario"],
            foreground=COLORES["texto_secundario"],
            padding=(14, 8),
            borderwidth=0
        )

        estilo.map(
            "TNotebook.Tab",
            background=[
                ("selected", COLORES["verde_oscuro"])
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        estilo.configure(
            "Treeview",
            background=COLORES["panel"],
            foreground=COLORES["texto"],
            fieldbackground=COLORES["panel"],
            rowheight=27
        )

        estilo.configure(
            "Treeview.Heading",
            background=COLORES["panel_secundario"],
            foreground=COLORES["verde"],
            relief="flat"
        )

    # ==========================================
    # INTERFAZ PRINCIPAL
    # ==========================================

    def crear_interfaz(self):

        self.crear_barra_superior()

        principal = tk.Frame(
            self.ventana,
            bg=COLORES["fondo"]
        )

        principal.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(5, 10)
        )

        # Distribucion horizontal
        horizontal = tk.PanedWindow(
            principal,
            orient="horizontal",
            bg=COLORES["fondo"],
            sashwidth=5,
            bd=0
        )

        horizontal.pack(fill="both", expand=True)

        # Editor izquierdo
        self.panel_editor = tk.Frame(
            horizontal,
            bg=COLORES["editor"]
        )

        horizontal.add(
            self.panel_editor,
            minsize=420,
            width=650
        )

        # Panel de resultados derecho
        self.panel_resultados = tk.Frame(
            horizontal,
            bg=COLORES["panel"]
        )

        horizontal.add(
            self.panel_resultados,
            minsize=300
        )

        self.crear_editor()
        self.crear_resultados()
        self.crear_consola(principal)

        self.crear_barra_estado()

    # ==========================================
    # BARRA SUPERIOR
    # ==========================================

    def crear_barra_superior(self):

        barra = tk.Frame(
            self.ventana,
            bg=COLORES["panel"],
            height=65
        )

        barra.pack(fill="x")
        barra.pack_propagate(False)

        logo = tk.Frame(
            barra,
            bg=COLORES["panel"]
        )

        logo.pack(side="left", padx=18)

        tk.Label(
            logo,
            text="MILPA",
            font=("Segoe UI", 19, "bold"),
            fg=COLORES["verde"],
            bg=COLORES["panel"]
        ).pack(side="left")

        tk.Label(
            logo,
            text="  COMPILER IDE",
            font=("Segoe UI", 9),
            fg=COLORES["texto_secundario"],
            bg=COLORES["panel"]
        ).pack(side="left", pady=(8, 0))

        botones = tk.Frame(
            barra,
            bg=COLORES["panel"]
        )

        botones.pack(side="right", padx=15)

        self.boton(
            botones,
            "Abrir",
            self.abrir_archivo
        ).pack(side="left", padx=4)

        self.boton(
            botones,
            "Guardar",
            self.guardar_archivo
        ).pack(side="left", padx=4)

        self.boton(
            botones,
            "Compilar",
            self.compilar
        ).pack(side="left", padx=4)

        self.boton(
            botones,
            "Optimizar",
            self.optimizar
        ).pack(side="left", padx=4)

    # ==========================================
    # BOTONES
    # ==========================================

    def boton(self, padre, texto, comando):

        return tk.Button(
            padre,
            text=texto,
            command=comando,
            bg=COLORES["verde_oscuro"],
            fg="#FFFFFF",
            activebackground=COLORES["verde"],
            activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        )

    # ==========================================
    # EDITOR
    # ==========================================

    def crear_editor(self):

        encabezado = tk.Frame(
            self.panel_editor,
            bg=COLORES["panel_secundario"],
            height=38
        )

        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text="  EDITOR DE CODIGO",
            bg=COLORES["panel_secundario"],
            fg=COLORES["verde"],
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=8, pady=9)

        tk.Label(
            encabezado,
            text="MILPA",
            bg=COLORES["panel_secundario"],
            fg=COLORES["texto_secundario"],
            font=("Segoe UI", 9)
        ).pack(side="right", padx=12)

        contenedor = tk.Frame(
            self.panel_editor,
            bg=COLORES["editor"]
        )

        contenedor.pack(fill="both", expand=True)

        self.lineas = tk.Text(
            contenedor,
            width=4,
            padx=8,
            pady=12,
            bg=COLORES["editor"],
            fg=COLORES["texto_secundario"],
            font=("Consolas", 11),
            relief="flat",
            state="disabled",
            takefocus=0
        )

        self.lineas.pack(side="left", fill="y")

        self.editor = tk.Text(
            contenedor,
            bg=COLORES["editor"],
            fg=COLORES["texto"],
            insertbackground=COLORES["verde"],
            selectbackground=COLORES["verde_oscuro"],
            font=("Consolas", 11),
            padx=10,
            pady=12,
            relief="flat",
            undo=True,
            wrap="none"
        )

        self.editor.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=self.editor.yview
        )

        scroll.pack(side="right", fill="y")

        self.editor.configure(yscrollcommand=scroll.set)

        self.editor.insert(
            "1.0",
            'entero humedad = 50\n'
            'entero limite = 80\n'
            '\n'
            'mientras (humedad < limite) {\n'
            '    humedad = humedad + 5\n'
            '}\n'
            '\n'
            'si (humedad >= limite) {\n'
            '    registrar("Riego completado")\n'
            '} si_no {\n'
            '    regar(10)\n'
            '}\n'
        )

        self.actualizar_lineas()

    def configurar_editor(self):

        self.editor.bind(
            "<KeyRelease>",
            lambda evento: self.actualizar_lineas()
        )

        self.editor.bind(
            "<MouseWheel>",
            lambda evento: self.actualizar_lineas()
        )

    def actualizar_lineas(self):

        contenido = self.editor.get("1.0", "end-1c")
        cantidad = contenido.count("\n") + 1

        self.lineas.configure(state="normal")
        self.lineas.delete("1.0", "end")

        for numero in range(1, cantidad + 1):
            self.lineas.insert("end", f"{numero}\n")

        self.lineas.configure(state="disabled")

    # ==========================================
    # PANEL DE RESULTADOS
    # ==========================================

    def crear_resultados(self):

        encabezado = tk.Label(
            self.panel_resultados,
            text="RESULTADOS DEL COMPILADOR",
            bg=COLORES["panel_secundario"],
            fg=COLORES["verde"],
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=12,
            pady=11
        )

        encabezado.pack(fill="x")

        self.pestanas = ttk.Notebook(
            self.panel_resultados
        )

        self.pestanas.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        nombres = [
            "Tokens",
            "AST",
            "Semántico",
            "Cuádruplos",
            "Optimización",
            "Registros",
            "MIPS"
        ]

        self.paneles = {}

        for nombre in nombres:

            marco = tk.Frame(
                self.pestanas,
                bg=COLORES["panel"]
            )

            self.pestanas.add(marco, text=nombre)

            texto = tk.Text(
                marco,
                bg=COLORES["panel"],
                fg=COLORES["texto"],
                font=("Consolas", 10),
                relief="flat",
                wrap="none",
                padx=10,
                pady=10
            )

            texto.pack(fill="both", expand=True)

            texto.insert(
                "1.0",
                f"Los resultados de {nombre} aparecerán aquí."
            )

            texto.configure(state="disabled")

            self.paneles[nombre] = texto

    # ==========================================
    # CONSOLA INFERIOR
    # ==========================================

    def crear_consola(self, padre):

        marco = tk.Frame(
            padre,
            bg=COLORES["panel"],
            height=145
        )

        marco.pack(fill="x", pady=(8, 0))
        marco.pack_propagate(False)

        tk.Label(
            marco,
            text="  CONSOLA DE MILPA",
            bg=COLORES["panel_secundario"],
            fg=COLORES["verde"],
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            pady=7
        ).pack(fill="x")

        self.consola = tk.Text(
            marco,
            bg=COLORES["editor"],
            fg=COLORES["texto"],
            font=("Consolas", 9),
            relief="flat",
            height=5,
            padx=10,
            pady=7,
            state="disabled"
        )

        self.consola.pack(fill="both", expand=True)

        self.mensaje("MILPA Compiler IDE iniciado correctamente.")
        self.mensaje("Editor preparado para archivos .milpa.")

    def mensaje(self, texto):

        self.consola.configure(state="normal")
        self.consola.insert("end", f"> {texto}\n")
        self.consola.see("end")
        self.consola.configure(state="disabled")

    # ==========================================
    # BARRA DE ESTADO
    # ==========================================

    def crear_barra_estado(self):

        barra = tk.Frame(
            self.ventana,
            bg=COLORES["verde_oscuro"],
            height=25
        )

        barra.pack(fill="x", side="bottom")

        tk.Label(
            barra,
            text="MILPA | Compilador de lenguaje para agricultura",
            bg=COLORES["verde_oscuro"],
            fg="#FFFFFF",
            font=("Segoe UI", 8)
        ).pack(side="left", padx=10)

        tk.Label(
            barra,
            text="Python | MIPS32 | MARS",
            bg=COLORES["verde_oscuro"],
            fg="#FFFFFF",
            font=("Segoe UI", 8)
        ).pack(side="right", padx=10)

    # ==========================================
    # ARCHIVOS
    # ==========================================

    def abrir_archivo(self):

        ruta = filedialog.askopenfilename(
            filetypes=[
                ("Archivos MILPA", "*.milpa"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        try:
            contenido = Path(ruta).read_text(encoding="utf-8")

            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", contenido)

            self.ruta_actual = Path(ruta)
            self.actualizar_lineas()

            self.mensaje(f"Archivo abierto: {ruta}")

        except OSError as error:
            messagebox.showerror("Error", str(error))

    def guardar_archivo(self):

        if self.ruta_actual is None:

            ruta = filedialog.asksaveasfilename(
                defaultextension=".milpa",
                filetypes=[
                    ("Archivos MILPA", "*.milpa")
                ]
            )

            if not ruta:
                return

            self.ruta_actual = Path(ruta)

        try:
            contenido = self.editor.get("1.0", "end-1c")

            self.ruta_actual.write_text(
                contenido,
                encoding="utf-8"
            )

            self.mensaje(
                f"Archivo guardado: {self.ruta_actual}"
            )

        except OSError as error:
            messagebox.showerror("Error", str(error))

    # ==========================================
    # ACCIONES TEMPORALES
    # ==========================================

    def compilar(self):

        self.mensaje(
            "La integración con las fases del compilador se realizará en la siguiente etapa."
        )

    def optimizar(self):

        self.mensaje(
            "La integración del optimizador se realizará en la siguiente etapa."
        )


def main():

    ventana = tk.Tk()
    MilpaIDE(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
