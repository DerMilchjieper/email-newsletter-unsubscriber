# Email Newsletter Unsubscriber PowerShell Launcher

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "        Email Newsletter Unsubscriber Launcher          " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".env")) {
    Write-Host "[!] Warnung: Keine .env Datei gefunden." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[+] Die Datei .env wurde aus .env.example erstellt. Bitte trage deine Zugangsdaten ein." -ForegroundColor Green
    Read-Host "Drücke Enter, sobald du die .env bearbeitet hast..."
}

Write-Host "[*] Installiere/Prüfe Abhängigkeiten aus requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "Wähle eine Aktion:" -ForegroundColor Green
Write-Host "[1] Postfach scannen (Vorschau / Scan)"
Write-Host "[2] Abmeldung ausführen (Unsubscribe All)"
Write-Host "[3] Beide Schritte nacheinander ausführen"
Write-Host ""

$choice = Read-Host "Bitte wähle [1, 2 oder 3]"

switch ($choice) {
    "1" {
        Write-Host "`n[*] Starte Scan..." -ForegroundColor Yellow
        python main.py scan --method imap
    }
    "2" {
        Write-Host "`n[*] Starte Abmeldung..." -ForegroundColor Yellow
        python main.py unsubscribe --all
    }
    "3" {
        Write-Host "`n[*] Starte Scan..." -ForegroundColor Yellow
        python main.py scan --method imap
        Write-Host "`n[*] Starte Abmeldung..." -ForegroundColor Yellow
        python main.py unsubscribe --all
    }
    Default {
        Write-Host "[!] Ungültige Auswahl." -ForegroundColor Red
    }
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "Vorgang abgeschlossen." -ForegroundColor Cyan
Read-Host "Drücke Enter zum Beenden..."
