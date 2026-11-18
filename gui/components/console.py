
# =====================================================
# MILPA IDE - CONSOLA
# =====================================================

import tkinter as tk

from gui.config.colors import COLORS
from gui.config.fonts import FONTS


class ConsolePanel:

    def __init__(self, parent):

        self.frame = tk.Frame(
            parent,
            bg=COLORS["console_background"],
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["border"],
            highlightthickness=1
        )

        self._crear_interfaz()

    # -------------------------------------------------
    # INTERFAZ
    # -------------------------------------------------

    def _crear_interfaz(self):

        encabezado = tk.Frame(
            self.frame,
            bg=COLORS["white"],
            height=38
        )

        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text="›_",
            bg=COLORS["white"],
            fg=COLORS["primary"],
            font=FONTS["console"]
        ).pack(side="left", padx=(16, 8))

        tk.Label(
            encabezado,
            text="Consola del compilador",
            bg=COLORS["white"],
            fg=COLORS["text"],
            font=FONTS["heading"],
            anchor="w"
        ).pack(side="left")

        tk.Frame(
            self.frame,
            bg=COLORS["border_soft"],
            height=1
        ).pack(fill="x")

        self.consola = tk.Text(
            self.frame,
            bg=COLORS["console_background"],
            fg=COLORS["code"],
            font=FONTS["console"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=16,
            pady=10,
            spacing1=2,
            spacing3=2,
            height=8,
            state="disabled",
            selectbackground=COLORS["selection"],
            inactiveselectbackground=COLORS["green_light"],
            wrap="word"
        )

        self.consola.pack(
            fill="both",
            expand=True
        )

        # Colores de mensajes
        self.consola.tag_configure(
            "success",
            foreground=COLORS["success"]
        )

        self.consola.tag_configure(
            "error",
            foreground=COLORS["error"]
        )

        self.consola.tag_configure(
            "warning",
            foreground=COLORS["warning"]
        )

        self.consola.tag_configure(
            "normal",
            foreground=COLORS["code"]
        )

        self.mensaje(
            "MILPA IDE iniciado correctamente.",
            "success"
        )

        self.mensaje(
            "Esperando compilación..."
        )

    # -------------------------------------------------
    # MENSAJES
    # -------------------------------------------------

    def mensaje(self, texto, tipo="normal"):

        self.consola.configure(state="normal")

        self.consola.insert(
            "end",
            f"> {texto}\n",
            tipo
        )

        self.consola.see("end")

        self.consola.configure(state="disabled")

    def limpiar(self):

        self.consola.configure(state="normal")
        self.consola.delete("1.0", "end")
        self.consola.configure(state="disabled")

    # -------------------------------------------------
    # REGISTRO DE EJECUCION
    # -------------------------------------------------

    def registrar(self, texto):

        self.mensaje(texto)

    def error(self, texto):

        self.mensaje(texto, "error")

    def exito(self, texto):

        self.mensaje(texto, "success")

    def advertencia(self, texto):

        self.mensaje(texto, "warning")
