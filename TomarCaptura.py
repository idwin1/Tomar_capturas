import os
import sys
import subprocess
import json

# Lista de librerías externas que requiere tu proyecto
LIBRERIAS_REQUERIDAS = {
    "colorama": "colorama",
    "customtkinter": "customtkinter",
    "PIL": "pillow",
    "mss": "mss"
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
import mss
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
        self.root.geometry("320x480")
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

        # Historial de capturas
        self.historial_rutas = []
        self.indice_actual = -1 # -1 significa que no hay capturas aún
        
 
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

        # ---------------------------------------------------------
        # NUEVO: SWITCH DEL PORTAPAPELES
        # ---------------------------------------------------------
        # 1. Leer el estado guardado (por defecto en True)
        datos_config = cargar_configuracion()
        copiar_auto = datos_config.get("Opciones", {}).get("copiar_portapapeles", True)
        
        self.var_portapapeles = ctk.BooleanVar(value=copiar_auto)
        
        # 2. Crear el Switch en la interfaz
        self.switch_portapapeles = ctk.CTkSwitch(
            self.frame_sec, 
            text="Copiar al portapapeles", 
            variable=self.var_portapapeles,
            command=self.guardar_config_switch, # Llama a esta función al hacer clic
            font=("Arial", 12)
        )
        # Lo colocamos en la fila 1 (debajo de los botones) ocupando ambas columnas
        self.switch_portapapeles.grid(row=1, column=0, columnspan=2, pady=(10, 5), padx=5, sticky="w")

        # --- FILA 4: PANEL DE PREVISUALIZACIÓN (CARRUSEL) ---
        self.frame_preview = ctk.CTkFrame(self.root, fg_color="#1a1a1a", corner_radius=8, border_width=1, border_color="#333333")
        self.frame_preview.pack(pady=(15, 10), padx=20, fill="both", expand=True)
        
        # 1. Cabecera del panel
        self.frame_textos = ctk.CTkFrame(self.frame_preview, fg_color="transparent")
        self.frame_textos.pack(fill="x", padx=10, pady=(5, 0))
        
        self.lbl_estado = ctk.CTkLabel(self.frame_textos, text="Esperando capturas...", font=("Arial", 11, "italic"), text_color="#aaaaaa")
        self.lbl_estado.pack(side="left")
        
        self.lbl_filename = ctk.CTkLabel(self.frame_textos, text="", font=("Arial", 11, "bold"), text_color="#ffffff")
        self.lbl_filename.pack(side="right")
        
        # 2. Contenedor central (Flecha <-  Imagen -> Flecha)
        self.preview_inner = ctk.CTkFrame(self.frame_preview, fg_color="transparent")
        self.preview_inner.pack(fill="both", expand=True, padx=5, pady=(10, 5))
        self.preview_inner.columnconfigure(1, weight=1) # La imagen toma el centro
        
        # Botón Izquierda
        self.btn_izq = ctk.CTkButton(self.preview_inner, text="◄", width=30, height=80, fg_color="#2b2b2b", hover_color="#3a3a3a", state="disabled", command=self.mostrar_anterior)
        self.btn_izq.grid(row=0, column=0, padx=(0, 5))
        
        # Botón Central (Es la imagen en sí misma)
        # Usamos un botón en lugar de un Label para detectar el clic fácilmente
        self.btn_thumb = ctk.CTkButton(self.preview_inner, text="🖼️\nNo hay imágenes", font=("Segoe UI Emoji", 20), fg_color="#2b2b2b", hover_color="#3a3a3a", corner_radius=6, state="disabled", command=self.copiar_imagen_actual)
        self.btn_thumb.grid(row=0, column=1, sticky="nsew")
        
        # Botón Derecha
        self.btn_der = ctk.CTkButton(self.preview_inner, text="►", width=30, height=80, fg_color="#2b2b2b", hover_color="#3a3a3a", state="disabled", command=self.mostrar_siguiente)
        self.btn_der.grid(row=0, column=2, padx=(5, 0))
        
        # 3. Botón para abrir la carpeta abajo (Opcional, pero útil)
        self.btn_open_img = ctk.CTkButton(self.frame_preview, text="🔍 Abrir Imagen Original", fg_color="#1f538d", height=28, state="disabled", command=self.abrir_imagen_actual)
        self.btn_open_img.pack(fill="x", padx=10, pady=(0, 10))
        self.btn_open_img.pack(side="bottom", fill="x")  
        # Al terminar de dibujar la interfaz, cargamos el historial
        self.cargar_historial_carpeta()
 
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

    def cargar_historial_carpeta(self):
        """Lee la carpeta de guardado y carga los nombres de los archivos en memoria (súper ligero)"""
        if not os.path.exists(self.ruta_guardado):
            return
            
        # Busca todos los archivos .png y los ordena por fecha (el más nuevo al final)
        archivos = sorted(Path(self.ruta_guardado).glob("*.png"), key=os.path.getmtime)
        
        # Guardamos solo el texto de la ruta, lo cual no consume casi nada de RAM
        self.historial_rutas = [str(ruta) for ruta in archivos]
        
        if self.historial_rutas:
            self.indice_actual = len(self.historial_rutas) - 1
            # Importante: pasamos prevent_append=True para no duplicar en el historial
            self.actualizar_vista_previa(prevent_append=True)


    def actualizar_vista_previa(self, ruta_imagen=None, prevent_append=False):
        """Añade una imagen al historial y/o actualiza la vista con el índice actual"""
        
        # Si recibimos una ruta nueva y NO estamos solo iniciando, la añadimos al final
        if ruta_imagen and not prevent_append:
            self.historial_rutas.append(ruta_imagen)
            self.indice_actual = len(self.historial_rutas) - 1

        if not self.historial_rutas or self.indice_actual < 0:
            return

        ruta_mostrar = self.historial_rutas[self.indice_actual]
        total_imgs = len(self.historial_rutas)

        try:
            img = Image.open(ruta_mostrar)
            resample_metodo = getattr(Image.Resampling, 'LANCZOS', Image.BILINEAR)
            img_recortada = ImageOps.fit(img, (140, 80), resample_metodo)
            
            ctk_img = ctk.CTkImage(light_image=img_recortada, dark_image=img_recortada, size=(140, 80))
            
            # --- SOLUCIÓN A LA FUGA DE MEMORIA ---
            img.close() # Liberamos la imagen original de la RAM inmediatamente
            
            self.btn_thumb.configure(image=ctk_img, text="", state="normal")
            
            nombre_archivo = Path(ruta_mostrar).name
            if len(nombre_archivo) > 20:
                nombre_archivo = nombre_archivo[:17] + "..."
                
            self.lbl_estado.configure(text=f"Imagen {self.indice_actual + 1} de {total_imgs}")
            self.lbl_filename.configure(text=nombre_archivo)
            
            self.btn_izq.configure(state="normal" if self.indice_actual > 0 else "disabled")
            self.btn_der.configure(state="normal" if self.indice_actual < total_imgs - 1 else "disabled")
            self.btn_open_img.configure(state="normal")
            
        except Exception as e:
            print(f"Error menor al cargar miniatura: {e}")
    # -------------------------------------------------------------------------
    # MÉTODOS DE CAPTURA
    # -------------------------------------------------------------------------
    def captura_completa(self):
        self.root.withdraw()
        self.root.after(300, self._hacer_captura_completa)
 
    def _hacer_captura_completa(self):
        try:
            ruta = self.preparar_carpeta()
            
            with mss.mss() as sct:
                # monitor[0] representa la suma de todas las pantallas conectadas
                monitor = sct.monitors[0]
                sct_img = sct.grab(monitor)
                
                # Convertimos el formato nativo de mss a un objeto Image de PIL
                captura = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                captura.save(ruta)
                captura.close()

            # Solo copiar si el switch está activado
            if self.var_portapapeles.get():
                self.copiar_al_portapapeles(ruta)
            self.actualizar_vista_previa(ruta)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
        self.root.deiconify()
 
    def iniciar_recorte(self):
        self.root.withdraw()
        self.root.after(300, self._crear_capa_recorte)
 
    def _crear_capa_recorte(self):
        # 1. Tomar captura de todas las pantallas en segundo plano con mss
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            self.pantalla_completa_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        # 2. Configurar la ventana transparente de recorte
        self.ventana_recorte = tk.Toplevel()
        self.ventana_recorte.attributes("-alpha", 0.3)
        self.ventana_recorte.overrideredirect(True) # Oculta la barra de título y bordes de Windows
        self.ventana_recorte.config(cursor="cross")
 
        # 3. Calcular el tamaño del "Escritorio Virtual" (todas las pantallas juntas)
        # x e y detectan si tienes un monitor a la izquierda o arriba (coordenadas negativas)
        x = self.root.winfo_vrootx()
        y = self.root.winfo_vrooty()
        w = self.root.winfo_vrootwidth()
        h = self.root.winfo_vrootheight()
        
        # Expandir la ventana sobre todas las coordenadas detectadas
        self.ventana_recorte.geometry(f"{w}x{h}+{x}+{y}")
 
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
        
        # 1. Obtener dimensiones del lienzo (Tkinter) y de la imagen real (mss)
        tk_w = self.canvas.winfo_width()
        tk_h = self.canvas.winfo_height()
        img_w, img_h = self.pantalla_completa_img.size
        
        # 2. Convertir coordenadas de Tkinter a coordenadas reales de la imagen usando porcentajes
        x1 = int((min(self.inicio_x, fin_x) / tk_w) * img_w)
        y1 = int((min(self.inicio_y, fin_y) / tk_h) * img_h)
        x2 = int((max(self.inicio_x, fin_x) / tk_w) * img_w)
        y2 = int((max(self.inicio_y, fin_y) / tk_h) * img_h)
        
        self.ventana_recorte.destroy()
 
        if x2 - x1 > 5 and y2 - y1 > 5:
            try:
                ruta = self.preparar_carpeta()
                
                # 3. Recortar usando las coordenadas perfectamente ajustadas
                imagen_recortada = self.pantalla_completa_img.crop((x1, y1, x2, y2))
                imagen_recortada.save(ruta)
                imagen_recortada.close()

                # Solo copiar si el switch está activado
                if self.var_portapapeles.get():
                    self.copiar_al_portapapeles(ruta)
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

    def copiar_al_portapapeles(self, ruta_imagen):
        """Copia la imagen guardada al portapapeles de Windows sin librerías extra."""
        if platform.system() == "Windows":
            try:
                comando = [
                    "powershell",
                    "-command",
                    f"Add-Type -AssemblyName System.Windows.Forms; [Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{ruta_imagen}'))"
                ]
                # 0x08000000 es CREATE_NO_WINDOW, evita que parpadee la consola
                subprocess.run(comando, creationflags=0x08000000)
            except Exception as e:
                print(f"[❌] Error al copiar al portapapeles: {e}")
                
    def guardar_config_switch(self):
        """Guarda el estado del switch en el archivo config.json"""
        try:
            datos = cargar_configuracion()
            if "Opciones" not in datos or not isinstance(datos["Opciones"], dict):
                datos["Opciones"] = {}
                
            # Guardamos True o False dependiendo de si el switch está activado
            datos["Opciones"]["copiar_portapapeles"] = self.var_portapapeles.get()
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[❌] Error al guardar config del switch: {e}")


    def mostrar_anterior(self):
        if self.indice_actual > 0:
            self.indice_actual -= 1
            self.actualizar_vista_previa()

    def mostrar_siguiente(self):
        if self.indice_actual < len(self.historial_rutas) - 1:
            self.indice_actual += 1
            self.actualizar_vista_previa()

    def copiar_imagen_actual(self):
        """Se ejecuta al hacer clic sobre la miniatura"""
        if self.indice_actual >= 0 and self.indice_actual < len(self.historial_rutas):
            ruta = self.historial_rutas[self.indice_actual]
            self.copiar_al_portapapeles(ruta)
            
            # Un pequeño feedback visual temporal
            texto_original = self.lbl_estado.cget("text")
            self.lbl_estado.configure(text="¡Copiado al portapapeles! ✓", text_color="#00ff00")
            # Restaurar texto después de 1.5 segundos
            self.root.after(1500, lambda: self.lbl_estado.configure(text=texto_original, text_color="#aaaaaa"))

    def abrir_imagen_actual(self):
        if self.indice_actual >= 0:
            self.abrir_ubicacion(self.historial_rutas[self.indice_actual])

    
 
if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
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