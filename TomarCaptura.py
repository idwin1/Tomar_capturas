import os
import sys
import subprocess
import json

# Lista de librerías externas que requiere tu proyecto
LIBRERIAS_REQUERIDAS = {
    "colorama": "colorama",
    "customtkinter": "customtkinter",
    "PIL": "pillow"
}

def verificar_e_instalar_librerias():
    """Revisa si las librerías están instaladas; si no, las instala automáticamente"""
    for import_name, pip_name in LIBRERIAS_REQUERIDAS.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"[!] La librería '{import_name}' no está instalada.")
            print(f"[+] Instalando '{pip_name}' automáticamente en segundo plano...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"[✔] '{pip_name}' instalada con éxito.\n")
            except Exception as e:
                print(f"[❌] Error crítico al intentar instalar {pip_name}: {e}")
                sys.exit(1)

verificar_e_instalar_librerias()

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageGrab, ImageOps
import platform
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)
 
# -------------------------------------------------------------------------
# CARGA DE CONFIGURACIÓN SEGURA
# -------------------------------------------------------------------------
CONFIG_FILE = "config.json"

def cargar_configuracion():
    """Carga el JSON. Si no existe, devuelve un diccionario vacío para crearlo después."""
    if not os.path.exists(CONFIG_FILE):
        return {}
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(Fore.RED + f"[❌] Error al cargar la configuración: {e}")
        return {}

 
class AplicacionCaptura:
 
    def __init__(self, ventana_principal):
        self.root = ventana_principal
        self.root.title("Capturador Pro")
        self.root.geometry("320x450")
        #self.root.resizable(False, False)
        
        # Tema oscuro por defecto
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
 
        # CARGA LA RUTA (Sin ocultar la ventana a la fuerza, evitando que se corrompa)
        self.ruta_guardado = self.obtener_ruta_inicial()
 
        # Variables para el recorte
        self.inicio_x = None
        self.inicio_y = None
        self.cuadrado_seleccion = None
        self.pantalla_completa_img = None
 
        # ---------------------------------------------------------------------
        # INTERFAZ DE USUARIO (GRID LAYOUT MODERNO)
        # ---------------------------------------------------------------------
        
        # --- FILA 1: CABECERA E INFORMACIÓN ---
        self.frame_header = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_header.pack(pady=(15, 5), padx=20, fill="x")
        
        lbl_titulo = ctk.CTkLabel(self.frame_header, text="📸 Capturador Pro", font=("Arial", 18, "bold"))
        lbl_titulo.pack(side="left")
        
        nombre_carpeta = Path(self.ruta_guardado).name
        self.lbl_ruta = ctk.CTkLabel(self.frame_header, text=f"📁 {nombre_carpeta}", fg_color="#2b2b2b", corner_radius=6, padx=10)
        self.lbl_ruta.pack(side="right")

        # --- FILA 2: ACCIONES PRINCIPALES ---
        self.frame_grid = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_grid.pack(pady=5, padx=15, fill="x")
        self.frame_grid.columnconfigure((0, 1), weight=1)

        # Tarjeta 1: Pantalla Completa
        self.tarjeta_completa = ctk.CTkFrame(self.frame_grid, fg_color="#2b2b2b", corner_radius=10)
        self.tarjeta_completa.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.tarjeta_completa, text="📸", font=("Segoe UI Emoji", 36)).pack(pady=(15, 0))
        ctk.CTkLabel(self.tarjeta_completa, text="Pantalla Completa", font=("Arial", 12, "bold")).pack()
        ctk.CTkButton(self.tarjeta_completa, text="Capturar", command=self.captura_completa, width=120).pack(pady=15)

        # Tarjeta 2: Recortar
        self.tarjeta_recorte = ctk.CTkFrame(self.frame_grid, fg_color="#2b2b2b", corner_radius=10)
        self.tarjeta_recorte.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.tarjeta_recorte, text="✂️", font=("Segoe UI Emoji", 36)).pack(pady=(15, 0))
        ctk.CTkLabel(self.tarjeta_recorte, text="Recortar Área", font=("Arial", 12, "bold")).pack()
        ctk.CTkButton(self.tarjeta_recorte, text="Iniciar", command=self.iniciar_recorte, width=120).pack(pady=15)

        # --- FILA 3: ACCIONES SECUNDARIAS ---
        self.frame_sec = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_sec.pack(pady=0, padx=15, fill="x")
        self.frame_sec.columnconfigure((0, 1), weight=1)
        
        btn_cambiar = ctk.CTkButton(self.frame_sec, text="⚙️ Cambiar Carpeta", fg_color="#3a3a3a", hover_color="#4a4a4a", command=self.cambiar_carpeta)
        btn_cambiar.grid(row=0, column=0, padx=5, pady=5, sticky="nsew", ipady=4)
        
        btn_abrir = ctk.CTkButton(self.frame_sec, text="📂 Abrir Directorio", fg_color="#3a3a3a", hover_color="#4a4a4a", command=lambda: self.abrir_ubicacion(self.ruta_guardado))
        btn_abrir.grid(row=0, column=1, padx=5, pady=5, sticky="nsew", ipady=4)

        # --- FILA 4: PANEL DE PREVISUALIZACIÓN ---
        self.frame_preview = ctk.CTkFrame(self.root, fg_color="#1a1a1a", corner_radius=8, border_width=1, border_color="#333333")
        self.frame_preview.pack(pady=(15, 10), padx=20, fill="both", expand=True)
        
        # 1. Agrupamos el texto estático y el nombre del archivo en la misma línea superior
        self.frame_textos = ctk.CTkFrame(self.frame_preview, fg_color="transparent")
        self.frame_textos.pack(fill="x", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(self.frame_textos, text="Última captura guardada: ", font=("Arial", 11), text_color="#aaaaaa").pack(side="left")
        
        self.lbl_filename = ctk.CTkLabel(self.frame_textos, text="Esperando captura...", font=("Arial", 11, "italic"), text_color="#888888")
        self.lbl_filename.pack(side="left")
        
        # 2. Contenedor interno para la miniatura y el botón
        self.preview_inner = ctk.CTkFrame(self.frame_preview, fg_color="transparent")
        self.preview_inner.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Miniatura centrada
        self.lbl_thumb = ctk.CTkLabel(self.preview_inner, text="🖼️", font=("Segoe UI Emoji", 30), text_color="#555555", width=140, height=80, fg_color="#2b2b2b", corner_radius=6)
        self.lbl_thumb.pack(side="top", pady=(5, 10))
        
        # Botón abajo ocupando el ancho
        self.btn_open_img = ctk.CTkButton(self.preview_inner, text="🔍 Abrir Imagen", fg_color="#1f538d", state="disabled")
        self.btn_open_img.pack(side="bottom", fill="x")  
 
    # -------------------------------------------------------------------------
    # FUNCIONES LÓGICAS
    # -------------------------------------------------------------------------
    def obtener_ruta_inicial(self):
        datos = cargar_configuracion()
        ruta_guardada = datos.get("Ruta_Guardada", {}).get("ruta", "")
        
        # Si la ruta ya existe, devolverla inmediatamente (sin tocar la ventana)
        if ruta_guardada and os.path.exists(ruta_guardada):
            return os.path.abspath(ruta_guardada)
 
        # Si NO existe, ocultamos la ventana SOLAMENTE para pedir la carpeta
        self.root.withdraw()
        messagebox.showinfo("Configuración", "Por favor selecciona la carpeta en donde quieres guardar tus capturas por defecto.")
        ruta_seleccionada = filedialog.askdirectory(title="Selecciona tu carpeta de capturas inicial")
 
        if ruta_seleccionada:
            ruta_abs = os.path.abspath(ruta_seleccionada)
            self.guardar_ruta_en_config(ruta_abs)
            self.root.deiconify() # Restauramos la ventana
            return ruta_abs
        else:
            sys.exit() # Si cancela, cerramos sin errores
 
    def guardar_ruta_en_config(self, ruta):
        try:
            datos = cargar_configuracion()
            if "Ruta_Guardada" not in datos or not isinstance(datos["Ruta_Guardada"], dict):
                datos["Ruta_Guardada"] = {}
            datos["Ruta_Guardada"]["ruta"] = ruta
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[❌] Error al guardar config: {e}")
 
    def preparar_carpeta(self):
        if not os.path.exists(self.ruta_guardado):
            os.makedirs(self.ruta_guardado, exist_ok=True)
        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(self.ruta_guardado, f"captura_{fecha_hora}.png")
 
    def cambiar_carpeta(self):
        nueva_ruta = filedialog.askdirectory(initialdir=self.ruta_guardado, title="Selecciona la carpeta para guardar")
        if nueva_ruta:
            self.ruta_guardado = os.path.abspath(nueva_ruta)
            self.guardar_ruta_en_config(self.ruta_guardado)
            self.lbl_ruta.configure(text=f"📁 {Path(self.ruta_guardado).name}")


    def actualizar_vista_previa(self, ruta_imagen):
        """Genera la miniatura y actualiza el panel inferior con la nueva captura"""
        try:
            img = Image.open(ruta_imagen)
            
            # Recorta y ajusta la imagen para que llene perfectamente el espacio de 140x80
            img_recortada = ImageOps.fit(img, (140, 80), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img_recortada, dark_image=img_recortada, size=(140, 80))
            
            # Actualizar labels
            self.lbl_thumb.configure(image=ctk_img, text="")
            nombre_archivo = Path(ruta_imagen).name
            
            # Recortar nombre si es muy largo para que no desborde la interfaz
            if len(nombre_archivo) > 22:
                nombre_archivo = nombre_archivo[:19] + "..."
                
            self.lbl_filename.configure(text=f"📄 {nombre_archivo}", font=("Arial", 11, "normal"), text_color="#ffffff")
            
            # Habilitar botón de acción rápida
            self.btn_open_img.configure(state="normal", command=lambda: self.abrir_ubicacion(ruta_imagen))
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al generar miniatura: {e}")

    # -------------------------------------------------------------------------
    # MÉTODOS DE CAPTURA
    # -------------------------------------------------------------------------
    def captura_completa(self):
        self.root.withdraw()
        self.root.after(300, self._hacer_captura_completa)
 
    def _hacer_captura_completa(self):
        try:
            ruta = self.preparar_carpeta()
            captura = ImageGrab.grab()
            captura.save(ruta)
            captura.close()
            # En lugar de messagebox, actualizamos la vista previa silenciosamente
            self.actualizar_vista_previa(ruta)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
        self.root.deiconify()
 
    def iniciar_recorte(self):
        self.root.withdraw()
        self.root.after(300, self._crear_capa_recorte)
 
    def _crear_capa_recorte(self):
        self.pantalla_completa_img = ImageGrab.grab()
        self.ventana_recorte = tk.Toplevel()
        self.ventana_recorte.attributes("-fullscreen", True)
        self.ventana_recorte.attributes("-alpha", 0.3)
        self.ventana_recorte.config(cursor="cross")
 
        self.canvas = tk.Canvas(self.ventana_recorte, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
 
        self.canvas.bind("<ButtonPress-1>", self.al_hacer_clic)
        self.canvas.bind("<B1-Motion>", self.al_arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.al_soltar_clic)
        self.ventana_recorte.bind("<Escape>", lambda e: self.cancelar_recorte())
 
    def al_hacer_clic(self, event):
        self.inicio_x = event.x
        self.inicio_y = event.y
        self.cuadrado_seleccion = self.canvas.create_rectangle(self.inicio_x, self.inicio_y, self.inicio_x, self.inicio_y, outline="red", width=2)
 
    def al_arrastrar(self, event):
        actual_x, actual_y = event.x, event.y
        self.canvas.coords(self.cuadrado_seleccion, self.inicio_x, self.inicio_y, actual_x, actual_y)
 
    def al_soltar_clic(self, event):
        fin_x, fin_y = event.x, event.y
        self.ventana_recorte.destroy()
 
        x1, y1 = min(self.inicio_x, fin_x), min(self.inicio_y, fin_y)
        x2, y2 = max(self.inicio_x, fin_x), max(self.inicio_y, fin_y)
 
        if x2 - x1 > 5 and y2 - y1 > 5:
            try:
                ruta = self.preparar_carpeta()
                imagen_recortada = self.pantalla_completa_img.crop((x1, y1, x2, y2))
                imagen_recortada.save(ruta)
                imagen_recortada.close()
                self.actualizar_vista_previa(ruta)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo recortar: {e}")
        
        if self.pantalla_completa_img:
            self.pantalla_completa_img.close()
            self.pantalla_completa_img = None
            
        self.root.deiconify()
 
    def cancelar_recorte(self):
        self.ventana_recorte.destroy()
        if self.pantalla_completa_img:
            self.pantalla_completa_img.close()
            self.pantalla_completa_img = None
        self.root.deiconify()
 
    def abrir_ubicacion(self, ruta_str):
        ruta = Path(ruta_str).resolve()
        if not ruta.exists():
            messagebox.showerror("Error", f"La ruta no existe:\n{ruta}")
            return
   
        sistema = platform.system()
        if sistema == "Windows":
            ruta_win = str(ruta).replace("/", "\\")
            if ruta.is_file():
                subprocess.Popen(f'explorer /select,"{ruta_win}"')
            else:
                os.startfile(ruta_win)
        elif sistema == "Darwin":
            subprocess.Popen(["open", "-R", str(ruta)])
        else:
            carpeta = str(ruta.parent) if ruta.is_file() else str(ruta)
            subprocess.Popen(["open", carpeta])
 
if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
 
    # === SISTEMA DE DETECCIÓN DE ERRORES AL INICIO ===
    try:
        ventana = ctk.CTk()
        app = AplicacionCaptura(ventana)
        ventana.mainloop()
    except Exception as e:
        import tkinter.messagebox as mb
        # Si la app crashea al abrir, te saldrá esta ventana diciendo el porqué:
        mb.showerror("Error Crítico de Inicialización", f"El aplicativo no pudo iniciar.\n\nDetalle del error:\n{e}")