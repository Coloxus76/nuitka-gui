import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import ast
import shutil
import time
from PIL import Image

# ==============================================================================
# MAPA COMPLETO: nombre_de_import -> plugin_de_nuitka
# ==============================================================================
IMPORT_TO_PLUGIN = {
    "tkinter":        "tk-inter",
    "_tkinter":       "tk-inter",
    "customtkinter":  "tk-inter",
    "kivy":           "kivy",
    "kivymd":         "kivy",
    "PyQt5":          "pyqt5",
    "PyQt6":          "pyqt6",
    "PySide2":        "pyside2",
    "PySide6":        "pyside6",
    "wx":             "wx",
    "gi":             "gi",
    "numpy":          "numpy",
    "scipy":          "numpy",
    "matplotlib":     "matplotlib",
    "pandas":         "pandas",
    "sklearn":        "sklearn",
    "tensorflow":     "tensorflow",
    "keras":          "tensorflow",
    "torch":          "torch",
    "cv2":            "opencv",
    # "PIL":            "pil",
    # "Pillow":         "pil",
    "upx":            "upx",
    "eventlet":       "eventlet",
    "gevent":         "gevent",
    "trio":           "trio",
    "asyncio":        "asyncio",
    "sqlalchemy":     "sqlalchemy",
    "django":         "django",
    "pkg_resources":  "pkg-resources",
    "setuptools":     "pkg-resources",
    "multiprocessing":"multiprocessing",
}

ALL_PLUGINS = sorted(set(IMPORT_TO_PLUGIN.values()))


# ==============================================================================
# POPUP: Editor manual de plugins
# ==============================================================================
class PluginEditorPopup(ctk.CTkToplevel):
    def __init__(self, parent, plugin_vars: dict, on_close_callback):
        super().__init__(parent)
        self.title("Editar Plugins Manualmente")
        self.geometry("520x500")
        self.resizable(False, False)
        self.grab_set()  # Modal
        self.on_close_callback = on_close_callback
        self.plugin_vars = plugin_vars

        ctk.CTkLabel(self, text="Plugins de Nuitka", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(self, text="Activá o desactivá plugins manualmente:",
                     font=("Arial", 12), text_color="gray").pack(pady=(0, 10))

        # Frame scrollable con checkboxes
        scroll = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        cols = 3
        for i, p in enumerate(ALL_PLUGINS):
            cb = ctk.CTkCheckBox(scroll, text=p, variable=self.plugin_vars[p], font=("Arial", 12))
            cb.grid(row=i // cols, column=i % cols, padx=15, pady=6, sticky="w")

        # Botones inferiores
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(btn_frame, text="Desmarcar Todos", fg_color="#400", hover_color="#600",
                      command=self.deselect_all).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(btn_frame, text="Aceptar", fg_color="#007acc", hover_color="#005fa3",
                      command=self.close_popup).pack(side="right", expand=True, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.close_popup)

    def deselect_all(self):
        for var in self.plugin_vars.values():
            var.set(False)

    def close_popup(self):
        self.on_close_callback()
        self.destroy()


# ==============================================================================
# VENTANA PRINCIPAL
# ==============================================================================
class NuitkaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Nuitka GUI Compiler v2.5.0")
        self.geometry("900x950")
        ctk.set_appearance_mode("dark")

        self.script_path = ""
        self.icon_path = ""
        self.extra_files = []
        self.extra_dirs  = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------
        # COLUMNA IZQUIERDA
        # -------------------------------------------------------
        self.frame_left = ctk.CTkFrame(self, corner_radius=15, border_width=1, border_color="#333")
        self.frame_left.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_left, text="Project Explorer", font=("Arial", 18, "bold")).pack(pady=10)

        self.load_frame = ctk.CTkFrame(self.frame_left, fg_color="#121212", border_width=2, border_color="#444")
        self.load_frame.pack(fill="x", padx=15, pady=5)
        self.btn_load = ctk.CTkButton(
            self.load_frame, text="1. Script Principal (.py)", font=("Arial", 14),
            fg_color="#007acc", hover_color="#005fa3", command=self.select_file
        )
        self.btn_load.pack(padx=10, pady=10, fill="x")
        self.lbl_selected = ctk.CTkLabel(self.load_frame, text="Ningún script seleccionado",
                                         wraplength=180, text_color="gray")
        self.lbl_selected.pack(pady=5)

        ctk.CTkLabel(self.frame_left, text="Recursos Adicionales", font=("Arial", 14, "bold")).pack(pady=(20, 5))
        ctk.CTkButton(self.frame_left, text="+ Añadir Archivos (.ini, .txt, .db)",
                      fg_color="#333", hover_color="#444", command=self.add_extra_files).pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(self.frame_left, text="+ Añadir Carpeta (Imágenes, Assets)",
                      fg_color="#333", hover_color="#444", command=self.add_extra_dir).pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(self.frame_left, text="Limpiar Lista de Recursos",
                      fg_color="#400", hover_color="#600", command=self.clear_extra_resources).pack(padx=20, pady=10, fill="x")

        self.extra_list_text = ctk.CTkTextbox(self.frame_left, height=200, font=("Consolas", 11), fg_color="#000")
        self.extra_list_text.pack(padx=15, pady=10, fill="both", expand=True)
        self.update_extra_list_visual()

        # -------------------------------------------------------
        # COLUMNA DERECHA
        # -------------------------------------------------------
        self.frame_right = ctk.CTkScrollableFrame(self, corner_radius=15)
        self.frame_right.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        # --- Opciones de compilación + preview icono ---
        self.top_config_frame = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        self.top_config_frame.pack(fill="x", pady=5)

        self.build_opts_frame = ctk.CTkFrame(self.top_config_frame, fg_color="transparent")
        self.build_opts_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(self.build_opts_frame, text="Opciones de Compilación",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10)
        self.onefile_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.build_opts_frame, text="Modo Portable (OneFile)",
                        variable=self.onefile_var).pack(pady=5, anchor="w", padx=20)
        self.console_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.build_opts_frame, text="Ocultar Consola (Modo Ventana)",
                        variable=self.console_var).pack(pady=5, anchor="w", padx=20)

        # Preview icono
        self.icon_preview_frame = ctk.CTkFrame(self.top_config_frame, fg_color="transparent")
        self.icon_preview_frame.pack(side="right", padx=20)

        ctk.CTkButton(self.icon_preview_frame, text="Seleccionar Icono",
                      command=self.select_icon).pack(pady=5)

        self.preview_border = ctk.CTkFrame(self.icon_preview_frame, width=74, height=74,
                                           fg_color="#333", corner_radius=10,
                                           border_width=2, border_color="#555")
        self.preview_border.pack(pady=5)
        self.preview_border.pack_propagate(False)

        self.preview_canvas = ctk.CTkLabel(self.preview_border, text="", fg_color="transparent")
        self.preview_canvas.pack(expand=True, fill="both")
        ctk.CTkLabel(self.icon_preview_frame, text="Preview",
                     font=("Arial", 10), text_color="gray").pack()

        # -------------------------------------------------------
        # SECCIÓN PLUGINS — chips + botón editar
        # -------------------------------------------------------
        plugin_header = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        plugin_header.pack(fill="x", padx=10, pady=(15, 0))

        ctk.CTkLabel(plugin_header, text="Plugins de Nuitka",
                     font=("Arial", 14, "bold")).pack(side="left")

        self.btn_edit_plugins = ctk.CTkButton(
            plugin_header, text="⚙ Editar manualmente",
            width=180, height=28, font=("Arial", 12),
            fg_color="#333", hover_color="#444",
            command=self.open_plugin_editor
        )
        self.btn_edit_plugins.pack(side="right")

        self.btn_autodetect = ctk.CTkButton(
            plugin_header, text="⟳ Auto-detectar",
            width=140, height=28, font=("Arial", 12),
            fg_color="#1a5c1a", hover_color="#256625",
            command=self.autodetect_plugins
        )
        self.btn_autodetect.pack(side="right", padx=(0, 8))

        # Panel de chips — fondo sutil, altura fija compacta
        self.chips_outer = ctk.CTkFrame(self.frame_right, fg_color="#111",
                                        corner_radius=10, border_width=1, border_color="#2a2a2a")
        self.chips_outer.pack(fill="x", padx=10, pady=(6, 0))

        self.lbl_no_plugins = ctk.CTkLabel(
            self.chips_outer,
            text="Ningún plugin activo — cargá un script y usá Auto-detectar",
            font=("Arial", 11, "italic"), text_color="#555"
        )
        self.lbl_no_plugins.pack(pady=14)

        # Frame interno donde van los chips (se muestra solo cuando hay plugins)
        self.chips_inner = ctk.CTkFrame(self.chips_outer, fg_color="transparent")

        # Variables internas de plugins (no visibles directamente en UI)
        self.plugin_vars = {p: ctk.BooleanVar(value=False) for p in ALL_PLUGINS}

        # --- Metadatos ---
        self.group_meta = ctk.CTkFrame(self.frame_right, border_width=1, border_color="#333")
        self.group_meta.pack(fill="x", pady=15, padx=5)
        ctk.CTkLabel(self.group_meta, text="Metadatos de Propiedades",
                     font=("Arial", 14, "bold")).pack(pady=5, padx=10, anchor="w")

        self.ent_app_name  = self.create_input(self.group_meta, "Nombre Aplicación:", "Nombre del Producto/Descripción")
        self.ent_copyright = self.create_input(self.group_meta, "Copyright:", "© 2026 Hector Bertorello")
        self.ent_ver       = self.create_input(self.group_meta, "Versión:", "1.0.0.0")

        # --- Salida ---
        ctk.CTkLabel(self.frame_right, text="Carpeta de Salida",
                     font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 0), padx=10)
        output_frame = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        output_frame.pack(fill="x", padx=10)

        self.ent_output = ctk.CTkEntry(output_frame, placeholder_text="Ruta de destino")
        self.ent_output.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
        ctk.CTkButton(output_frame, text="...", width=40,
                      command=self.select_output_dir).pack(side="right")

        self.cleanup_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.frame_right, text="Limpiar archivos temporales al finalizar",
                        variable=self.cleanup_var).pack(anchor="w", padx=20, pady=(0, 5))

        self.btn_build = ctk.CTkButton(
            self.frame_right, text="COMPILAR APLICACIÓN", height=60,
            font=("Arial", 16, "bold"), fg_color="#007acc", hover_color="#005fa3",
            command=self.start_build_thread
        )
        self.btn_build.pack(fill="x", pady=25, padx=10)

        # --- Log ---
        self.log_text = ctk.CTkTextbox(self, height=180, fg_color="#000",
                                       text_color="#0f0", font=("Consolas", 12))
        self.log_text.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 20), sticky="nsew")

    # ===========================================================
    # CHIPS
    # ===========================================================

    def refresh_chips(self):
        """Reconstruye los chips según los plugin_vars activos."""
        # Limpiar chips anteriores
        for widget in self.chips_inner.winfo_children():
            widget.destroy()

        active = [p for p, v in self.plugin_vars.items() if v.get()]

        if not active:
            self.chips_inner.pack_forget()
            self.lbl_no_plugins.pack(pady=14)
            return

        self.lbl_no_plugins.pack_forget()
        self.chips_inner.pack(fill="x", padx=10, pady=10)

        # Chips con "×" para quitar individualmente
        row_frame = None
        for i, plugin in enumerate(active):
            if i % 4 == 0:
                row_frame = ctk.CTkFrame(self.chips_inner, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)

            chip = ctk.CTkFrame(row_frame, fg_color="#1e3a5f", corner_radius=20,
                                border_width=1, border_color="#3a6ea8")
            chip.pack(side="left", padx=4)

            ctk.CTkLabel(chip, text=plugin, font=("Arial", 11, "bold"),
                         text_color="#7ec8e3", padx=8, pady=4).pack(side="left")

            # Botón × para quitar el chip
            p_ref = plugin
            ctk.CTkButton(
                chip, text="×", width=18, height=18,
                font=("Arial", 11, "bold"),
                fg_color="transparent", hover_color="#2a4a6f",
                text_color="#aaa",
                command=lambda p=p_ref: self.remove_chip(p)
            ).pack(side="right", padx=(0, 4))

    def remove_chip(self, plugin_name: str):
        self.plugin_vars[plugin_name].set(False)
        self.refresh_chips()
        self.log(f"Plugin removido: {plugin_name}")

    # ===========================================================
    # POPUP EDITOR
    # ===========================================================

    def open_plugin_editor(self):
        PluginEditorPopup(self, self.plugin_vars, on_close_callback=self.refresh_chips)

    # ===========================================================
    # AUTO-DETECCIÓN
    # ===========================================================

    def extract_imports(self, filepath: str) -> set:
        imports = set()
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
            tree = ast.parse(source, filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
        except SyntaxError as e:
            self.log(f"⚠ SyntaxError al parsear: {e}")
        except Exception as e:
            self.log(f"⚠ Error al analizar imports: {e}")
        return imports

    def autodetect_plugins(self):
        if not self.script_path:
            messagebox.showwarning("Auto-detectar", "Primero seleccioná un script principal (.py)")
            return

        imports = self.extract_imports(self.script_path)
        detected = set()

        for module in imports:
            plugin = IMPORT_TO_PLUGIN.get(module)
            if plugin:
                detected.add(plugin)

        for name, var in self.plugin_vars.items():
            var.set(name in detected)

        self.refresh_chips()

        if detected:
            self.log(f"🔍 Plugins detectados: {', '.join(sorted(detected))}")
        else:
            self.log("🔍 No se detectaron plugins necesarios.")

    # ===========================================================
    # AUXILIARES
    # ===========================================================

    def select_icon(self):
        icon = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.ico *.png *.jpg *.jpeg"), ("Todos", "*.*")])
        if icon:
            self.icon_path = icon
            try:
                img = Image.open(icon).resize((60, 60))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                self.preview_canvas.configure(image=ctk_img, text="")
                self.log(f"Icono: {os.path.basename(icon)}")
            except Exception as e:
                self.log(f"Error preview icono: {e}")

    def create_input(self, master, label_text, placeholder):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def update_extra_list_visual(self):
        self.extra_list_text.configure(state="normal")
        self.extra_list_text.delete("1.0", "end")
        self.extra_list_text.insert("end", "--- RECURSOS INCLUIDOS ---\n")
        for f in self.extra_files:
            self.extra_list_text.insert("end", f"📄 FILE: {os.path.basename(f)}\n")
        for d in self.extra_dirs:
            self.extra_list_text.insert("end", f"📁 DIR:  {os.path.basename(d)}/\n")
        self.extra_list_text.configure(state="disabled")

    def add_extra_files(self):
        files = filedialog.askopenfilenames(title="Seleccionar archivos extra")
        if files:
            self.extra_files.extend(list(files))
            self.update_extra_list_visual()

    def add_extra_dir(self):
        directory = filedialog.askdirectory(title="Seleccionar carpeta de recursos")
        if directory:
            self.extra_dirs.append(directory)
            self.update_extra_list_visual()

    def clear_extra_resources(self):
        self.extra_files = []
        self.extra_dirs  = []
        self.update_extra_list_visual()

    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("Archivos Python", "*.py")])
        if file:
            self.script_path = file
            self.lbl_selected.configure(text=os.path.basename(file), text_color="#007acc")
            self.ent_output.delete(0, "end")
            self.ent_output.insert(0, os.path.dirname(file))
            self.autodetect_plugins()

    def select_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.ent_output.delete(0, "end")
            self.ent_output.insert(0, directory)

    def log(self, message):
        self.log_text.insert("end", f"\n> {message}")
        self.log_text.see("end")

    # ===========================================================
    # COMPILACIÓN
    # ===========================================================

    def start_build_thread(self):
        if not self.script_path:
            messagebox.showwarning("Error", "Debes cargar el script principal (.py)")
            return
        threading.Thread(target=self.run_nuitka, daemon=True).start()

    # def cleanup_temp_files(self, output_dir: str, base_name: str):
    #     """Elimina solo las carpetas temporales que genera Nuitka, respetando el resto."""
    #     import stat

    #     def force_remove(func, path, exc_info):
    #         """Handler: ante acceso denegado, fuerza permisos de escritura y reintenta."""
    #         try:
    #             os.chmod(path, stat.S_IWRITE)
    #             func(path)
    #         except Exception:
    #             pass  # Si sigue fallando, el reintento externo lo maneja

    #     temp_suffixes = [".dist", ".onefile-build", ".build"]
    #     for suffix in temp_suffixes:
    #         target = os.path.join(output_dir, f"{base_name}{suffix}")
    #         if os.path.isdir(target):
    #             for attempt in range(1, 6):
    #                 try:
    #                     shutil.rmtree(target, onerror=force_remove)
    #                     if not os.path.isdir(target):
    #                         self.log(f"🗑 Eliminado: {base_name}{suffix}")
    #                         break
    #                     else:
    #                         raise Exception("Carpeta aún existe tras rmtree")
    #                 except Exception as e:
    #                     if attempt < 5:
    #                         self.log(f"⏳ Reintentando borrar {base_name}{suffix} ({attempt}/5)...")
    #                         time.sleep(2)
    #                     else:
    #                         self.log(f"⚠ No se pudo eliminar {base_name}{suffix}: {e}")

    def cleanup_temp_files(self, output_dir: str, base_name: str):
        import stat

        def force_remove(func, path, exc_info):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass

        # Si es standalone (no onefile), .dist ES el resultado — no borrarlo
        if self.onefile_var.get():
            temp_suffixes = [".onefile-build", ".build"]
        else:
            temp_suffixes = [".build"]  # Solo borra el build, respeta .dist

        for suffix in temp_suffixes:
            target = os.path.join(output_dir, f"{base_name}{suffix}")
            if os.path.isdir(target):
                for attempt in range(1, 6):
                    try:
                        shutil.rmtree(target, onerror=force_remove)
                        if not os.path.isdir(target):
                            self.log(f"🗑 Eliminado: {base_name}{suffix}")
                            break
                        else:
                            raise Exception("Carpeta aún existe tras rmtree")
                    except Exception as e:
                        if attempt < 5:
                            self.log(f"⏳ Reintentando borrar {base_name}{suffix} ({attempt}/5)...")
                            time.sleep(2)
                        else:
                            self.log(f"⚠ No se pudo eliminar {base_name}{suffix}: {e}")

    def run_nuitka(self):
        self.btn_build.configure(state="disabled", text="COMPILANDO...")
        cmd = ["python", "-m", "nuitka", "--standalone", "--no-progress", "--assume-yes-for-downloads"]

        for plugin, var in self.plugin_vars.items():
            if var.get():
                cmd.append(f"--enable-plugin={plugin}")

        cmd.append("--include-module=pywin32_bootstrap")

        for f in self.extra_files:
            cmd.append(f'--include-data-files="{f}={os.path.basename(f)}"')
        for d in self.extra_dirs:
            cmd.append(f'--include-data-dir="{d}={os.path.basename(d)}"')

        if self.onefile_var.get():
            cmd.extend(["--onefile", "--onefile-no-compression",
                        "--onefile-cache-mode=cached"])

        cmd.append("--windows-console-mode=disable" if self.console_var.get()
                   else "--windows-console-mode=force")

        base_name = os.path.splitext(os.path.basename(self.script_path))[0]
        cmd.append(f'--output-filename="{base_name}.exe"')

        app_display_name = self.ent_app_name.get() or base_name
        version          = self.ent_ver.get()       or "1.0.0.0"
        copyright_txt    = self.ent_copyright.get() or "© 2026 Hector Bertorello"

        cmd.extend([
            f'--product-name="{app_display_name}"',
            f'--file-description="{app_display_name}"',
            f'--file-version="{version}"',
            f'--product-version="{version}"',
            f'--copyright="{copyright_txt}"',
        ])

        if self.icon_path:
            cmd.append(f'--windows-icon-from-ico="{self.icon_path}"')

        output_dir = self.ent_output.get()
        cmd.append(f'--output-dir="{output_dir}"')
        cmd.append(f'"{self.script_path}"')

        try:
            process = subprocess.Popen(
                " ".join(cmd), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, shell=True
            )
            for line in process.stdout:
                self.log(line.strip())
            process.wait()

            if process.returncode == 0:
                self.log("--- COMPILACIÓN EXITOSA ---")
                # Limpieza controlada desde Python
                if self.cleanup_var.get():
                    self.log("🧹 Esperando que el sistema libere los archivos...")
                    time.sleep(4)
                    self.log("🧹 Limpiando archivos temporales de Nuitka...")
                    self.cleanup_temp_files(output_dir, base_name)
                    self.log("✅ Limpieza completada.")
                try:
                    os.startfile(output_dir)
                except Exception:
                    pass
            else:
                self.log(f"--- ERROR: CÓDIGO {process.returncode} ---")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")

        self.btn_build.configure(state="normal", text="COMPILAR APLICACIÓN")
        messagebox.showinfo("Nuitka GUI", "Compilación completada.")


def main():
    app = NuitkaGUI()
    app.mainloop()

if __name__ == "__main__":
    main()