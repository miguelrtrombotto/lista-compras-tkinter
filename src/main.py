import tkinter as tk
from tkinter import ttk, messagebox

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lista de compras")
        self.root.geometry("700x520")
        self.items = []  # {"text": str, "done": bool}

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # Formulario
        form = ttk.Frame(main)
        form.pack(fill="x")
        ttk.Label(form, text="Ítem:").grid(row=0, column=0, padx=(0,6))
        self.var_item = tk.StringVar()
        entry = ttk.Entry(form, textvariable=self.var_item)
        entry.grid(row=0, column=1, sticky="ew")
        form.columnconfigure(1, weight=1)
        ttk.Button(form, text="Agregar", command=self.add_item).grid(row=0, column=2, padx=(8,0))
        entry.bind("<Return>", lambda e: self.add_item())

        # Tabla
        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True, pady=8)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("item","hecho"),
            show="headings",
            height=14
        )
        self.tree.heading("item", text="Ítem")
        self.tree.heading("hecho", text="Hecho")
        self.tree.column("item", width=520, anchor="w")
        self.tree.column("hecho", width=80, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        # Estado
        self.status = tk.StringVar(value="0 ítems · 0 hechos")
        ttk.Label(self.root, textvariable=self.status, anchor="w").pack(fill="x", padx=12, pady=(0,8))

    def add_item(self):
        text = (self.var_item.get() or "").strip()
        if not text:
            messagebox.showinfo("Info", "Escribe un ítem.")
            return
        self.items.append({"text": text, "done": False})
        self.var_item.set("")
        self.render()
        self.update_status()

    def render(self):
        self.tree.delete(*self.tree.get_children())
        for it in self.items:
            self.tree.insert("", "end", values=(it["text"], "✔" if it["done"] else ""))

    def update_status(self):
        total = len(self.items)
        done = sum(1 for i in self.items if i["done"])
        self.status.set(f"{total} ítems · {done} hechos")

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()