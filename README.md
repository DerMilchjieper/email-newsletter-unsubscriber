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

## 🛠️ Quick Start

### 1. Installation

Clone this repository:
```bash
git clone https://github.com/your-username/email-newsletter-unsubscriber.git
cd email-newsletter-unsubscriber
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

### 2. Configuration

Create a `.env` file in the root directory (or edit the provided template):

#### For GMX / Web.de / Standard IMAP:
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
