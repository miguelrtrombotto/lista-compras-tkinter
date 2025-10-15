import tkinter as tk
from tkinter import ttk

def main():
    root = tk.Tk()
    root.title("Lista de compras")
    root.geometry("480x420")

    container = ttk.Frame(root, padding=12)
    container.pack(fill="both", expand=True)
    ttk.Label(container, text="Ventana base lista").pack(anchor="w")

    root.mainloop()

if __name__ == "__main__":
    main()