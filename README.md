# Nuitka GUI 🐍➡️⚙️

A friendly graphical interface for [Nuitka](https://nuitka.net/), the Python-to-C compiler.  
No more memorizing long command-line flags — just point, click, and compile.

---

## ✨ Features

- **Auto-detects Nuitka plugins** by scanning your script's imports
- **OneFile or Standalone** mode toggle
- **Plugin chip editor** — add/remove plugins visually
- **Icon preview** — supports `.ico`, `.png`, `.jpg`
- **Extra files & folders** bundling (assets, databases, configs)
- **Windows metadata** — product name, version, copyright
- **Auto-cleanup** of temporary build files
- Real-time compilation log

---

## 📸 Screenshots

![Nuitka GUI Screenshot](https://raw.githubusercontent.com/Coloxus/nuitka-gui/main/assets/screenshot.png)
---

## ⚙️ Requirements

- Windows 10/11
- Python 3.10 or newer
- A C compiler accessible to Nuitka (MSVC, MinGW-w64, or Clang)

---

## 📦 Installation

```bash
pip install nuitka-gui
```

Then launch it from anywhere:

```bash
nuitka-gui
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/hbertorello/nuitka-gui.git
```

---

## 🚀 Usage

1. Click **"1. Script Principal (.py)"** and select your Python entry point.
2. The tool auto-detects required Nuitka plugins from your imports.
3. Adjust options: OneFile mode, hide console, icon, metadata.
4. Set the output folder.
5. Click **"COMPILAR APLICACIÓN"**.

### Supported plugin auto-detection

| Import in your script | Nuitka plugin enabled |
|-----------------------|-----------------------|
| `tkinter`, `customtkinter` | `tk-inter` |
| `PyQt5` / `PyQt6` | `pyqt5` / `pyqt6` |
| `PySide6` | `pyside6` |
| `numpy`, `scipy` | `numpy` |
| `torch` | `torch` |
| `PIL` / `Pillow` | `pil` |
| `cv2` | `opencv` |
| `django` | `django` |
| `sqlalchemy` | `sqlalchemy` |
| …and more | See source |

---

## 🗂️ Project structure

```
nuitka_gui/
├── __init__.py
└── main.py        ← full GUI source
```

---

## 🛠️ Development

```bash
git clone https://github.com/hbertorello/nuitka-gui.git
cd nuitka-gui
pip install -e .
nuitka-gui
```

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) and powered by [Nuitka](https://nuitka.net/).
