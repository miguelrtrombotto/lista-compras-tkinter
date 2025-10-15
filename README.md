# lista-compras-tkinter
Proyecto 01 con el Informatorio, Solo
Requisitos (Python 3.10+)
Cómo correr: python src/main.py
Atajos: Ctrl+S, Ctrl+O, Delete, Enter, Doble clic
Flujo de trabajo (Issues → ramas → PR → Merge)

Windows:
git clone https://github.com/miguelrtrombotto/lista-compras-tkinter
cd lista-compras-tkinter
python -m venv .venv
..venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py

macOS/Linux:
git clone REPO_URL
cd REPO
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/main.py

Nota Linux: Instalar Tk si falta.

Debian/Ubuntu: sudo apt-get install python3-tk
Fedora: sudo dnf install python3-tkinter
Arch: sudo pacman -S tk