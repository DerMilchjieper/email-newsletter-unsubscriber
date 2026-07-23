import os
import sys
import json
import argparse
from scanner import GmailApiScanner, ImapScanner
from unsubscriber import Unsubscriber

# Try loading environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def cmd_scan(args):
    newsletters = []
    gmail_service = None
    
    # Determine method based on arguments or environment variables
    email_addr = (args.email or os.getenv('GMX_ADDRESS') or os.getenv('GMAIL_ADDRESS') or '').strip()
    app_passwd = (args.password or os.getenv('GMX_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD') or '').replace(' ', '').strip()
    
    # Auto-detect IMAP server if not explicitly passed
    imap_server = args.server or os.getenv('IMAP_SERVER')
    if not imap_server:
        if email_addr.lower().endswith(('@gmx.net', '@gmx.de', '@gmx.at', '@gmx.ch')):
            imap_server = 'imap.gmx.net'
        elif email_addr.lower().endswith('@web.de'):
            imap_server = 'imap.web.de'
        else:
            imap_server = 'imap.gmail.com'

    # If method is default ('api') but user configured .env with credentials and no credentials.json exists, default to IMAP
    method = args.method
    if method == 'api' and not os.path.exists(args.credentials) and email_addr and app_passwd:
        print(f"[Info] Nutze IMAP-Modus für {email_addr} auf Server {imap_server}...")
        method = 'imap'

    if method == 'api':
        scanner = GmailApiScanner(credentials_path=args.credentials, token_path=args.token)
        try:
            scanner.authenticate()
            gmail_service = scanner.service
            newsletters = scanner.scan_newsletters(max_results=args.max)
        except Exception as e:
            print(f"[Error] Gmail API scan failed: {e}")
            print("Tipp: Falls du GMX oder IMAP nutzt, starte mit: python main.py scan --method imap")
            sys.exit(1)
    else:
        if not email_addr or not app_passwd:
            print("[Error] Für den IMAP-Modus wird E-Mail und Passwort in der .env-Datei oder per Commandline benötigt.")
            sys.exit(1)
        scanner = ImapScanner(email_address=email_addr, app_password=app_passwd, imap_server=imap_server)
        try:
            newsletters = scanner.scan_newsletters(max_results=args.max)
        except Exception as e:
            print(f"[Error] IMAP scan failed on {imap_server}: {e}")
            sys.exit(1)

    # Save raw JSON data
    output_json = 'newsletters_found.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(newsletters, f, indent=2, ensure_ascii=False)
    print(f"\n[Success] Found {len(newsletters)} distinct newsletter senders.")
    print(f"[Output] Saved details to '{output_json}'.")

    # Generate Markdown Report
    report_md = 'newsletters_report.md'
    with open(report_md, 'w', encoding='utf-8') as f:
        f.write("# Gmail Newsletter Discovery Report\n\n")
        f.write(f"Total Newsletters / Senders Found: **{len(newsletters)}**\n\n")
        f.write("Review the list below. To unsubscribe from specific senders, set `\"selected\": true` in `newsletters_found.json` or run `python main.py unsubscribe --all` to process all.\n\n")
        f.write("| Selected | Sender | Emails Found | One-Click Ready | Latest Subject |\n")
        f.write("| :---: | :--- | :---: | :---: | :--- |\n")
        
        for item in sorted(newsletters, key=lambda x: x['email_count'], reverse=True):
            one_click = "✅" if item.get('supports_one_click') or item.get('unsubscribe_https') else "⚠️ Mailto"
            sender_str = item.get('sender_name_raw', item.get('sender_email'))
            subject_str = item.get('latest_subject', 'N/A')
            f.write(f"| [ ] | `{sender_str}` | {item.get('email_count')} | {one_click} | {subject_str} |\n")
            
    print(f"[Output] Generated markdown summary report in '{report_md}'.\n")

def cmd_unsubscribe(args):
    input_json = 'newsletters_found.json'
    if not os.path.exists(input_json):
        print(f"[Error] '{input_json}' nicht gefunden! Bitte führe zuerst 'python main.py scan' aus.")
        sys.exit(1)
        
    with open(input_json, 'r', encoding='utf-8') as f:
        newsletters = json.load(f)

    if not newsletters:
        print("[Info] Keine Newsletter zum Verarbeiten gefunden.")
        return

    # Filter selected items if not --all
    if not args.all:
        selected_items = [n for n in newsletters if n.get('selected', False)]
        if not selected_items:
            print("[Info] Keine Einträge mit 'selected: true' markiert. Verarbeite ALLE Newsletter...")
            selected_items = newsletters
    else:
        selected_items = newsletters

    print(f"\n[Unsubscribe] Verarbeite {len(selected_items)} Newsletter-Absender...")
    
    # Try initializing Gmail API service if available for mailto fallback
    gmail_service = None
    if os.path.exists(args.token):
        try:
            scanner = GmailApiScanner(credentials_path=args.credentials, token_path=args.token)
            scanner.authenticate()
            gmail_service = scanner.service
        except Exception:
            pass

    unsub = Unsubscriber(gmail_service=gmail_service)
    results = []
    
    for idx, item in enumerate(selected_items, start=1):
        sender = item.get('sender_email', 'Unknown')
        print(f"[{idx}/{len(selected_items)}] Melde ab von {sender}...")
        res = unsub.unsubscribe(item)
        results.append(res)
        print(f"  -> {res['status']}: {res['method_used'] or res['details']}")

    # Summary
    successes = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed_items = [r for r in results if r['status'] == 'FAILED']
    
    print(f"\n[Summary] Erfolgreich von {successes}/{len(selected_items)} Newslettern abgemeldet.")
    
    # Output list of failed unsubscribes with URLs if any exist
    if failed_items:
        print("\n" + "=" * 60)
        print("⚠️  NICHT AUTOMATISCH ABGEMELDET (MANUELLE ABMELDUNG NÖTIG):")
        print("=" * 60)
        
        failed_report_file = 'failed_unsubscribes.md'
        with open(failed_report_file, 'w', encoding='utf-8') as f_out:
            f_out.write("# Manuelle Abmeldeliste\n\n")
            f_out.write("Folgende Newsletter konnten nicht automatisch per Ein-Klick abgemeldet werden. Klicke auf die Links, um dich manuell abzumelden:\n\n")
            f_out.write("| # | Absender / Name | Abmelde-Link |\n")
            f_out.write("| :---: | :--- | :--- |\n")
            
            for idx, item in enumerate(failed_items, start=1):
                name = item.get('sender_name', item.get('sender', 'Unknown'))
                url = item.get('url') or 'Kein Link in E-Mail gefunden'
                
                # Format short display URL
                short_url_display = url
                if len(url) > 60:
                    short_url_display = url[:57] + "..."
                
                link_md = f"[{short_url_display}]({url})" if url.startswith('http') else url
                f_out.write(f"| {idx} | `{name}` | {link_md} |\n")
                
                print(f"{idx}. {name}")
                print(f"   Link: {url}\n")
                
        print("=" * 60)
        print(f"[Output] Übersicht der nicht abgemeldeten Newsletter gespeichert in '{failed_report_file}'.")

    with open('unsubscribe_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("[Output] Ausführlicher Protokollbericht in 'unsubscribe_results.json' gespeichert.")

def main():
    parser = argparse.ArgumentParser(description="Gmail Newsletter Scanner & Unsubscriber Utility")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Scan command
    scan_parser = subparsers.add_parser('scan', help="Scan inbox for newsletters")
    scan_parser.add_argument('--method', choices=['api', 'imap'], default='api', help="Authentication method (default: api)")
    scan_parser.add_argument('--max', type=int, default=200, help="Max email messages to inspect (default: 200)")
    scan_parser.add_argument('--server', help="IMAP server hostname (e.g. imap.gmx.net, imap.gmail.com)")
    scan_parser.add_argument('--credentials', default='credentials.json', help="OAuth credentials JSON path")
    scan_parser.add_argument('--token', default='token.json', help="OAuth token storage JSON path")
    scan_parser.add_argument('--email', help="Gmail address (overrides .env)")
    scan_parser.add_argument('--password', help="App Password (overrides .env)")

    # Unsubscribe command
    unsub_parser = subparsers.add_parser('unsubscribe', help="Execute unsubscribe requests")
    unsub_parser.add_argument('--all', action='store_true', help="Unsubscribe from all found newsletters without requiring manual selection")
    unsub_parser.add_argument('--credentials', default='credentials.json', help="OAuth credentials JSON path")
    unsub_parser.add_argument('--token', default='token.json', help="OAuth token storage JSON path")

    args = parser.parse_args()

    if args.command == 'scan':
        cmd_scan(args)
    elif args.command == 'unsubscribe':
        cmd_unsubscribe(args)

if __name__ == '__main__':
    main()
