@echo off
REM ============================================================
REM  Build script per LMU Setup Installer
REM  Richiede Python 3.10+ (con pip)
REM  Esegui questo file dalla cartella del progetto
REM ============================================================

echo [1/3] Installazione dipendenze (pyinstaller + pillow)...
pip install pyinstaller pillow --quiet

echo.
echo [2/3] Generazione icona lmu_icon.ico...
python -c "from lmu_setup_installer import export_icon; from pathlib import Path; ok = export_icon(Path('lmu_icon.ico')); print('  Icona generata!' if ok else '  Pillow non disponibile, build senza icona.')"

echo.
echo [3/3] Compilazione .exe in corso...
if exist lmu_icon.ico (
    pyinstaller ^
        --onefile ^
        --windowed ^
        --name "LMU Setup Installer" ^
        --icon lmu_icon.ico ^
        lmu_setup_installer.py
) else (
    pyinstaller ^
        --onefile ^
        --windowed ^
        --name "LMU Setup Installer" ^
        lmu_setup_installer.py
)

echo.
if exist "dist\LMU Setup Installer.exe" (
    echo  ================================================================
    echo   SUCCESSO!
    echo   Il file .exe si trova in:  dist\LMU Setup Installer.exe
    echo  ================================================================
) else (
    echo  ERRORE: la compilazione non e' riuscita.
    echo  Controlla l'output sopra per dettagli.
)

pause
