#  Deep Terrain AI PS-Tool

A robust desktop GUI tool for pre-selecting and labeling images with scene-based attributes. Built with Python and Tkinter, this app streamlines the process of image selection, categorization, and dataset generation.

---

##  Features

-  Zoom and drag to explore images
-  Dark/Light mode toggle
-  Attribute tagging (class, action, accessories, age, gender, distance, time, occlusion)
-  Empty Frame disables irrelevant fields automatically
-  Folder navigation with search
-  Auto CSV logging and undo support
-  Save selections with metadata for dataset preparation
-  Overwrite confirmation for already-selected images

---

## 🛠 Requirements

- Python 3.7 or newer
- `pip` (Python package manager)

---

##  Installation

1. **Clone or Download** this repository.
2. **Install dependencies** via:

```bash
pip install -r requirements.txt
```

---

## ▶ Running the Application

Simply launch the GUI with:

```bash
python main.py
```

Make sure `main.py` contains your full application code.

---

## 🛠 Packaging for Desktop (Executable)

You can build standalone executables using **PyInstaller**:

### Step 1: Install PyInstaller (if not already)

```bash
pip install pyinstaller
```

### Step 2: Build the App

```bash
pyinstaller --noconfirm --onefile --windowed main.py
```

This will generate a standalone app inside the `dist/` folder.

---

## 🖥️ Platform Packaging Notes

###  Windows

- Output: `dist/main.exe`
- Run by double-clicking the `.exe` file
- Automatically runs as a GUI without terminal popups

###  macOS

- Output: `dist/main`
- Run with: `./main` or bundle it into a `.app` with additional flags

Optional: To create a native `.app` format:
```bash
pyinstaller --noconfirm --windowed --onefile --name "DeepTerrainTool" main.py
```

###  Linux

- Output: `dist/main`
- Make it executable:
```bash
chmod +x dist/main
./dist/main
```

---

##  Project Structure

```
.
├── main.py                # Main GUI application
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
└── dist/                  # Folder where PyInstaller outputs the final app
```

---

##  Contributions

Feel free to report issues, request features, or open PRs!

---

## Built With

- Python 
- Tkinter 
- PIL (Pillow) 
