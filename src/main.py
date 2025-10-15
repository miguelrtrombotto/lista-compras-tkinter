import tkinter as tk  # tkinter para GUI
from tkinter import ttk, messagebox  # messagebox para diálogos
from tkinter import filedialog  # filedialog para abrir/guardar archivos
import json  # json para guardar/cargar en formato JSON
from pathlib import Path  # Path para manejo de rutas

CATEGORIAS_PREDEFINIDAS = [
    "General", "Almacén", "Frescos", "Bebidas", "Limpieza", "Higiene", "Otros"
]

class App:
    def __init__(self, root: tk.Tk):  # Inicialización de la app
        self.root = root
        self.root.title("Lista de compras")
        self.root.geometry("840x560")
        self.current_file = None

        # Modelo: lista de dicts
        # {"text": str, "done": bool, "cantidad": int, "categoria": str}
        self.items = []

        # Estado de edición en línea
        self._editor = None          # widget de edición (Entry o Combobox)
        self._editor_item_id = None  # item de Treeview en edición
        self._editor_col = None      # índice de columna en edición

        self._build_ui()
        self._bind_shortcuts()
        self.render()
        self.update_status()

    def _build_ui(self):  # Construcción de la UI
        # Contenedor principal
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # Formulario
        form = ttk.Frame(main)
        form.pack(fill="x")
        ttk.Label(form, text="Ítem:").grid(row=0, column=0, padx=(0, 6))
        self.var_item = tk.StringVar()
        entry = ttk.Entry(form, textvariable=self.var_item)
        entry.grid(row=0, column=1, sticky="ew")
        form.columnconfigure(1, weight=1)
        ttk.Button(form, text="Agregar", command=self.add_item).grid(row=0, column=2, padx=(8, 0))
        entry.bind("<Return>", lambda e: self.add_item())

        # Barra de acciones
        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(6, 0))
        ttk.Button(actions, text="Eliminar seleccionado(s)", command=self.delete_selected).pack(side="left")
        ttk.Button(actions, text="Limpiar lista", command=self.clear_list).pack(side="left", padx=6)
        ttk.Button(actions, text="Guardar (Ctrl+S)", command=self.save_json).pack(side="left", padx=6)
        ttk.Button(actions, text="Abrir (Ctrl+O)", command=self.load_json).pack(side="left", padx=6)

        # Tabla
        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True, pady=8)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("item", "cantidad", "categoria", "hecho"),
            show="headings",
            height=16
        )
        self.tree.heading("item", text="Ítem")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("hecho", text="Hecho")

        self.tree.column("item", width=520, anchor="w")
        self.tree.column("cantidad", width=90, anchor="center")
        self.tree.column("categoria", width=150, anchor="center")
        self.tree.column("hecho", width=70, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        # Interacciones
        # Doble clic en celda: edita; si es "hecho", alterna ✔
        self.tree.bind("<Double-1>", self.on_double_click)

        # Estado
        self.status = tk.StringVar(value="0 ítems · 0 hechos")
        ttk.Label(self.root, textvariable=self.status, anchor="w").pack(fill="x", padx=12, pady=(0, 8))

    def _bind_shortcuts(self):
        # Atajos útiles
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<Control-s>", lambda e: self.save_json())
        self.root.bind("<Control-o>", lambda e: self.load_json())
        # Confirmar/cancelar edición en línea
        self.root.bind("<Return>", self._finish_editor_if_any)
        self.root.bind("<Escape>", self._cancel_editor_if_any)

    # ------------------------------
    # CRUD / Lógica principal
    # ------------------------------
    def add_item(self):  # agregar ítem
        text = (self.var_item.get() or "").strip()
        if not text:  # vacío
            messagebox.showinfo("Info", "Escribe un ítem.")
            return
        if len(text) > 200:
            messagebox.showinfo("Info", "Máximo 200 caracteres.")
            return
        if any(i["text"].lower() == text.lower() for i in self.items):  # duplicados
            if not messagebox.askyesno("Duplicado", f"“{text}” ya existe. ¿Agregar de todos modos?"):
                return
        # Nuevos campos por defecto
        self.items.append({"text": text, "done": False, "cantidad": 1, "categoria": "General"})
        self.var_item.set("")  # limpiar
        self.render()
        self.update_status()

    def delete_selected(self):  # eliminar seleccionado(s)
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecciona filas para eliminar.")
            return
        indices = [self.tree.index(i) for i in sel]
        for idx in sorted(indices, reverse=True):
            self.items.pop(idx)
        self.render()
        self.update_status()

    def clear_list(self):  # limpiar lista
        if not self.items:
            return
        if messagebox.askyesno("Limpiar", "¿Seguro que quieres limpiar toda la lista?"):
            self.items.clear()
            self.render()
            self.update_status()

    # ------------------------------
    # Render y estado
    # ------------------------------
    def render(self):  # actualizar tabla
        # Cerrar editor si existe antes de redibujar
        self._destroy_editor()

        self.tree.delete(*self.tree.get_children())
        for it in self.items:
            self.tree.insert(
                "",
                "end",
                values=(
                    it.get("text", ""),
                    it.get("cantidad", 1),
                    it.get("categoria", "General"),
                    "✔" if it.get("done", False) else ""
                )
            )

    def update_status(self):  # actualizar estado
        total = len(self.items)
        done = sum(1 for i in self.items if i.get("done"))
        self.status.set(f"{total} ítems · {done} hechos")

    # ------------------------------
    # Edición en línea
    # ------------------------------
    def on_double_click(self, event):
        # Determinar región, fila y columna
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        item_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)  # '#1', '#2', ...
        if not item_id or not col_id:
            return

        col_index = int(col_id.replace("#", "")) - 1
        # 0=item, 1=cantidad, 2=categoria, 3=hecho
        if col_index == 3:
            # Alternar hecho
            idx = self.tree.index(item_id)
            self.items[idx]["done"] = not self.items[idx]["done"]
            self.render()
            self.update_status()
            return

        # Editar en línea otras columnas
        self.start_inline_editor(item_id, col_index)

    def start_inline_editor(self, item_id, col_index):
        # Cerrar editor previo si existe
        self._destroy_editor()

        bbox = self.tree.bbox(item_id, f"#{col_index+1}")
        if not bbox:
            return
        x, y, w, h = bbox

        # Editor como hijo del Treeview, para usar coords relativas a la celda
        idx = self.tree.index(item_id)
        item = self.items[idx]

        if col_index == 2:
            # Categoría: Combobox readonly
            editor = ttk.Combobox(self.tree, values=CATEGORIAS_PREDEFINIDAS, state="readonly")
            editor.set(item.get("categoria", "General") or "General")
        else:
            # Ítem o Cantidad: Entry
            editor = ttk.Entry(self.tree)
            if col_index == 0:
                editor.insert(0, item.get("text", ""))
            elif col_index == 1:
                editor.insert(0, str(item.get("cantidad", 1)))

        editor.place(x=x, y=y, width=w, height=h)
        editor.focus_set()
        try:
            editor.select_range(0, "end")
        except Exception:
            pass

        # Guardar/cancelar por eventos
        editor.bind("<FocusOut>", lambda e: self.finish_inline_editor(save=True))
        editor.bind("<Return>", lambda e: self.finish_inline_editor(save=True))
        editor.bind("<Escape>", lambda e: self.finish_inline_editor(save=False))

        self._editor = editor
        self._editor_item_id = item_id
        self._editor_col = col_index

    def finish_inline_editor(self, save: bool):
        self._finish_editor(save)

    def _finish_editor_if_any(self, event=None):
        if self._editor is not None:
            self._finish_editor(save=True)

    def _cancel_editor_if_any(self, event=None):
        if self._editor is not None:
            self._finish_editor(save=False)

    def _finish_editor(self, save: bool):
        if self._editor is None or self._editor_item_id is None or self._editor_col is None:
            self._destroy_editor()
            return

        item_id = self._editor_item_id
        col_index = self._editor_col
        editor = self._editor
        idx = self.tree.index(item_id)

        if save:
            val = (editor.get() if hasattr(editor, "get") else "").strip()
            if col_index == 0:
                # Ítem
                if not val:
                    messagebox.showinfo("Info", "El ítem no puede estar vacío.")
                    self._destroy_editor()
                    return
                if len(val) > 200:
                    messagebox.showinfo("Info", "Máximo 200 caracteres.")
                    self._destroy_editor()
                    return
                self.items[idx]["text"] = val
            elif col_index == 1:
                # Cantidad
                if not self._is_positive_int(val):
                    messagebox.showinfo("Info", "Cantidad debe ser un entero positivo (>= 1).")
                    self._destroy_editor()
                    return
                self.items[idx]["cantidad"] = int(val)
            elif col_index == 2:
                # Categoría
                self.items[idx]["categoria"] = val or "General"

        self._destroy_editor()
        self.render()
        self.update_status()

    def _destroy_editor(self):
        if self._editor is not None:
            try:
                self._editor.destroy()
            except Exception:
                pass
        self._editor = None
        self._editor_item_id = None
        self._editor_col = None

    @staticmethod
    def _is_positive_int(s: str) -> bool:
        try:
            return int(s) >= 1
        except Exception:
            return False

    # ------------------------------
    # Guardar / Abrir JSON (compatibilidad hacia atrás)
    # ------------------------------
    def save_json(self):  # guardar archivo json
        if not self.current_file:
            path = filedialog.asksaveasfilename(
                title="Guardar lista",
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
                initialfile="lista_compras.json",
            )
            if not path:
                return
            self.current_file = Path(path)
        try:
            # Normalizar datos antes de guardar
            data = []
            for it in self.items:
                data.append({
                    "text": it.get("text", ""),
                    "done": bool(it.get("done", False)),
                    "cantidad": int(it.get("cantidad", 1) or 1),
                    "categoria": str(it.get("categoria", "General") or "General"),
                })
            self.current_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.status.set(f"Guardado en {self.current_file.name}")
            self.root.after(1800, self.update_status)
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    def load_json(self):  # abrir archivo json
        path = filedialog.askopenfilename(
            title="Abrir lista",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Formato inválido: se esperaba una lista.")
            items = []
            for it in data:
                if isinstance(it, dict):
                    items.append({
                        "text": str(it.get("text", "")),
                        "done": bool(it.get("done", False)),
                        "cantidad": int(it.get("cantidad", 1) or 1),
                        "categoria": str(it.get("categoria", "General") or "General"),
                    })
                else:
                    # Formato antiguo: solo texto
                    items.append({"text": str(it), "done": False, "cantidad": 1, "categoria": "General"})
            self.items = items
            self.current_file = Path(path)
            self.render()
            self.update_status()
        except Exception as e:
            messagebox.showerror("Error al abrir", str(e))

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()