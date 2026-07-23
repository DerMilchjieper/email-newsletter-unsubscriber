@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo         Email Newsletter Unsubscriber Launcher
echo ========================================================
echo.

IF NOT EXIST ".env" (
    echo [!] Warnung: Keine .env Datei gefunden.
    echo [!] Bitte kopiere .env.example zu .env und trage deine Zugangsdaten ein.
    echo.
    copy .env.example .env
    echo [.env erstellt aus Template. Bitte jetzt anpassen!]
    pause
    exit /b
)

echo [*] Prüfe und installiere Abhängigkeiten...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [!] Fehler bei der Installation der Abhängigkeiten.
    pause
    exit /b
)

echo.
echo Wähle eine Aktion:
echo [1] Postfach scannen (Vorschau / Scan)
echo [2] Abmeldung ausführen (Unsubscribe All)
echo [3] Beide Schritte nacheinander ausführen
echo.
set /p CHOICE="Bitte wähle [1, 2 oder 3]: "

if "%CHOICE%"=="1" (
    echo.
    echo [*] Starte Scan...
    python main.py scan --method imap
) else if "%CHOICE%"=="2" (
    echo.
    echo [*] Starte Abmeldung...
    python main.py unsubscribe --all
) else if "%CHOICE%"=="3" (
    echo.
    echo [*] Starte Scan...
    python main.py scan --method imap
    echo.
    echo [*] Starte Abmeldung...
    python main.py unsubscribe --all
) else (
    echo [!] Ungültige Auswahl.
)

echo.
echo ========================================================
echo Abgeschlossen.
pause
