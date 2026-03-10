# LMU Setup Installer v6

A desktop application to install Le Mans Ultimate setup files (`.svm`) into the correct folder, based on the selected car and track.

Supports **compressed files** (.zip, .7z, .rar), **batch installation**, **parameter preview**, **history** and **rollback**.

---

## Features

### Setup installation
- **Automatic detection** of the LMU Settings folder
- **Automatic detection** of car and track from the `.svm` file contents
- **Manual selection** of car and track via dropdown menus
- **Overwrite** and **automatic backup** (`.svm.bak`) are configurable

### Compressed files
- Support for **.zip**, **.7z**, **.rar** archives
- Automatic extraction and recursive scanning for `.svm` files within the archive
- If the archive contains multiple setups → selection dialog or batch installation

### Batch installation
- Drag multiple files onto the window at once
- Select multiple files from the "Browse" dialog
- Auto-detection of car/track for each file; falls back to the current selection

### Setup preview
- Displays key parameters: tire pressures, wings, fuel, brakes, anti-roll bars, final drive ratio, toe, camber

### History
- Last 20 installations stored
- Double-click an entry → opens the destination folder
- Option to clear the entire history

### Rollback
- Restore a `.svm.bak` backup with one click
- If multiple backups exist in the folder → selection dialog

### Keyboard shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Browse files |
| `Ctrl+I` | Install setup |
| `Ctrl+R` | Rollback |

### Drag & Drop
- Drag `.svm` files or archives directly onto the window
- Multiple file drag support

### Other
- **Persistent configuration** (LMU folder saved between sessions)
- **GUI** with Le Mans Ultimate color palette (deep navy, gold, racing red)
- **Custom icon** with checkered flag

---

## Download

Download `LMU Setup Installer.exe` from the `dist\` folder. No installation required — just run it.

---

## Quick start

1. **Launch** `LMU Setup Installer.exe`
2. The LMU folder is detected automatically (or use "Browse...")
3. **Drag** an `.svm` file or archive onto the window (or use `Ctrl+O`)
4. The app detects car and track — verify or change manually
5. Click **Install** (or `Ctrl+I`)
6. You can open the destination folder or rollback at any time

---

## Building from source

### Requirements
- **Python 3.10+** — [python.org](https://www.python.org/downloads/) (select "Add Python to PATH")
- Libraries: `pip install pyinstaller pillow tkinterdnd2 py7zr rarfile`

### Build

```batch
build_exe.bat
```

or manually:

```batch
pip install pyinstaller pillow tkinterdnd2 py7zr rarfile
python -c "from lmu_setup_installer import export_icon; from pathlib import Path; export_icon(Path('lmu_icon.ico'))"
python -m PyInstaller --onefile --windowed --name "LMU Setup Installer" --icon lmu_icon.ico --collect-all tkinterdnd2 --collect-all py7zr --hidden-import rarfile lmu_setup_installer.py
```

The `.exe` will be in `dist\LMU Setup Installer.exe` (~22 MB).

### Run without compiling

```batch
python lmu_setup_installer.py
```

---

## Expected LMU folder structure

```
Documents\
  Le Mans Ultimate\
    UserData\
      player\
        Settings\
          Ferrari 499P\            ← one folder per car
            Le Mans\               ← track subfolder (optional)
            Monza\
          Toyota GR010\
          Peugeot 9X8\
          ...
```

---

## Notes

- If the LMU folder is not found automatically, use **Browse...** to select it manually.
- Automatic detection works if the `.svm` file contains `GameVehicleClass`, `Vehicle`, `TrackName`, `Circuit` or `RaceConfigPath` fields.
- The **Track** field is optional: if left empty, the setup is copied to the car's root folder.
- Backups (`.svm.bak`) are created in the same folder as the destination file.
