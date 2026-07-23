# 📧 Email Newsletter Unsubscriber

An automated Python tool designed to scan your email inboxes (Gmail, GMX, Web.de, or any IMAP provider), group active newsletters, and automatically unsubscribe using RFC standards (**RFC 2369** and **RFC 8058 One-Click Unsubscribe**) and HTML link parsing.

---

## ✨ Features

- ⚡ **RFC 8058 One-Click Unsubscribe**: Sends standardized HTTP POST requests (`List-Unsubscribe=One-Click`).
- 🔗 **HTML Body Fallback Parser**: Extracts embedded unsubscribe links from email HTML when standard headers are missing.
- 🌐 **Multi-Provider Support**: Built-in auto-detection for **Gmail**, **GMX.net / GMX.de**, **Web.de**, and custom IMAP servers.
- 🔑 **Dual Authentication**: Supports Google OAuth 2.0 (Gmail API) and IMAP with App Passwords / `.env` configuration.
- 🛡️ **Safety & Privacy First**:
  - **Dry-Run Mode**: Scans and generates a report (`newsletters_report.md`) *before* unsubscribing.
  - **Account Protection**: Non-newsletter emails (security alerts, receipts, password resets) are safely ignored.
  - Zero third-party data tracking. Everything runs locally on your machine.

---

## 🚀 Quick Start & Launchers

### Easy One-Click Launchers

We provide ready-to-use launcher scripts for all platforms:

- **Windows Batch**: Double-click `run.bat` or execute `.\run.bat`
- **Windows PowerShell**: Right-click `run.ps1` -> *Run with PowerShell* or `.\run.ps1`
- **Linux / macOS Bash**: Run `./run.sh`

The launcher automatically checks for `.env`, installs required Python dependencies, and provides an interactive menu (Scan, Unsubscribe, or Both).

---

### Manual CLI Usage

#### Step 1: Installation & Configuration

Install dependencies:
```bash
pip install -r requirements.txt
```

Create `.env` file with your email credentials:
```env
GMX_ADDRESS=your_email@gmx.net
GMX_PASSWORD=your_gmx_password
```

#### For Gmail (IMAP with App Password):
```env
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_digit_app_password
```

---

### 3. Usage

#### Step 1: Scan Postbox (Dry-Run & Discovery)
```bash
python main.py scan --method imap
```

This generates:
- `newsletters_report.md`: Human-readable summary table.
- `newsletters_found.json`: Structured list of detected newsletters.

#### Step 2: Unsubscribe
To unsubscribe from all detected newsletters:
```bash
python main.py unsubscribe --all
```

Or edit `newsletters_found.json` to mark specific senders (`"selected": true`) and run:
```bash
python main.py unsubscribe
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
