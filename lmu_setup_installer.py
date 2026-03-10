"""
LMU Setup Installer v6
Installa i file setup (.svm) di Le Mans Ultimate.
Supporta: archivi compressi, installazione batch, anteprima parametri,
cronologia installazioni, rollback backup, scorciatoie tastiera.
"""

import shutil
import re
import json
import subprocess
import tempfile
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

# Librerie opzionali per archivi
try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False

try:
    import rarfile
    HAS_RAR = True
except ImportError:
    HAS_RAR = False

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------------------------------------------------------------------------
# Palette — Le Mans Ultimate
# ---------------------------------------------------------------------------
C = {
    "bg":       "#080c18",
    "surface":  "#0f1628",
    "surface2": "#172038",
    "border":   "#1e2d50",
    "accent":   "#d4a843",
    "accent2":  "#edc35a",
    "red":      "#c0392b",
    "red2":     "#e74c3c",
    "fg":       "#ffffff",
    "fg2":      "#b0bec5",
    "fg3":      "#7890a0",
    "success":  "#2ecc71",
    "danger":   "#e74c3c",
    "drop_bg":  "#0b1020",
    "drop_brd": "#1a3060",
    "statusbg": "#060a14",
}

FONT       = "Segoe UI"
COMPRESSED = {".zip", ".7z", ".rar"}
MAX_HISTORY = 20


# ---------------------------------------------------------------------------
# Icona + Banner
# ---------------------------------------------------------------------------

def _build_icon_image(size: int = 64):
    if not HAS_PIL:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    GOLD, WHT, DARK = (212, 168, 67), (255, 255, 255), (15, 22, 40)
    d.ellipse([1, 1, size - 2, size - 2], fill=DARK, outline=GOLD, width=2)
    m = size // 4
    sq = (size - 2 * m) // 4
    for r in range(4):
        for c in range(4):
            d.rectangle([m + c * sq, m + r * sq, m + c * sq + sq - 1, m + r * sq + sq - 1],
                        fill=GOLD if (r + c) % 2 == 0 else WHT)
    return img


def export_icon(dest: Path) -> bool:
    img = _build_icon_image(64)
    if not img:
        return False
    try:
        img.save(str(dest), format="ICO", sizes=[(64, 64), (32, 32), (16, 16)])
        return True
    except Exception:
        return False


def _build_banner(w: int, h: int):
    if not HAS_PIL:
        return None
    img = Image.new("RGBA", (w, h), (8, 12, 24, 255))
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / w
        r = int(8 + 15 * t)
        g = int(12 + 10 * t)
        b = int(24 + 30 * t)
        d.line([(x, 0), (x, h)], fill=(r, g, b, 255))
    sq = 20
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    sx = w - sq * 10
    for ri in range(h // sq + 1):
        for ci in range(10):
            if (ri + ci) % 2 == 0:
                od.rectangle([sx + ci * sq, ri * sq, sx + ci * sq + sq, ri * sq + sq],
                             fill=(212, 168, 67, 14))
    img = Image.alpha_composite(img, ov)
    d2 = ImageDraw.Draw(img)
    d2.rectangle([0, h - 3, w, h], fill=(192, 57, 43, 255))
    return img


# ---------------------------------------------------------------------------
# Config persistente
# ---------------------------------------------------------------------------

CONFIG_FILE = Path.home() / ".lmu_setup_installer.json"


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data: dict):
    try:
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Logica LMU
# ---------------------------------------------------------------------------

LMU_FOLDER_NAMES = ["Le Mans Ultimate", "LeMansUltimate", "LMU"]


def find_lmu_settings_dir() -> Path | None:
    docs = Path.home() / "Documents"
    for name in LMU_FOLDER_NAMES:
        c = docs / name / "UserData" / "player" / "Settings"
        if c.is_dir():
            return c
    for item in docs.iterdir():
        if item.is_dir():
            c = item / "UserData" / "player" / "Settings"
            if c.is_dir():
                return c
    return None


def get_car_folders(d: Path) -> list[str]:
    if not d or not d.is_dir():
        return []
    return sorted([x.name for x in d.iterdir() if x.is_dir()], key=str.lower)


def get_track_folders(d: Path, car: str) -> list[str]:
    if not d or not car:
        return []
    cd = d / car
    return sorted([x.name for x in cd.iterdir() if x.is_dir()], key=str.lower) if cd.is_dir() else []


def guess_car_from_svm(p: Path) -> str | None:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
        for pat in [r'GameVehicleClass="([^"]+)"', r"GameVehicleClass=([^\r\n]+)",
                    r'Vehicle="([^"]+)"', r"Vehicle=([^\r\n]+)"]:
            m = re.search(pat, t, re.IGNORECASE)
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return None


def guess_track_from_svm(p: Path) -> str | None:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
        for pat in [r'TrackName="([^"]+)"', r"TrackName=([^\r\n]+)",
                    r'Circuit="([^"]+)"', r"Circuit=([^\r\n]+)",
                    r'RaceConfigPath="([^"]+)"', r"RaceConfigPath=([^\r\n]+)"]:
            m = re.search(pat, t, re.IGNORECASE)
            if m:
                v = m.group(1).strip()
                if "/" in v or "\\" in v:
                    v = re.split(r"[/\\]", v)[-1]
                return v
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Anteprima SVM — parsing parametri chiave
# ---------------------------------------------------------------------------

_PREVIEW_PATTERNS = [
    ("Pressione ant.", r'FrontTirePressure[^=]*=\s*([0-9.]+)', "kPa"),
    ("Pressione post.", r'RearTirePressure[^=]*=\s*([0-9.]+)', "kPa"),
    ("Ala anteriore", r'FrontWing[^=]*=\s*([0-9.]+)', ""),
    ("Ala posteriore", r'RearWing[^=]*=\s*([0-9.]+)', ""),
    ("Carburante", r'Fuel[^=]*=\s*([0-9.]+)', "L"),
    ("Bilanciamento freni", r'BrakePressure[^=]*=\s*([0-9.]+)', "%"),
    ("Barra ant.", r'FrontAntiSway[^=]*=\s*([0-9.]+)', ""),
    ("Barra post.", r'RearAntiSway[^=]*=\s*([0-9.]+)', ""),
    ("Rapporto finale", r'FinalDrive[^=]*=\s*([0-9.]+)', ""),
    ("Toe anteriore", r'FrontToe[^=]*=\s*([0-9.\-]+)', "°"),
    ("Toe posteriore", r'RearToe[^=]*=\s*([0-9.\-]+)', "°"),
    ("Camber ant.", r'FrontCamber[^=]*=\s*([0-9.\-]+)', "°"),
    ("Camber post.", r'RearCamber[^=]*=\s*([0-9.\-]+)', "°"),
]


def parse_svm_preview(p: Path) -> list[tuple[str, str]]:
    """Restituisce una lista di (etichetta, valore) per i parametri chiave."""
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    result = []
    for label, pattern, unit in _PREVIEW_PATTERNS:
        m = re.search(pattern, t, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            result.append((label, f"{val} {unit}".strip()))
    return result


# ---------------------------------------------------------------------------
# Estrazione archivi compressi
# ---------------------------------------------------------------------------

def extract_svm_from_archive(archive_path: Path) -> list[Path]:
    suffix = archive_path.suffix.lower()
    tmp = Path(tempfile.mkdtemp(prefix="lmu_setup_"))
    try:
        if suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(tmp)
        elif suffix == ".7z" and HAS_7Z:
            with py7zr.SevenZipFile(archive_path, "r") as sz:
                sz.extractall(tmp)
        elif suffix == ".rar" and HAS_RAR:
            with rarfile.RarFile(archive_path, "r") as rf:
                rf.extractall(tmp)
        else:
            return []
    except Exception:
        return []
    return list(tmp.rglob("*.svm"))


# ---------------------------------------------------------------------------
# Widget custom
# ---------------------------------------------------------------------------

class HoverButton(tk.Button):
    def __init__(self, parent, text="", command=None,
                 bg_color=C["accent"], fg_color=C["bg"],
                 hover_color=C["accent2"], disabled_color="#2a2a3a",
                 font_spec=(FONT, 11, "bold"), **kw):
        self._bg = bg_color
        self._fg = fg_color
        self._hover = hover_color
        self._dis = disabled_color
        self._enabled = True
        super().__init__(parent, text=text, command=command,
                         bg=bg_color, fg=fg_color, activebackground=hover_color,
                         activeforeground=fg_color, font=font_spec, relief="flat",
                         bd=0, highlightthickness=0, cursor="hand2",
                         padx=16, pady=8, **kw)
        self.bind("<Enter>", lambda e: self._on_enter())
        self.bind("<Leave>", lambda e: self._on_leave())

    def _on_enter(self):
        if self._enabled:
            self.configure(bg=self._hover)

    def _on_leave(self):
        self.configure(bg=self._bg if self._enabled else self._dis)

    def set_enabled(self, on: bool):
        self._enabled = on
        self.configure(state="normal" if on else "disabled",
                       bg=self._bg if on else self._dis,
                       fg=self._fg if on else "#555",
                       cursor="hand2" if on else "")


class SectionLabel(tk.Frame):
    def __init__(self, parent, text, icon=""):
        super().__init__(parent, bg=C["bg"])
        self.columnconfigure(2, weight=1)
        tk.Frame(self, bg=C["border"], height=1, width=20).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(self, text=f"{icon}  {text}" if icon else text,
                 bg=C["bg"], fg=C["accent"], font=(FONT, 10, "bold")).grid(row=0, column=1)
        tk.Frame(self, bg=C["border"], height=1).grid(row=0, column=2, sticky="ew", padx=(8, 0))


# ---------------------------------------------------------------------------
# ScrollableFrame helper
# ---------------------------------------------------------------------------

class ScrollableFrame(tk.Frame):
    """Contenitore scrollabile verticalmente."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg"], **kw)
        self._canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        self._vscroll = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.inner = tk.Frame(self._canvas, bg=C["bg"])
        self.inner.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._win = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._vscroll.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._vscroll.pack(side="right", fill="y")
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        # Mousewheel
        self.inner.bind("<Enter>", lambda e: self._bind_wheel())
        self.inner.bind("<Leave>", lambda e: self._unbind_wheel())

    def _on_canvas_resize(self, e):
        self._canvas.itemconfigure(self._win, width=e.width)

    def _bind_wheel(self):
        self._canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _unbind_wheel(self):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, e):
        self._canvas.yview_scroll(-1 * (e.delta // 120), "units")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class App(tk.Tk):
    WW = 700

    def __init__(self):
        super().__init__()
        self.title("LMU Setup Installer")
        self.resizable(False, True)
        self.configure(bg=C["bg"])
        self._config = load_config()
        self._last_dest_dir: Path | None = None
        self._temp_dirs: list[Path] = []
        self._pending_files: list[Path] = []  # batch mode
        self._build_ui()
        self._apply_icon()
        self._enable_drop()
        self._bind_shortcuts()
        self._auto_detect_settings()
        self._refresh_history_list()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        h = min(self.winfo_height(), sh - 80)
        self.geometry(f"{self.WW}x{h}+{(sw - self.WW) // 2}+{max((sh - h) // 2 - 20, 0)}")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _bind_shortcuts(self):
        self.bind_all("<Control-o>", lambda e: self._browse_setup())
        self.bind_all("<Control-O>", lambda e: self._browse_setup())
        self.bind_all("<Control-i>", lambda e: self._install())
        self.bind_all("<Control-I>", lambda e: self._install())
        self.bind_all("<Control-r>", lambda e: self._rollback())
        self.bind_all("<Control-R>", lambda e: self._rollback())

    def _on_close(self):
        for td in self._temp_dirs:
            try:
                shutil.rmtree(td, ignore_errors=True)
            except Exception:
                pass
        self.destroy()

    def _apply_icon(self):
        img = _build_icon_image(64)
        if img:
            try:
                self._icon_ref = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon_ref)
            except Exception:
                pass

    def _enable_drop(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self._drop_hint.set("Trascina qui file .svm o archivi (.zip .7z .rar)")
        except Exception:
            pass

    def _on_drop(self, event):
        raw = event.data.strip()
        # Parsing multiplo — tkinterdnd2 su Windows usa {} per path con spazi
        paths = []
        if "{" in raw:
            for part in re.findall(r"\{([^}]+)\}", raw):
                p = Path(part)
                if p.is_file():
                    paths.append(p)
        else:
            for part in raw.split():
                p = Path(part)
                if p.is_file():
                    paths.append(p)
        if not paths:
            self._set_status("Nessun file valido trascinato", "warn")
            return
        if len(paths) == 1:
            self._handle_file(paths[0])
        else:
            self._handle_batch(paths)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        W = self.WW
        BG = C["bg"]

        # ═══ HEADER ═══
        hh = 88
        hc = tk.Canvas(self, width=W, height=hh, bg=BG, highlightthickness=0)
        hc.pack(fill="x")
        banner = _build_banner(W, hh)
        if banner:
            self._banner_ph = ImageTk.PhotoImage(banner)
            hc.create_image(0, 0, anchor="nw", image=self._banner_ph)
        hc.create_text(28, 18, anchor="nw", text="LMU Setup Installer",
                       fill="#ffffff", font=(FONT, 22, "bold"))
        hc.create_text(28, 54, anchor="nw",
                       text="Installa i setup di Le Mans Ultimate nella cartella corretta",
                       fill=C["fg2"], font=(FONT, 10))

        # ═══ SCROLLABLE BODY ═══
        sf = ScrollableFrame(self)
        sf.pack(fill="both", expand=True)
        outer = tk.Frame(sf.inner, bg=BG, padx=22, pady=14)
        outer.pack(fill="x", expand=True)

        # ── Cartella LMU ──
        SectionLabel(outer, "Cartella LMU", "📁").pack(fill="x", pady=(0, 6))
        c1 = self._card(outer)
        r0 = tk.Frame(c1, bg=C["surface"])
        r0.pack(fill="x", pady=3)
        self._flbl(r0, "Percorso:")
        self._settings_var = tk.StringVar()
        self._fentry(r0, self._settings_var)
        HoverButton(r0, "Sfoglia…", self._browse_settings,
                    font_spec=(FONT, 10, "bold")).pack(side="right")

        # ── File Setup ──
        SectionLabel(outer, "File Setup", "📄").pack(fill="x", pady=(16, 6))

        self._drop_hint = tk.StringVar(value="Seleziona file .svm o archivi (.zip .7z .rar)")
        self._drop_zone = tk.Frame(outer, bg=C["drop_bg"],
                                   highlightthickness=2, highlightbackground=C["drop_brd"])
        self._drop_zone.pack(fill="x", ipady=14, pady=(0, 8))
        tk.Label(self._drop_zone, textvariable=self._drop_hint,
                 bg=C["drop_bg"], fg=C["fg3"],
                 font=(FONT, 10, "italic")).pack(pady=6)

        c2 = self._card(outer)
        r1 = tk.Frame(c2, bg=C["surface"])
        r1.pack(fill="x", pady=3)
        self._flbl(r1, "File:")
        self._setup_var = tk.StringVar()
        self._fentry(r1, self._setup_var)
        HoverButton(r1, "Sfoglia…", self._browse_setup,
                    font_spec=(FONT, 10, "bold")).pack(side="right")

        # Batch indicator
        self._batch_frame = tk.Frame(c2, bg=C["surface"])
        self._batch_var = tk.StringVar()
        tk.Label(self._batch_frame, textvariable=self._batch_var,
                 bg=C["surface"], fg=C["accent"], font=(FONT, 10, "bold")).pack(side="left", padx=6)
        HoverButton(self._batch_frame, "✕ Annulla batch", self._clear_batch,
                    bg_color="#1a2540", fg_color=C["fg2"],
                    hover_color="#243050", font_spec=(FONT, 9, "bold")).pack(side="right")

        # ── Anteprima Setup ──
        self._preview_section = tk.Frame(outer, bg=BG)
        SectionLabel(self._preview_section, "Anteprima Setup", "🔍").pack(fill="x", pady=(0, 6))
        self._preview_card = self._card(self._preview_section)
        self._preview_grid = tk.Frame(self._preview_card, bg=C["surface"])
        self._preview_grid.pack(fill="x")
        # Preview will be populated dynamically

        # ── Auto & Tracciato ──
        SectionLabel(outer, "Auto & Tracciato", "🏎").pack(fill="x", pady=(16, 6))
        c3 = self._card(outer)

        ra = tk.Frame(c3, bg=C["surface"]); ra.pack(fill="x", pady=3)
        self._flbl(ra, "Rilevata:")
        self._detected_car_var = tk.StringVar(value="—")
        tk.Label(ra, textvariable=self._detected_car_var, bg=C["surface"],
                 fg=C["accent"], font=(FONT, 11, "bold")).pack(side="left", padx=6)

        rb = tk.Frame(c3, bg=C["surface"]); rb.pack(fill="x", pady=4)
        self._flbl(rb, "Auto:")
        self._car_var = tk.StringVar()
        self._car_combo = ttk.Combobox(rb, textvariable=self._car_var,
                                       state="readonly", font=(FONT, 10))
        self._car_combo.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._car_combo.bind("<<ComboboxSelected>>", self._on_car_changed)

        tk.Frame(c3, bg=C["border"], height=1).pack(fill="x", pady=10, padx=8)

        rc = tk.Frame(c3, bg=C["surface"]); rc.pack(fill="x", pady=3)
        self._flbl(rc, "Rilevato:")
        self._detected_track_var = tk.StringVar(value="—")
        tk.Label(rc, textvariable=self._detected_track_var, bg=C["surface"],
                 fg=C["accent"], font=(FONT, 11, "bold")).pack(side="left", padx=6)

        rd = tk.Frame(c3, bg=C["surface"]); rd.pack(fill="x", pady=4)
        self._flbl(rd, "Tracciato:")
        self._track_var = tk.StringVar()
        self._track_combo = ttk.Combobox(rd, textvariable=self._track_var, font=(FONT, 10))
        self._track_combo.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tk.Label(c3, text="Vuoto = cartella radice dell'auto  ·  Puoi digitare un nuovo nome tracciato",
                 bg=C["surface"], fg=C["fg3"], font=(FONT, 9)).pack(anchor="w", padx=6, pady=(2, 2))

        # ── Opzioni ──
        SectionLabel(outer, "Opzioni", "⚙").pack(fill="x", pady=(16, 6))
        c4 = self._card(outer)
        self._overwrite_var = tk.BooleanVar(value=True)
        self._backup_var = tk.BooleanVar(value=True)
        for var, txt in [(self._overwrite_var, "Sovrascrivi se il file esiste già"),
                         (self._backup_var, "Backup automatico del vecchio setup (.svm.bak)")]:
            tk.Checkbutton(c4, text=txt, variable=var, bg=C["surface"],
                           fg=C["fg"], activebackground=C["surface"],
                           activeforeground=C["fg"], selectcolor=C["surface2"],
                           font=(FONT, 10), anchor="w",
                           highlightthickness=0, bd=0).pack(fill="x", padx=6, pady=3)

        # ── Pulsanti ──
        bf = tk.Frame(outer, bg=BG)
        bf.pack(fill="x", pady=(18, 6))

        self._install_btn = HoverButton(
            bf, "⬇  Installa  (Ctrl+I)", self._install,
            bg_color=C["red"], fg_color="#ffffff",
            hover_color=C["red2"], font_spec=(FONT, 12, "bold"))
        self._install_btn.pack(side="left", padx=(0, 10))

        self._open_btn = HoverButton(
            bf, "📂  Apri cartella", self._open_dest_folder,
            bg_color="#1a2540", fg_color=C["fg2"],
            hover_color="#243050", font_spec=(FONT, 10, "bold"))
        self._open_btn.set_enabled(False)
        self._open_btn.pack(side="left", padx=(0, 10))

        self._rollback_btn = HoverButton(
            bf, "↩  Rollback  (Ctrl+R)", self._rollback,
            bg_color="#1a2540", fg_color=C["fg2"],
            hover_color="#243050", font_spec=(FONT, 10, "bold"))
        self._rollback_btn.set_enabled(False)
        self._rollback_btn.pack(side="left")

        # ── Cronologia ──
        SectionLabel(outer, "Cronologia installazioni", "📋").pack(fill="x", pady=(18, 6))
        c5 = self._card(outer)
        hist_top = tk.Frame(c5, bg=C["surface"])
        hist_top.pack(fill="x", pady=(0, 6))
        tk.Label(hist_top, text="Ultime installazioni (doppio click → apri cartella)",
                 bg=C["surface"], fg=C["fg3"], font=(FONT, 9)).pack(side="left")
        HoverButton(hist_top, "🗑 Svuota", self._clear_history,
                    bg_color="#1a2540", fg_color=C["fg3"],
                    hover_color="#243050", font_spec=(FONT, 9, "bold")).pack(side="right")

        self._hist_listbox = tk.Listbox(
            c5, bg=C["surface2"], fg=C["fg"], font=(FONT, 9),
            selectbackground=C["accent"], selectforeground=C["bg"],
            relief="flat", highlightthickness=1,
            highlightcolor=C["accent"], highlightbackground=C["border"],
            height=5, activestyle="none")
        self._hist_listbox.pack(fill="x")
        self._hist_listbox.bind("<Double-1>", self._on_history_dblclick)

        # Shortcut hint
        hint = tk.Frame(outer, bg=BG)
        hint.pack(fill="x", pady=(12, 4))
        tk.Label(hint, text="Ctrl+O  Sfoglia   ·   Ctrl+I  Installa   ·   Ctrl+R  Rollback",
                 bg=BG, fg=C["fg3"], font=(FONT, 9)).pack()

        # ── Status bar ──
        sb = tk.Frame(self, bg=C["statusbg"], padx=14, pady=7)
        sb.pack(fill="x", side="bottom")
        self._status_dot = tk.Canvas(sb, width=10, height=10,
                                     bg=C["statusbg"], highlightthickness=0)
        self._status_dot.pack(side="left", padx=(0, 8))
        self._status_dot.create_oval(1, 1, 9, 9, fill=C["fg3"], outline="")
        self._status_var = tk.StringVar(value="Pronto")
        tk.Label(sb, textvariable=self._status_var, bg=C["statusbg"],
                 fg=C["fg2"], font=(FONT, 9), anchor="w").pack(side="left", fill="x")

        formats = ".zip"
        if HAS_7Z:
            formats += "  .7z"
        if HAS_RAR:
            formats += "  .rar"
        tk.Label(sb, text=f"v6.0  ·  Archivi: {formats}",
                 bg=C["statusbg"], fg="#3a4a5a", font=(FONT, 8)).pack(side="right")

        # Stile combobox
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TCombobox", fieldbackground=C["surface2"], foreground=C["fg"],
                    selectbackground=C["accent"], selectforeground=C["bg"],
                    arrowcolor=C["accent"], font=(FONT, 10))
        s.map("TCombobox", fieldbackground=[("readonly", C["surface2"])])
        s.configure("Vertical.TScrollbar", background=C["surface2"],
                    troughcolor=C["bg"], arrowcolor=C["accent"])

    # --- UI helpers ---

    def _card(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=C["surface"], highlightbackground=C["border"],
                     highlightthickness=1, padx=14, pady=10)
        f.pack(fill="x", pady=(0, 3))
        return f

    def _flbl(self, parent, text):
        tk.Label(parent, text=text, bg=C["surface"], fg=C["fg2"],
                 font=(FONT, 10), width=10, anchor="w").pack(side="left")

    def _fentry(self, parent, var):
        tk.Entry(parent, textvariable=var, bg=C["surface2"], fg=C["fg"],
                 insertbackground=C["fg"], relief="flat", font=(FONT, 10),
                 highlightthickness=1, highlightcolor=C["accent"],
                 highlightbackground=C["border"]).pack(
            side="left", fill="x", expand=True, ipady=5, padx=(6, 8))

    def _flash_drop_zone(self, color):
        self._drop_zone.configure(highlightbackground=color)
        self.after(1200, lambda: self._drop_zone.configure(highlightbackground=C["drop_brd"]))

    # ------------------------------------------------------------------
    # Anteprima Setup
    # ------------------------------------------------------------------

    def _show_preview(self, svm_path: Path):
        """Mostra i parametri chiave del file .svm."""
        params = parse_svm_preview(svm_path)
        # Pulisci griglia precedente
        for w in self._preview_grid.winfo_children():
            w.destroy()
        if not params:
            tk.Label(self._preview_grid, text="Nessun parametro rilevato nel file",
                     bg=C["surface"], fg=C["fg3"], font=(FONT, 9, "italic")).grid(
                row=0, column=0, sticky="w", padx=4)
            self._preview_section.pack(fill="x", pady=(16, 0))
            return
        # Two-column grid
        cols = 2
        for i, (label, value) in enumerate(params):
            row, col = divmod(i, cols)
            base_col = col * 2
            tk.Label(self._preview_grid, text=label + ":",
                     bg=C["surface"], fg=C["fg2"], font=(FONT, 9),
                     anchor="w", width=16).grid(row=row, column=base_col, sticky="w", padx=(4, 2), pady=1)
            tk.Label(self._preview_grid, text=value,
                     bg=C["surface"], fg=C["accent"], font=(FONT, 9, "bold"),
                     anchor="w").grid(row=row, column=base_col + 1, sticky="w", padx=(0, 16), pady=1)
        self._preview_section.pack(fill="x", pady=(16, 0))

    def _hide_preview(self):
        self._preview_section.pack_forget()

    # ------------------------------------------------------------------
    # File handling (svm + archivi + batch)
    # ------------------------------------------------------------------

    def _handle_file(self, p: Path):
        """Gestisce un singolo file (.svm o archivio compresso)."""
        ext = p.suffix.lower()
        if ext == ".svm":
            self._clear_batch()
            self._setup_var.set(str(p))
            self._process_svm_file(p)
            self._show_preview(p)
            self._flash_drop_zone(C["success"])
            return

        if ext in COMPRESSED:
            self._set_status(f"Estrazione di {p.name} in corso…", "info")
            self.update_idletasks()
            svms = extract_svm_from_archive(p)
            if not svms:
                messagebox.showwarning("Nessun setup trovato",
                                       f"L'archivio {p.name} non contiene file .svm.")
                self._set_status("Nessun .svm trovato nell'archivio", "warn")
                return
            self._temp_dirs.append(svms[0].parent if len(svms) == 1 else svms[0].parents[1])

            if len(svms) == 1:
                self._clear_batch()
                self._setup_var.set(str(svms[0]))
                self._process_svm_file(svms[0])
                self._show_preview(svms[0])
                self._flash_drop_zone(C["success"])
                self._set_status(f"Estratto: {svms[0].name} da {p.name}", "ok")
            else:
                # Multiple .svm in archive → batch mode
                self._start_batch(svms, p.name)
            return

        self._set_status("Formato non supportato. Usa .svm, .zip, .7z o .rar", "warn")

    def _handle_batch(self, files: list[Path]):
        """Gestisce multipli file trascinati/selezionati."""
        all_svms: list[Path] = []
        for f in files:
            ext = f.suffix.lower()
            if ext == ".svm":
                all_svms.append(f)
            elif ext in COMPRESSED:
                self._set_status(f"Estrazione di {f.name}…", "info")
                self.update_idletasks()
                svms = extract_svm_from_archive(f)
                if svms:
                    self._temp_dirs.append(svms[0].parent if len(svms) == 1 else svms[0].parents[1])
                    all_svms.extend(svms)
        if not all_svms:
            self._set_status("Nessun file .svm trovato", "warn")
            return
        if len(all_svms) == 1:
            self._clear_batch()
            self._setup_var.set(str(all_svms[0]))
            self._process_svm_file(all_svms[0])
            self._show_preview(all_svms[0])
            self._flash_drop_zone(C["success"])
        else:
            self._start_batch(all_svms)

    def _start_batch(self, svms: list[Path], source_name: str = ""):
        """Attiva la modalità batch."""
        self._pending_files = list(svms)
        n = len(svms)
        src = f" da {source_name}" if source_name else ""
        self._batch_var.set(f"📦 Batch: {n} file setup pronti per l'installazione{src}")
        self._batch_frame.pack(fill="x", pady=(6, 0))
        self._setup_var.set(f"[Batch: {n} file]")
        # Mostra anteprima del primo per aiutare la selezione auto/tracciato
        self._process_svm_file(svms[0])
        self._show_preview(svms[0])
        self._flash_drop_zone(C["accent"])
        self._set_status(f"Batch: {n} file .svm pronti — scegli auto/tracciato e clicca Installa", "ok")

    def _clear_batch(self):
        self._pending_files = []
        self._batch_frame.pack_forget()

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _auto_detect_settings(self):
        saved = self._config.get("settings_dir", "")
        if saved and Path(saved).is_dir():
            self._settings_var.set(saved)
            self._refresh_car_list()
            self._set_status("Cartella LMU caricata dalla configurazione", "ok")
            return
        path = find_lmu_settings_dir()
        if path:
            self._settings_var.set(str(path))
            self._refresh_car_list()
            self._set_status("Cartella LMU trovata automaticamente", "ok")
        else:
            self._set_status("Cartella LMU non trovata — selezionala manualmente", "warn")

    def _browse_settings(self):
        path = filedialog.askdirectory(title="Seleziona cartella Settings di LMU")
        if path:
            self._settings_var.set(path)
            self._refresh_car_list()
            self._config["settings_dir"] = path
            save_config(self._config)

    def _browse_setup(self):
        ftypes = [("Setup e archivi", "*.svm *.zip *.7z *.rar"),
                  ("LMU Setup", "*.svm"),
                  ("Archivi compressi", "*.zip *.7z *.rar"),
                  ("Tutti i file", "*.*")]
        paths = filedialog.askopenfilenames(title="Seleziona file setup o archivio (anche multipli)",
                                            filetypes=ftypes)
        if not paths:
            return
        file_list = [Path(p) for p in paths]
        if len(file_list) == 1:
            self._handle_file(file_list[0])
        else:
            self._handle_batch(file_list)

    def _process_svm_file(self, svm: Path):
        car = guess_car_from_svm(svm)
        if car:
            self._detected_car_var.set(car)
            cars = list(self._car_combo["values"])
            match = next(
                (c for c in cars if car.lower() in c.lower() or c.lower() in car.lower()), None)
            if match:
                self._car_var.set(match)
                self._refresh_track_list()
        else:
            self._detected_car_var.set("Non rilevata — scegli manualmente")

        track = guess_track_from_svm(svm)
        if track:
            self._detected_track_var.set(track)
            tracks = list(self._track_combo["values"])
            match = next(
                (t for t in tracks if track.lower() in t.lower() or t.lower() in track.lower()), None)
            self._track_var.set(match if match else track)
        else:
            self._detected_track_var.set("Non rilevato — scegli manualmente")
        self._set_status(f"Setup caricato: {svm.name}", "ok")

    def _on_car_changed(self, _e=None):
        self._refresh_track_list()

    def _refresh_car_list(self):
        sp = self._settings_var.get().strip()
        if not sp:
            return
        cars = get_car_folders(Path(sp))
        self._car_combo["values"] = cars
        if cars:
            self._car_combo.current(0)
        self._refresh_track_list()

    def _refresh_track_list(self):
        sp = self._settings_var.get().strip()
        car = self._car_var.get().strip()
        if not sp or not car:
            self._track_combo["values"] = []
            return
        self._track_combo["values"] = get_track_folders(Path(sp), car)

    # ------------------------------------------------------------------
    # Installazione (singola + batch)
    # ------------------------------------------------------------------

    def _install(self):
        if self._pending_files:
            self._install_batch()
        else:
            self._install_single()

    def _install_single(self):
        ss = self._settings_var.get().strip()
        su = self._setup_var.get().strip()
        car = self._car_var.get().strip()
        trk = self._track_var.get().strip()

        if not ss:
            messagebox.showwarning("Attenzione", "Specifica la cartella Settings di LMU.")
            return
        if not su:
            messagebox.showwarning("Attenzione", "Seleziona un file setup (.svm).")
            return
        if not car:
            messagebox.showwarning("Attenzione", "Seleziona l'auto di destinazione.")
            return

        sdir = Path(ss)
        sf = Path(su)
        if not sf.is_file():
            messagebox.showerror("Errore", f"File non trovato:\n{sf}")
            return

        dd = sdir / car
        if trk:
            dd = dd / trk
        dd.mkdir(parents=True, exist_ok=True)
        df = dd / sf.name

        if df.exists():
            if not self._overwrite_var.get():
                messagebox.showinfo("File esistente",
                                    f"Il file esiste già e la sovrascrittura è disabilitata:\n{df}")
                return
            if self._backup_var.get():
                try:
                    shutil.copy2(df, df.with_suffix(".svm.bak"))
                except Exception as exc:
                    messagebox.showwarning("Backup", f"Backup non riuscito:\n{exc}")

        try:
            shutil.copy2(sf, df)
            self._last_dest_dir = dd
            self._open_btn.set_enabled(True)
            self._rollback_btn.set_enabled(True)
            ti = f" / {trk}" if trk else ""
            self._set_status(f"Installato: {sf.name}  →  {car}{ti}", "success")
            self._config["settings_dir"] = ss
            save_config(self._config)
            self._add_history_entry(sf.name, car, trk, str(dd))
            trk_info = f"\nTracciato: {trk}" if trk else "\nTracciato: (radice auto)"
            messagebox.showinfo("Successo! 🏁",
                                f"Setup installato correttamente!\n\n"
                                f"Auto: {car}{trk_info}\nFile: {df}")
        except Exception as exc:
            messagebox.showerror("Errore", str(exc))
            self._set_status(f"Errore: {exc}", "error")

    def _install_batch(self):
        """Installa tutti i file in coda (batch mode)."""
        ss = self._settings_var.get().strip()
        car_fallback = self._car_var.get().strip()
        trk_fallback = self._track_var.get().strip()

        if not ss:
            messagebox.showwarning("Attenzione", "Specifica la cartella Settings di LMU.")
            return
        if not car_fallback:
            messagebox.showwarning("Attenzione", "Seleziona l'auto di destinazione (usata come fallback).")
            return

        sdir = Path(ss)
        ok_count = 0
        fail_count = 0
        results = []

        for sf in self._pending_files:
            if not sf.is_file():
                fail_count += 1
                results.append(f"❌ {sf.name} — file non trovato")
                continue

            # Auto-detect per ogni file
            car = None
            detected_car = guess_car_from_svm(sf)
            if detected_car:
                cars = list(self._car_combo["values"])
                car = next((c for c in cars if detected_car.lower() in c.lower()
                            or c.lower() in detected_car.lower()), None)
            if not car:
                car = car_fallback

            track = guess_track_from_svm(sf) or trk_fallback

            dd = sdir / car
            if track:
                dd = dd / track
            dd.mkdir(parents=True, exist_ok=True)
            df = dd / sf.name

            if df.exists() and self._backup_var.get():
                try:
                    shutil.copy2(df, df.with_suffix(".svm.bak"))
                except Exception:
                    pass

            if df.exists() and not self._overwrite_var.get():
                results.append(f"⏭ {sf.name} — già esistente, skippato")
                continue

            try:
                shutil.copy2(sf, df)
                ti = f"/{track}" if track else ""
                results.append(f"✅ {sf.name}  →  {car}{ti}")
                self._add_history_entry(sf.name, car, track, str(dd))
                self._last_dest_dir = dd
                ok_count += 1
            except Exception as exc:
                results.append(f"❌ {sf.name} — {exc}")
                fail_count += 1

        self._open_btn.set_enabled(True)
        self._rollback_btn.set_enabled(True)
        self._config["settings_dir"] = ss
        save_config(self._config)
        self._clear_batch()
        self._setup_var.set("")
        self._hide_preview()

        summary = "\n".join(results)
        self._set_status(f"Batch: {ok_count} installati, {fail_count} errori", "success" if not fail_count else "warn")
        messagebox.showinfo("Installazione batch completata 🏁",
                            f"Installati: {ok_count}\nErrori: {fail_count}\n\n{summary}")

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def _rollback(self):
        """Ripristina l'ultimo backup .svm.bak."""
        history = self._config.get("history", [])
        if not history:
            messagebox.showinfo("Rollback", "Nessuna installazione in cronologia.")
            return

        # Cerca .bak nella cartella dell'ultima installazione
        last = history[0]
        dest_dir = Path(last.get("dest", ""))
        fname = last.get("file", "")
        if not dest_dir.is_dir() or not fname:
            messagebox.showwarning("Rollback", "Cartella di destinazione non trovata.")
            return

        bak_file = dest_dir / (fname.replace(".svm", "") + ".svm.bak")
        if not bak_file.suffix == ".bak":
            bak_file = dest_dir / f"{fname}.bak"

        target = dest_dir / fname

        if not bak_file.is_file():
            # Cerca qualsiasi .bak nella cartella
            baks = list(dest_dir.glob("*.svm.bak"))
            if not baks:
                messagebox.showinfo("Rollback", f"Nessun file .bak trovato in:\n{dest_dir}")
                return
            # Mostra dialog per scegliere
            bak_file = self._ask_which_bak(baks, dest_dir)
            if not bak_file:
                return
            target = dest_dir / bak_file.name.replace(".bak", "")

        if not messagebox.askyesno("Conferma rollback",
                                   f"Ripristinare il backup?\n\n"
                                   f"Backup: {bak_file.name}\n"
                                   f"Destinazione: {target}\n\n"
                                   f"Il file attuale verrà sovrascritto."):
            return

        try:
            shutil.copy2(bak_file, target)
            self._set_status(f"Rollback completato: {target.name}", "success")
            messagebox.showinfo("Rollback completato ↩",
                                f"Setup ripristinato:\n{target}")
        except Exception as exc:
            messagebox.showerror("Errore rollback", str(exc))

    def _ask_which_bak(self, baks: list[Path], folder: Path) -> Path | None:
        dlg = tk.Toplevel(self)
        dlg.title("Scegli backup da ripristinare")
        dlg.configure(bg=C["bg"])
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text=f"Backup trovati in {folder.name}:",
                 bg=C["bg"], fg=C["fg"], font=(FONT, 11, "bold"),
                 padx=16, pady=12).pack(fill="x")

        chosen = [None]
        listbox = tk.Listbox(dlg, bg=C["surface2"], fg=C["fg"],
                             selectbackground=C["accent"], selectforeground=C["bg"],
                             font=(FONT, 10), relief="flat", highlightthickness=1,
                             highlightcolor=C["accent"], highlightbackground=C["border"],
                             height=min(len(baks), 8))
        listbox.pack(fill="x", padx=16, pady=8)
        for b in baks:
            listbox.insert(tk.END, b.name)
        listbox.selection_set(0)

        def on_ok():
            sel = listbox.curselection()
            if sel:
                chosen[0] = baks[sel[0]]
            dlg.destroy()

        HoverButton(dlg, "Ripristina", on_ok,
                    bg_color=C["accent"], fg_color=C["bg"],
                    font_spec=(FONT, 10, "bold")).pack(pady=(4, 16))
        dlg.wait_window()
        return chosen[0]

    # ------------------------------------------------------------------
    # Cronologia
    # ------------------------------------------------------------------

    def _add_history_entry(self, filename: str, car: str, track: str, dest: str):
        history = self._config.get("history", [])
        entry = {
            "file": filename,
            "car": car,
            "track": track or "(radice)",
            "dest": dest,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        history.insert(0, entry)
        self._config["history"] = history[:MAX_HISTORY]
        save_config(self._config)
        self._refresh_history_list()

    def _refresh_history_list(self):
        self._hist_listbox.delete(0, tk.END)
        history = self._config.get("history", [])
        for h in history:
            self._hist_listbox.insert(
                tk.END,
                f"{h['date']}  ·  {h['file']}  →  {h['car']} / {h['track']}"
            )

    def _on_history_dblclick(self, _e):
        sel = self._hist_listbox.curselection()
        if not sel:
            return
        history = self._config.get("history", [])
        if sel[0] >= len(history):
            return
        dest = history[sel[0]].get("dest", "")
        if dest and Path(dest).is_dir():
            try:
                subprocess.Popen(["explorer", dest])
            except Exception:
                pass
        else:
            self._set_status("Cartella non trovata", "warn")

    def _clear_history(self):
        if not messagebox.askyesno("Svuota cronologia",
                                   "Eliminare tutta la cronologia installazioni?"):
            return
        self._config["history"] = []
        save_config(self._config)
        self._refresh_history_list()
        self._set_status("Cronologia svuotata", "ok")

    # ------------------------------------------------------------------
    # Utilità
    # ------------------------------------------------------------------

    def _open_dest_folder(self):
        if self._last_dest_dir:
            try:
                subprocess.Popen(["explorer", str(self._last_dest_dir)])
            except Exception:
                pass

    def _set_status(self, msg: str, level: str = "info"):
        self._status_var.set(msg)
        colors = {"ok": C["success"], "success": C["success"],
                  "warn": C["accent"], "error": C["danger"], "info": C["fg3"]}
        self._status_dot.delete("all")
        self._status_dot.create_oval(1, 1, 9, 9, fill=colors.get(level, C["fg3"]), outline="")
        self.update_idletasks()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    App().mainloop()
