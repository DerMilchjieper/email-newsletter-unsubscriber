#!/usr/bin/env bash

set -e

echo "========================================================"
echo "        Email Newsletter Unsubscriber Launcher"
echo "========================================================"
echo ""

if [ ! -f ".env" ]; then
    echo "[!] Warning: No .env file found."
    cp .env.example .env
    echo "[+] Created .env template from .env.example. Please update your credentials in .env!"
    read -p "Press Enter after updating your .env file..."
fi

echo "[*] Checking and installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Select an action:"
echo "[1] Scan inbox (Dry-Run / Report)"
echo "[2] Unsubscribe from all newsletters"
echo "[3] Run Scan and Unsubscribe sequentially"
echo ""

read -p "Enter choice [1, 2, or 3]: " choice

case $choice in
    1)
        echo ""
        echo "[*] Running scan..."
        python3 main.py scan --method imap
        ;;
    2)
        echo ""
        echo "[*] Running unsubscribe..."
        python3 main.py unsubscribe --all
        ;;
    3)
        echo ""
        echo "[*] Running scan..."
        python3 main.py scan --method imap
        echo ""
        echo "[*] Running unsubscribe..."
        python3 main.py unsubscribe --all
        ;;
    *)
        echo "[!] Invalid choice."
        ;;
esac

echo ""
echo "========================================================"
echo "Completed."
