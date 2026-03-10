"""Genera la guida utente PDF per LMU Setup Installer."""

from fpdf import FPDF
from pathlib import Path


class GuidaPDF(FPDF):
    NAVY = (8, 12, 24)
    GOLD = (212, 168, 67)
    WHITE = (255, 255, 255)
    GRAY = (180, 190, 200)
    RED = (192, 57, 43)
    DARK_SURFACE = (15, 22, 40)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 12, style="F")
        self.set_fill_color(*self.RED)
        self.rect(0, 12, 210, 1.5, style="F")
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.GRAY)
        self.set_xy(10, 4)
        self.cell(0, 5, "LMU Setup Installer v6 - Guida Utente", align="L")
        self.ln(12)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def title_page(self):
        self.add_page()
        # Background
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 297, style="F")
        # Gold stripe
        self.set_fill_color(*self.GOLD)
        self.rect(0, 100, 210, 3, style="F")
        self.rect(0, 180, 210, 3, style="F")
        # Red thin stripe
        self.set_fill_color(*self.RED)
        self.rect(0, 103, 210, 1, style="F")
        # Title
        self.set_font("Helvetica", "B", 36)
        self.set_text_color(*self.WHITE)
        self.set_xy(0, 115)
        self.cell(0, 20, "LMU Setup Installer", align="C")
        # Subtitle
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*self.GOLD)
        self.set_xy(0, 138)
        self.cell(0, 10, "Guida Utente", align="C")
        # Version
        self.set_font("Helvetica", "I", 11)
        self.set_text_color(*self.GRAY)
        self.set_xy(0, 155)
        self.cell(0, 10, "Versione 6.0", align="C")
        # Checkered flag visual
        sq = 8
        sx, sy = 75, 200
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 0:
                    self.set_fill_color(*self.GOLD)
                else:
                    self.set_fill_color(*self.WHITE)
                self.rect(sx + c * sq, sy + r * sq, sq, sq, style="F")

    def section_title(self, title):
        self.ln(6)
        self.set_fill_color(*self.GOLD)
        self.rect(10, self.get_y(), 3, 8, style="F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.NAVY)
        self.set_x(18)
        self.cell(0, 8, title)
        self.ln(12)

    def subsection(self, title):
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 60, 80)
        self.cell(0, 7, title)
        self.ln(8)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text, indent=15):
        x = self.get_x()
        self.set_x(indent)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.cell(4, 6, "-")
        self.multi_cell(0, 6, text)
        self.ln(1)

    def shortcut_row(self, keys, desc):
        self.set_font("Courier", "B", 10)
        self.set_text_color(*self.NAVY)
        self.cell(30, 7, keys)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.cell(0, 7, desc)
        self.ln(7)

    def info_box(self, text):
        self.ln(2)
        y = self.get_y()
        self.set_fill_color(230, 240, 250)
        self.set_draw_color(100, 140, 180)
        self.rect(15, y, 180, 14, style="DF")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(40, 70, 110)
        self.set_xy(20, y + 2)
        self.multi_cell(170, 5, text)
        self.ln(4)

    def step(self, num, text):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.GOLD)
        self.cell(10, 7, str(num) + ".")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, text)
        self.ln(2)


def generate_guide(output: Path):
    pdf = GuidaPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # === COPERTINA ===
    pdf.title_page()

    # === INTRODUZIONE ===
    pdf.add_page()
    pdf.section_title("1. Introduzione")
    pdf.body_text(
        "LMU Setup Installer e' un'applicazione desktop per Windows che semplifica "
        "l'installazione dei file di setup (.svm) di Le Mans Ultimate.\n\n"
        "Invece di copiare manualmente i file nelle sottocartelle corrette, "
        "basta trascinare il file (o un archivio compresso) sulla finestra dell'app: "
        "il programma rileva automaticamente l'auto e il tracciato e copia il setup "
        "nella posizione corretta."
    )

    pdf.subsection("Funzionalita' principali")
    pdf.bullet("Rilevamento automatico della cartella Settings di LMU")
    pdf.bullet("Rilevamento automatico di auto e tracciato dal file .svm")
    pdf.bullet("Supporto file compressi: .zip, .7z, .rar")
    pdf.bullet("Installazione batch (piu' setup contemporaneamente)")
    pdf.bullet("Anteprima parametri del setup (pressioni, ali, carburante...)")
    pdf.bullet("Cronologia delle ultime 20 installazioni")
    pdf.bullet("Rollback: ripristino del backup con un click")
    pdf.bullet("Scorciatoie tastiera: Ctrl+O, Ctrl+I, Ctrl+R")
    pdf.bullet("Drag & Drop (trascinamento file/archivi sulla finestra)")
    pdf.bullet("Backup automatico (.svm.bak) prima della sovrascrittura")

    # === INSTALLAZIONE ===
    pdf.section_title("2. Installazione")
    pdf.body_text(
        "LMU Setup Installer non richiede installazione. Basta scaricare il file "
        "\"LMU Setup Installer.exe\" dalla cartella dist\\ e avviarlo.\n\n"
        "Il file e' un eseguibile autonomo (~22 MB) che include tutte le dipendenze."
    )
    pdf.info_box(
        "Nota: Al primo avvio, Windows SmartScreen potrebbe mostrare un avviso. "
        "Clicca \"Ulteriori informazioni\" e poi \"Esegui comunque\"."
    )

    # === PRIMO AVVIO ===
    pdf.section_title("3. Primo avvio")
    pdf.body_text(
        "All'avvio, l'applicazione tenta di trovare automaticamente la cartella Settings "
        "di Le Mans Ultimate cercando in:"
    )
    pdf.bullet("Documenti\\Le Mans Ultimate\\UserData\\player\\Settings")
    pdf.bullet("Documenti\\LeMansUltimate\\UserData\\player\\Settings")
    pdf.bullet("Documenti\\LMU\\UserData\\player\\Settings")
    pdf.ln(2)
    pdf.body_text(
        "Se la cartella viene trovata, il campo \"Percorso\" viene compilato "
        "automaticamente e la lista delle auto disponibili viene popolata.\n\n"
        "Se non viene trovata, usa il pulsante \"Sfoglia...\" nella sezione "
        "\"Cartella LMU\" per selezionarla manualmente. Il percorso verra' "
        "memorizzato per i prossimi avvii."
    )

    # === INSTALLARE UN SETUP ===
    pdf.section_title("4. Installare un setup")
    pdf.subsection("Metodo 1: Drag & Drop")
    pdf.step(1, "Trascina un file .svm (o un archivio .zip/.7z/.rar) sulla finestra dell'app")
    pdf.step(2, "L'app rileva automaticamente auto e tracciato")
    pdf.step(3, "Verifica la selezione e clicca \"Installa\" (o premi Ctrl+I)")

    pdf.subsection("Metodo 2: Sfoglia")
    pdf.step(1, "Clicca \"Sfoglia...\" nella sezione File Setup (o premi Ctrl+O)")
    pdf.step(2, "Seleziona uno o piu' file .svm o archivi compressi")
    pdf.step(3, "Verifica auto e tracciato, poi clicca \"Installa\"")

    pdf.info_box(
        "Il campo Tracciato e' opzionale. Se lasciato vuoto, il setup viene copiato "
        "nella cartella radice dell'auto. Puoi anche digitare un nome tracciato nuovo."
    )

    # === FILE COMPRESSI ===
    pdf.add_page()
    pdf.section_title("5. File compressi")
    pdf.body_text(
        "L'app supporta archivi .zip, .7z e .rar. Quando carichi un archivio:\n\n"
        "1. L'archivio viene estratto in una cartella temporanea\n"
        "2. Vengono cercati tutti i file .svm ricorsivamente nelle sottocartelle\n"
        "3. Se c'e' un solo .svm, viene caricato direttamente\n"
        "4. Se ce ne sono piu' di uno, puoi scegliere quale installare "
        "oppure procedere con l'installazione batch"
    )
    pdf.info_box(
        "Le cartelle temporanee vengono pulite automaticamente alla chiusura dell'app."
    )

    # === INSTALLAZIONE BATCH ===
    pdf.section_title("6. Installazione batch")
    pdf.body_text(
        "Puoi installare piu' setup contemporaneamente in due modi:\n\n"
        "1. Trascinando piu' file sulla finestra\n"
        "2. Selezionando piu' file dal dialog \"Sfoglia\" (Ctrl+click o Shift+click)\n\n"
        "In modalita' batch, l'app tenta di rilevare auto e tracciato per ciascun file. "
        "Se la detection fallisce, usa come fallback l'auto e il tracciato selezionati "
        "nella finestra.\n\n"
        "Al termine, viene mostrato un riepilogo con lo stato di ciascun file."
    )

    # === ANTEPRIMA ===
    pdf.section_title("7. Anteprima setup")
    pdf.body_text(
        "Quando carichi un file .svm, la sezione \"Anteprima Setup\" mostra "
        "i parametri chiave estratti dal file:"
    )
    pdf.bullet("Pressione gomme anteriori e posteriori (kPa)")
    pdf.bullet("Ala anteriore e posteriore")
    pdf.bullet("Carburante (litri)")
    pdf.bullet("Bilanciamento freni")
    pdf.bullet("Barre antirollio anteriore e posteriore")
    pdf.bullet("Rapporto finale")
    pdf.bullet("Toe e Camber (anteriore e posteriore)")
    pdf.ln(2)
    pdf.body_text(
        "I parametri mostrati dipendono dal contenuto del file .svm: "
        "vengono visualizzati solo quelli effettivamente presenti."
    )

    # === CRONOLOGIA ===
    pdf.section_title("8. Cronologia installazioni")
    pdf.body_text(
        "Nella parte inferiore della finestra, la sezione \"Cronologia\" mostra "
        "le ultime 20 installazioni con data, nome file, auto e tracciato.\n\n"
        "Azioni disponibili:"
    )
    pdf.bullet("Doppio click su una voce: apre la cartella di destinazione in Esplora risorse")
    pdf.bullet("Pulsante \"Svuota\": cancella tutta la cronologia")
    pdf.ln(2)
    pdf.body_text(
        "La cronologia e' salvata nel file di configurazione e persiste tra le sessioni."
    )

    # === ROLLBACK ===
    pdf.section_title("9. Rollback")
    pdf.body_text(
        "Se hai abilitato il backup automatico (opzione attiva per default), "
        "ogni volta che un setup viene sovrascritto ne viene creata una copia .svm.bak.\n\n"
        "Per ripristinare un backup:"
    )
    pdf.step(1, "Clicca \"Rollback\" (o premi Ctrl+R)")
    pdf.step(2, "L'app cerca i file .bak nella cartella dell'ultima installazione")
    pdf.step(3, "Se ce ne sono piu' di uno, scegli quale ripristinare")
    pdf.step(4, "Conferma il ripristino")
    pdf.ln(2)
    pdf.body_text(
        "Il file .bak viene copiato sopra il file .svm corrente, ripristinando "
        "il setup precedente."
    )

    # === SCORCIATOIE ===
    pdf.add_page()
    pdf.section_title("10. Scorciatoie tastiera")
    pdf.shortcut_row("Ctrl+O", "Apre il dialog per sfogliare file setup o archivi")
    pdf.shortcut_row("Ctrl+I", "Avvia l'installazione del setup (o batch)")
    pdf.shortcut_row("Ctrl+R", "Avvia il rollback dell'ultimo backup")

    # === OPZIONI ===
    pdf.section_title("11. Opzioni")
    pdf.subsection("Sovrascrivi se il file esiste gia'")
    pdf.body_text(
        "Se abilitata (default), il file di destinazione viene sovrascritto. "
        "Se disabilitata, i file esistenti vengono saltati."
    )
    pdf.subsection("Backup automatico (.svm.bak)")
    pdf.body_text(
        "Se abilitata (default), prima della sovrascrittura viene creata "
        "una copia del file esistente con estensione .svm.bak. "
        "Questo backup puo' essere ripristinato con la funzione Rollback."
    )

    # === STRUTTURA CARTELLE ===
    pdf.section_title("12. Struttura cartelle LMU")
    pdf.body_text(
        "L'app si aspetta la seguente struttura dentro la cartella Settings:"
    )
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(30, 30, 30)
    tree = (
        "Documenti/\n"
        "  Le Mans Ultimate/\n"
        "    UserData/\n"
        "      player/\n"
        "        Settings/\n"
        "          Ferrari 499P/         <- cartella auto\n"
        "            Le Mans/            <- cartella tracciato\n"
        "            Monza/\n"
        "            setup_base.svm\n"
        "          Toyota GR010/\n"
        "          Peugeot 9X8/\n"
        "          ..."
    )
    pdf.set_fill_color(240, 242, 245)
    y0 = pdf.get_y()
    pdf.set_x(15)
    pdf.multi_cell(170, 5, tree, fill=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.body_text(
        "I setup possono essere copiati nella cartella radice dell'auto "
        "o in una sottocartella dedicata al tracciato."
    )

    # === RISOLUZIONE PROBLEMI ===
    pdf.section_title("13. Risoluzione problemi")
    pdf.subsection("\"Cartella LMU non trovata\"")
    pdf.body_text(
        "Clicca \"Sfoglia...\" e cerca manualmente la cartella "
        "Settings dentro la directory di LMU nei Documenti."
    )
    pdf.subsection("\"Nessun .svm trovato nell'archivio\"")
    pdf.body_text(
        "L'archivio non contiene file .svm. Verifica il contenuto "
        "dell'archivio e che i file abbiano estensione .svm."
    )
    pdf.subsection("Auto/tracciato non rilevati")
    pdf.body_text(
        "Alcuni file .svm non contengono i metadati per l'auto-detection. "
        "In questo caso, seleziona manualmente auto e tracciato dai menu a tendina."
    )
    pdf.subsection("Windows SmartScreen blocca l'avvio")
    pdf.body_text(
        "Clicca \"Ulteriori informazioni\" e poi \"Esegui comunque\". "
        "Questo accade perche' l'eseguibile non e' firmato digitalmente."
    )

    # === OUTPUT ===
    pdf.output(str(output))


def generate_guide_en(output: Path):
    pdf = GuidaPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Override header/footer for English
    original_header = pdf.header
    original_footer = pdf.footer

    def header_en(self=pdf):
        if self.page_no() == 1:
            return
        self.set_fill_color(*GuidaPDF.NAVY)
        self.rect(0, 0, 210, 12, style="F")
        self.set_fill_color(*GuidaPDF.RED)
        self.rect(0, 12, 210, 1.5, style="F")
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GuidaPDF.GRAY)
        self.set_xy(10, 4)
        self.cell(0, 5, "LMU Setup Installer v6 - User Guide", align="L")
        self.ln(12)

    def footer_en(self=pdf):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GuidaPDF.GRAY)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    pdf.header = header_en
    pdf.footer = footer_en

    # === COVER ===
    pdf.add_page()
    pdf.set_fill_color(*GuidaPDF.NAVY)
    pdf.rect(0, 0, 210, 297, style="F")
    pdf.set_fill_color(*GuidaPDF.GOLD)
    pdf.rect(0, 100, 210, 3, style="F")
    pdf.rect(0, 180, 210, 3, style="F")
    pdf.set_fill_color(*GuidaPDF.RED)
    pdf.rect(0, 103, 210, 1, style="F")
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*GuidaPDF.WHITE)
    pdf.set_xy(0, 115)
    pdf.cell(0, 20, "LMU Setup Installer", align="C")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(*GuidaPDF.GOLD)
    pdf.set_xy(0, 138)
    pdf.cell(0, 10, "User Guide", align="C")
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(*GuidaPDF.GRAY)
    pdf.set_xy(0, 155)
    pdf.cell(0, 10, "Version 6.0", align="C")
    sq = 8
    sx, sy = 75, 200
    for r in range(3):
        for c in range(8):
            if (r + c) % 2 == 0:
                pdf.set_fill_color(*GuidaPDF.GOLD)
            else:
                pdf.set_fill_color(*GuidaPDF.WHITE)
            pdf.rect(sx + c * sq, sy + r * sq, sq, sq, style="F")

    # === INTRODUCTION ===
    pdf.add_page()
    pdf.section_title("1. Introduction")
    pdf.body_text(
        "LMU Setup Installer is a Windows desktop application that simplifies "
        "the installation of Le Mans Ultimate setup files (.svm).\n\n"
        "Instead of manually copying files into the correct subfolders, "
        "just drag a file (or a compressed archive) onto the app window: "
        "the program automatically detects the car and track and copies the setup "
        "to the correct location."
    )

    pdf.subsection("Key features")
    pdf.bullet("Automatic detection of the LMU Settings folder")
    pdf.bullet("Automatic detection of car and track from the .svm file")
    pdf.bullet("Compressed file support: .zip, .7z, .rar")
    pdf.bullet("Batch installation (multiple setups at once)")
    pdf.bullet("Setup parameter preview (tire pressures, wings, fuel...)")
    pdf.bullet("History of the last 20 installations")
    pdf.bullet("Rollback: restore a backup with one click")
    pdf.bullet("Keyboard shortcuts: Ctrl+O, Ctrl+I, Ctrl+R")
    pdf.bullet("Drag & Drop (drag files/archives onto the window)")
    pdf.bullet("Automatic backup (.svm.bak) before overwriting")

    # === INSTALLATION ===
    pdf.section_title("2. Installation")
    pdf.body_text(
        "LMU Setup Installer requires no installation. Simply download "
        "\"LMU Setup Installer.exe\" from the dist\\ folder and run it.\n\n"
        "The file is a standalone executable (~22 MB) that includes all dependencies."
    )
    pdf.info_box(
        "Note: On first launch, Windows SmartScreen may show a warning. "
        "Click \"More info\" and then \"Run anyway\"."
    )

    # === FIRST LAUNCH ===
    pdf.section_title("3. First launch")
    pdf.body_text(
        "On startup, the application tries to automatically find the Le Mans Ultimate "
        "Settings folder by searching in:"
    )
    pdf.bullet("Documents\\Le Mans Ultimate\\UserData\\player\\Settings")
    pdf.bullet("Documents\\LeMansUltimate\\UserData\\player\\Settings")
    pdf.bullet("Documents\\LMU\\UserData\\player\\Settings")
    pdf.ln(2)
    pdf.body_text(
        "If the folder is found, the \"Path\" field is filled automatically "
        "and the list of available cars is populated.\n\n"
        "If not found, use the \"Browse...\" button in the \"LMU Folder\" section "
        "to select it manually. The path will be saved for future sessions."
    )

    # === INSTALLING A SETUP ===
    pdf.section_title("4. Installing a setup")
    pdf.subsection("Method 1: Drag & Drop")
    pdf.step(1, "Drag an .svm file (or a .zip/.7z/.rar archive) onto the app window")
    pdf.step(2, "The app automatically detects car and track")
    pdf.step(3, "Verify the selection and click \"Install\" (or press Ctrl+I)")

    pdf.subsection("Method 2: Browse")
    pdf.step(1, "Click \"Browse...\" in the Setup File section (or press Ctrl+O)")
    pdf.step(2, "Select one or more .svm files or compressed archives")
    pdf.step(3, "Verify car and track, then click \"Install\"")

    pdf.info_box(
        "The Track field is optional. If left empty, the setup is copied to "
        "the car's root folder. You can also type a new track name."
    )

    # === COMPRESSED FILES ===
    pdf.add_page()
    pdf.section_title("5. Compressed files")
    pdf.body_text(
        "The app supports .zip, .7z and .rar archives. When you load an archive:\n\n"
        "1. The archive is extracted to a temporary folder\n"
        "2. All .svm files are searched recursively in subfolders\n"
        "3. If there is only one .svm, it is loaded directly\n"
        "4. If there are multiple, you can choose which one to install "
        "or proceed with batch installation"
    )
    pdf.info_box(
        "Temporary folders are cleaned up automatically when the app closes."
    )

    # === BATCH INSTALLATION ===
    pdf.section_title("6. Batch installation")
    pdf.body_text(
        "You can install multiple setups at once in two ways:\n\n"
        "1. Dragging multiple files onto the window\n"
        "2. Selecting multiple files from the \"Browse\" dialog (Ctrl+click or Shift+click)\n\n"
        "In batch mode, the app tries to detect car and track for each file. "
        "If detection fails, it uses the car and track selected in the window "
        "as a fallback.\n\n"
        "When done, a summary showing the status of each file is displayed."
    )

    # === PREVIEW ===
    pdf.section_title("7. Setup preview")
    pdf.body_text(
        "When you load an .svm file, the \"Setup Preview\" section shows "
        "key parameters extracted from the file:"
    )
    pdf.bullet("Front and rear tire pressures (kPa)")
    pdf.bullet("Front and rear wing")
    pdf.bullet("Fuel (liters)")
    pdf.bullet("Brake bias")
    pdf.bullet("Front and rear anti-roll bars")
    pdf.bullet("Final drive ratio")
    pdf.bullet("Toe and Camber (front and rear)")
    pdf.ln(2)
    pdf.body_text(
        "The parameters shown depend on the .svm file contents: "
        "only those actually present are displayed."
    )

    # === HISTORY ===
    pdf.section_title("8. Installation history")
    pdf.body_text(
        "At the bottom of the window, the \"History\" section shows "
        "the last 20 installations with date, filename, car and track.\n\n"
        "Available actions:"
    )
    pdf.bullet("Double-click an entry: opens the destination folder in File Explorer")
    pdf.bullet("\"Clear\" button: deletes the entire history")
    pdf.ln(2)
    pdf.body_text(
        "History is saved in the configuration file and persists across sessions."
    )

    # === ROLLBACK ===
    pdf.section_title("9. Rollback")
    pdf.body_text(
        "If automatic backup is enabled (on by default), a .svm.bak copy is "
        "created every time a setup is overwritten.\n\n"
        "To restore a backup:"
    )
    pdf.step(1, "Click \"Rollback\" (or press Ctrl+R)")
    pdf.step(2, "The app searches for .bak files in the last installation folder")
    pdf.step(3, "If there are multiple, choose which one to restore")
    pdf.step(4, "Confirm the restoration")
    pdf.ln(2)
    pdf.body_text(
        "The .bak file is copied over the current .svm file, restoring "
        "the previous setup."
    )

    # === SHORTCUTS ===
    pdf.add_page()
    pdf.section_title("10. Keyboard shortcuts")
    pdf.shortcut_row("Ctrl+O", "Opens the file browser for setup files or archives")
    pdf.shortcut_row("Ctrl+I", "Starts the setup installation (or batch)")
    pdf.shortcut_row("Ctrl+R", "Starts rollback of the last backup")

    # === OPTIONS ===
    pdf.section_title("11. Options")
    pdf.subsection("Overwrite if file already exists")
    pdf.body_text(
        "If enabled (default), the destination file is overwritten. "
        "If disabled, existing files are skipped."
    )
    pdf.subsection("Automatic backup (.svm.bak)")
    pdf.body_text(
        "If enabled (default), a copy of the existing file is created "
        "with the .svm.bak extension before overwriting. "
        "This backup can be restored using the Rollback feature."
    )

    # === FOLDER STRUCTURE ===
    pdf.section_title("12. LMU folder structure")
    pdf.body_text(
        "The app expects the following structure inside the Settings folder:"
    )
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(30, 30, 30)
    tree = (
        "Documents/\n"
        "  Le Mans Ultimate/\n"
        "    UserData/\n"
        "      player/\n"
        "        Settings/\n"
        "          Ferrari 499P/         <- car folder\n"
        "            Le Mans/            <- track folder\n"
        "            Monza/\n"
        "            setup_base.svm\n"
        "          Toyota GR010/\n"
        "          Peugeot 9X8/\n"
        "          ..."
    )
    pdf.set_fill_color(240, 242, 245)
    pdf.set_x(15)
    pdf.multi_cell(170, 5, tree, fill=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.body_text(
        "Setups can be copied to the car's root folder "
        "or to a subfolder dedicated to a specific track."
    )

    # === TROUBLESHOOTING ===
    pdf.section_title("13. Troubleshooting")
    pdf.subsection("\"LMU folder not found\"")
    pdf.body_text(
        "Click \"Browse...\" and manually locate the Settings folder "
        "inside the LMU directory in your Documents."
    )
    pdf.subsection("\"No .svm found in archive\"")
    pdf.body_text(
        "The archive doesn't contain .svm files. Check the archive contents "
        "and make sure the files have the .svm extension."
    )
    pdf.subsection("Car/track not detected")
    pdf.body_text(
        "Some .svm files don't contain metadata for auto-detection. "
        "In this case, manually select car and track from the dropdown menus."
    )
    pdf.subsection("Windows SmartScreen blocks launch")
    pdf.body_text(
        "Click \"More info\" and then \"Run anyway\". "
        "This happens because the executable is not digitally signed."
    )

    # === OUTPUT ===
    pdf.output(str(output))


if __name__ == "__main__":
    base = Path(__file__).parent
    out_it = base / "LMU Setup Installer - Guida Utente.pdf"
    out_en = base / "LMU Setup Installer - User Guide.pdf"
    generate_guide(out_it)
    print(f"PDF IT generato: {out_it}")
    generate_guide_en(out_en)
    print(f"PDF EN generato: {out_en}")
