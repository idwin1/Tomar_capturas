import os
import sys
import subprocess
import json
# Lista de librerías externas que requiere tu proyecto
LIBRERIAS_REQUERIDAS = {
    "psycopg2": "psycopg2-binary",
    "colorama": "colorama",
    "tkinter": "tkinter",
    "platform" : "platform"
}

def verificar_e_instalar_librerIAS():
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

verificar_e_instalar_librerIAS()


from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageTk, Image, ImageGrab
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
        self.root.geometry("350x290")
        self.root.resizable(False, False)
 
        # Ocultar la ventana principal temporalmente por si hay que pedir la carpeta al inicio
        self.root.withdraw()
 
        # Cargar la ruta guardada o pedirla obligatoriamente si es la primera vez
        self.ruta_guardado = self.obtener_ruta_inicial()
 
        # Volver a mostrar la ventana principal una vez definida la carpeta
        self.root.deiconify()
 
        # Variables para el recorte
        self.inicio_x = None
        self.inicio_y = None
        self.cuadrado_seleccion = None
        self.pantalla_completa_img = None
 
        # Interfaz de usuario
        etiqueta = tk.Label(
            self.root,
            text="Selecciona el tipo de captura:",
            font=("Arial", 11, "bold"),
            pady=10,
        )
        etiqueta.pack()
 
        # Botón para captura completa
        btn_completa = tk.Button(
            self.root,
            text="📸 Pantalla Completa",
            command=self.captura_completa,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10),
            width=22,
        )
        btn_completa.pack(pady=4)
 
        # Botón para recortar zona
        btn_recorte = tk.Button(
            self.root,
            text="✂️ Recortar Área",
            command=self.iniciar_recorte,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10),
            width=22,
        )
        btn_recorte.pack(pady=4)
 
        # Botón para cambiar de carpeta
        btn_cambiar_carpeta = tk.Button(
            self.root,
            text="⚙️ Cambiar Carpeta",
            command=self.cambiar_carpeta,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 10),
            width=22,
        )
        btn_cambiar_carpeta.pack(pady=4)
 
        # Botón para abrir ubicación de archivo
        btn_ubicacion = tk.Button(
            self.root,
            text="📁 Abrir Ubicación",
            command=lambda: self.abrir_ubicacion(self.ruta_guardado),
            bg="#FF9800",
            fg="white",
            font=("Arial", 10),
            width=22,
        )
        btn_ubicacion.pack(pady=4)
 
        # Texto indicador de la carpeta activa actual
        self.lbl_ruta = tk.Label(
            self.root,
            text=f"Guardando en: {Path(self.ruta_guardado).name}",
            font=("Arial", 8, "italic"),
            fg="#555555",
            pady=5
        )
        self.lbl_ruta.pack()
 
    def obtener_ruta_inicial(self):
        """
        Intenta leer la ruta guardada en el JSON. Si es la primera vez,
        le pide al usuario que seleccione su carpeta.
        """
        # 1. Intentar leer la ruta guardada previamente en el config usando la nueva estructura
        datos = cargar_configuracion()
        ruta_guardada = datos.get("Ruta_Guardada", {}).get("ruta", "")
        
        # Validamos que la ruta exista físicamente en la computadora
        if ruta_guardada and os.path.exists(ruta_guardada):
            return os.path.abspath(ruta_guardada)
 
        # 2. Si no hay archivo de configuración o la ruta fue borrada, pedir la carpeta
        messagebox.showinfo(
            "Configuración Inicial",
            "¡Bienvenido a Capturador Pro!\n\n"
            "Para comenzar, por favor selecciona la carpeta en donde quieres que se guarden tus capturas por defecto."
        )
 
        # Abrir el selector de carpetas
        ruta_seleccionada = filedialog.askdirectory(
            title="Selecciona tu carpeta de capturas inicial"
        )
 
        # Si el usuario selecciona una carpeta, la memoriza y arranca la app
        if ruta_seleccionada:
            ruta_abs = os.path.abspath(ruta_seleccionada)
            self.guardar_ruta_en_config(ruta_abs)
            return ruta_abs
        else:
            # Si cancela en este paso inicial, cerramos el programa de forma segura
            messagebox.showwarning(
                "Configuración Requerida",
                "Debes elegir una carpeta para poder utilizar la aplicación."
            )
            self.root.destroy()
            sys.exit()
 
    def guardar_ruta_en_config(self, ruta):
        """Guarda la ruta seleccionada en el archivo JSON manteniendo la estructura segura."""
        try:
            datos = cargar_configuracion()
            
            # Aseguramos que la estructura exista
            if "Ruta_Guardada" not in datos or not isinstance(datos["Ruta_Guardada"], dict):
                datos["Ruta_Guardada"] = {}
                
            # Guardamos la nueva ruta
            datos["Ruta_Guardada"]["ruta"] = ruta
            
            # Escribimos el JSON
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(Fore.RED + f"[❌] No se pudo guardar la configuración: {e}")
 
    def preparar_carpeta(self):
        # Asegurarse de que la carpeta de guardado exista antes de capturar
        if not os.path.exists(self.ruta_guardado):
            os.makedirs(self.ruta_guardado, exist_ok=True)
               
        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(self.ruta_guardado, f"captura_{fecha_hora}.png")
 
    def cambiar_carpeta(self):
        # Abre el selector de directorios del sistema
        nueva_ruta = filedialog.askdirectory(
            initialdir=self.ruta_guardado,
            title="Selecciona la carpeta para guardar tus capturas"
        )
        # Si el usuario no cancela el selector, actualiza la ruta y la memoriza
        if nueva_ruta:
            self.ruta_guardado = os.path.abspath(nueva_ruta)
            self.guardar_ruta_en_config(self.ruta_guardado)
            # Actualiza el texto en la interfaz (muestra el nombre de la carpeta final)
            self.lbl_ruta.config(text=f"Guardando en: {Path(self.ruta_guardado).name}")
            messagebox.showinfo(
                "Carpeta Cambiada",
                f"Las capturas ahora se guardarán en:\n{self.ruta_guardado}"
            )
 
    def captura_completa(self):
        self.root.withdraw()  # Ocultar menú
        self.root.after(
            300, self._hacer_captura_completa
        )  # Pequeña pausa para ocultar bien
 
    def _hacer_captura_completa(self):
        try:
            ruta = self.preparar_carpeta()
            captura = ImageGrab.grab()
            captura.save(ruta)
            messagebox.showinfo("Éxito", f"Captura completa guardada en:\n{ruta}")
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
 
        self.ventana_recorte.bind(
            "<Escape>", lambda e: self.cancelar_recorte()
        )
 
    def al_hacer_clic(self, event):
        self.inicio_x = event.x
        self.inicio_y = event.y
        self.cuadrado_seleccion = self.canvas.create_rectangle(
            self.inicio_x,
            self.inicio_y,
            self.inicio_x,
            self.inicio_y,
            outline="red",
            width=2,
        )
 
    def al_arrastrar(self, event):
        actual_x, actual_y = event.x, event.y
        self.canvas.coords(
            self.cuadrado_seleccion,
            self.inicio_x,
            self.inicio_y,
            actual_x,
            actual_y,
        )
 
    def al_soltar_clic(self, event):
        fin_x, fin_y = event.x, event.y
        self.ventana_recorte.destroy()
 
        x1 = min(self.inicio_x, fin_x)
        y1 = min(self.inicio_y, fin_y)
        x2 = max(self.inicio_x, fin_x)
        y2 = max(self.inicio_y, fin_y)
 
        if x2 - x1 > 5 and y2 - y1 > 5:
            try:
                ruta = self.preparar_carpeta()
                imagen_recortada = self.pantalla_completa_img.crop(
                    (x1, y1, x2, y2)
                )
                imagen_recortada.save(ruta)
                messagebox.showinfo(
                    "Éxito", f"Recorte guardado con éxito en:\n{ruta}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo recortar: {e}")
 
        self.root.deiconify()
 
    def cancelar_recorte(self):
        self.ventana_recorte.destroy()
        self.root.deiconify()
   
    def abrir_ubicacion(self, ruta_str):
        ruta = Path(ruta_str).resolve()
   
        if not ruta.exists():
            messagebox.showerror(
                "Error", f"La ruta especificada no existe:\n{ruta}"
            )
            return
   
        sistema = platform.system()
   
        if sistema == "Windows":
            ruta_win = str(ruta).replace("/", "\\")
   
            if ruta.is_file():
                subprocess.Popen(f'explorer /select,"{ruta_win}"')
            else:
                os.startfile(ruta_win)
   
        elif sistema == "Darwin":  # macOS
            subprocess.Popen(["open", "-R", str(ruta)])
   
        else:  # Linux
            carpeta = str(ruta.parent) if ruta.is_file() else str(ruta)
            subprocess.Popen(["open", carpeta])
 
 
if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
 
    ventana = tk.Tk()
    app = AplicacionCaptura(ventana)
    ventana.mainloop()