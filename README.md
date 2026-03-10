# LMU Setup Installer v6

Applicazione desktop per installare i file setup (`.svm`) di **Le Mans Ultimate** nella cartella corretta, in base all'auto e al tracciato selezionati.

Supporta **file compressi** (.zip, .7z, .rar), **installazione batch**, **anteprima parametri**, **cronologia** e **rollback**.

---

## Funzionalità

### Installazione setup
- **Rilevamento automatico** della cartella Settings di LMU
- **Rilevamento automatico** di auto e tracciato dal contenuto del file `.svm`
- **Selezione manuale** di auto e tracciato tramite menu a tendina
- **Sovrascrittura** e **backup automatico** (`.svm.bak`) configurabili

### File compressi
- Supporto archivi **.zip**, **.7z**, **.rar**
- Estrazione automatica e scansione ricorsiva dei file `.svm` nell'archivio
- Se l'archivio contiene più setup → dialog di selezione o installazione batch

### Installazione batch
- Trascinare più file contemporaneamente sulla finestra
- Selezionare più file dal dialog "Sfoglia"
- Auto-detection di auto/tracciato per ciascun file; fallback sulla selezione corrente

### Anteprima setup
- Visualizzazione parametri chiave: pressione gomme, ali, carburante, freni, barre, rapporto finale, toe, camber

### Cronologia
- Ultime 20 installazioni memorizzate
- Doppio click su una voce → apre la cartella di destinazione
- Possibilità di svuotare la cronologia

### Rollback
- Ripristino del backup `.svm.bak` con un click
- Se nella cartella ci sono più backup → dialog per scegliere quale ripristinare

### Scorciatoie tastiera
| Shortcut | Azione |
|----------|--------|
| `Ctrl+O` | Sfoglia file |
| `Ctrl+I` | Installa setup |
| `Ctrl+R` | Rollback |

### Drag & Drop
- Trascina file `.svm` o archivi direttamente sulla finestra
- Supporto trascinamento multiplo

### Altro
- **Configurazione persistente** (cartella LMU memorizzata tra le sessioni)
- **Interfaccia grafica** con palette Le Mans Ultimate (blu notte, oro, rosso racing)
- **Icona personalizzata** con bandiera a scacchi

---

## Download

Scarica `LMU Setup Installer.exe` dalla cartella `dist\`. Non richiede installazione — basta avviarlo.

---

## Utilizzo rapido

1. **Avvia** `LMU Setup Installer.exe`
2. La cartella LMU viene rilevata automaticamente (oppure usa "Sfoglia…")
3. **Trascina** un file `.svm` o un archivio sulla finestra (oppure usa `Ctrl+O`)
4. L'app rileva auto e tracciato — verifica o modifica manualmente
5. Clicca **Installa** (o `Ctrl+I`)
6. Puoi aprire la cartella di destinazione o fare rollback in qualsiasi momento

---

## Compilare da sorgente

### Requisiti
- **Python 3.10+** — [python.org](https://www.python.org/downloads/) (seleziona "Add Python to PATH")
- Librerie: `pip install pyinstaller pillow tkinterdnd2 py7zr rarfile`

### Build

```batch
build_exe.bat
```

oppure manualmente:

```batch
pip install pyinstaller pillow tkinterdnd2 py7zr rarfile
python -c "from lmu_setup_installer import export_icon; from pathlib import Path; export_icon(Path('lmu_icon.ico'))"
python -m PyInstaller --onefile --windowed --name "LMU Setup Installer" --icon lmu_icon.ico --collect-all tkinterdnd2 --collect-all py7zr --hidden-import rarfile lmu_setup_installer.py
```

Il file `.exe` sarà in `dist\LMU Setup Installer.exe` (~22 MB).

### Eseguire senza compilare

```batch
python lmu_setup_installer.py
```

---

## Struttura cartelle LMU attesa

```
Documenti\
  Le Mans Ultimate\
    UserData\
      player\
        Settings\
          Ferrari 499P\            ← cartella per ciascuna auto
            Le Mans\               ← sotto-cartella per tracciato (opzionale)
            Monza\
          Toyota GR010\
          Peugeot 9X8\
          ...
```

---

## Note

- Se la cartella LMU non viene trovata automaticamente, usa **Sfoglia…** per selezionarla manualmente.
- Il rilevamento automatico funziona se il file `.svm` contiene i campi `GameVehicleClass`, `Vehicle`, `TrackName`, `Circuit` o `RaceConfigPath`.
- Il campo **Tracciato** è opzionale: se lasciato vuoto, il setup viene copiato nella cartella radice dell'auto.
- I backup (`.svm.bak`) vengono creati nella stessa cartella del file di destinazione.
