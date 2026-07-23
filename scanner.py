import os
import re
import json
import email
from email.header import decode_header
import imaplib
import urllib.parse
from typing import List, Dict, Any, Optional

# Optional Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

def parse_header_str(header_value: Optional[str]) -> str:
    """Decode encoded header values (e.g. utf-8, iso-8859-1)."""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for content, encoding in decoded_parts:
        if isinstance(content, bytes):
            try:
                result.append(content.decode(encoding or 'utf-8', errors='replace'))
            except Exception:
                result.append(content.decode('utf-8', errors='replace'))
        else:
            result.append(str(content))
    return "".join(result)

def extract_unsubscribe_links(header_value: str) -> Dict[str, Optional[str]]:
    """Extract mailto and http(s) URLs from List-Unsubscribe header."""
    res = {'https': None, 'mailto': None}
    if not header_value:
        return res
    
    links = re.findall(r'<([^>]+)>', header_value)
    for link in links:
        link = link.strip()
        if link.startswith('http://') or link.startswith('https://'):
            if not res['https']:
                res['https'] = link
        elif link.startswith('mailto:'):
            if not res['mailto']:
                res['mailto'] = link
    return res

def extract_body_unsubscribe_link(html_or_text_content: str) -> Optional[str]:
    """Fallback: Find links in email body containing unsubscribe/abmelden keywords."""
    if not html_or_text_content:
        return None
    
    # Search for hrefs with unsubscribe/abmelden in URL or anchor text
    urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', html_or_text_content, re.IGNORECASE)
    for url in urls:
        url_lower = url.lower()
        if any(k in url_lower for k in ['unsubscribe', 'abmelden', 'optout', 'opt-out', 'newsletter/cancel', 'preferences']):
            return url
    return None

class GmailApiScanner:
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries not installed. Please run: pip install -r requirements.txt")
        
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"OAuth credentials file '{self.credentials_path}' not found!")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token_file:
                token_file.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)

    def scan_newsletters(self, max_results: int = 200, query: str = 'category:promotions OR "unsubscribe" OR "abmelden"') -> List[Dict[str, Any]]:
        if not self.service:
            self.authenticate()
        
        print(f"[Scanner] Querying Gmail API (Query: '{query}', Max: {max_results})...")
        results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        senders_dict: Dict[str, Dict[str, Any]] = {}
        
        for idx, msg in enumerate(messages):
            if idx % 20 == 0 and idx > 0:
                print(f"[Scanner] Processed {idx}/{len(messages)} messages...")
                
            msg_data = self.service.users().messages().get(
                userId='me', id=msg['id'], format='full'
            ).execute()
            
            headers = msg_data.get('payload', {}).get('headers', [])
            header_map = {h['name'].lower(): h['value'] for h in headers}
            
            sender_raw = header_map.get('from', 'Unknown Sender')
            sender = parse_header_str(sender_raw)
            subject = parse_header_str(header_map.get('subject', 'No Subject'))
            list_unsub = header_map.get('list-unsubscribe', '')
            list_unsub_post = header_map.get('list-unsubscribe-post', '')
            
            unsub_links = extract_unsubscribe_links(list_unsub)
            
            email_match = re.search(r'<([^>]+)>', sender)
            sender_email = email_match.group(1) if email_match else sender
            
            # Fallback to body link if header missing
            body_link = None
            if not unsub_links['https']:
                snippet = msg_data.get('snippet', '')
                body_link = extract_body_unsubscribe_link(snippet)

            if sender_email not in senders_dict:
                senders_dict[sender_email] = {
                    'sender_name_raw': sender,
                    'sender_email': sender_email,
                    'email_count': 0,
                    'latest_subject': subject,
                    'list_unsubscribe_raw': list_unsub,
                    'unsubscribe_https': unsub_links['https'] or body_link,
                    'unsubscribe_mailto': unsub_links['mailto'],
                    'supports_one_click': 'List-Unsubscribe=One-Click' in list_unsub_post,
                    'sample_message_ids': []
                }
            
            entry = senders_dict[sender_email]
            entry['email_count'] += 1
            if len(entry['sample_message_ids']) < 5:
                entry['sample_message_ids'].append(msg['id'])
            if not entry['unsubscribe_https']:
                entry['unsubscribe_https'] = unsub_links['https'] or body_link
            if not entry['unsubscribe_mailto'] and unsub_links['mailto']:
                entry['unsubscribe_mailto'] = unsub_links['mailto']

        return list(senders_dict.values())

class ImapScanner:
    def __init__(self, email_address: str, app_password: str, imap_server: str = 'imap.gmail.com'):
        self.email_address = email_address.strip() if email_address else ''
        self.app_password = app_password.replace(' ', '').strip() if app_password else ''
        self.imap_server = imap_server

    def scan_newsletters(self, max_results: int = 200) -> List[Dict[str, Any]]:
        print(f"[Scanner] Connecting via IMAP to {self.imap_server}...")
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_address, self.app_password)
        mail.select('INBOX')
        
        # Search for messages with List-Unsubscribe or text 'unsubscribe' / 'abmelden'
        status, search_data = mail.search(None, 'OR (HEADER List-Unsubscribe "") (TEXT "unsubscribe")')
        if status != 'OK' or not search_data[0]:
            status, search_data = mail.search(None, 'ALL')
            
        if not search_data or not search_data[0]:
            print("[Scanner] No messages found via IMAP search.")
            return []
        
        msg_ids = search_data[0].split()
        msg_ids = msg_ids[-max_results:]
        
        senders_dict: Dict[str, Dict[str, Any]] = {}
        
        print(f"[Scanner] Inspecting {len(msg_ids)} messages via IMAP...")
        for i, m_id in enumerate(reversed(msg_ids)):
            if i % 20 == 0 and i > 0:
                print(f"[Scanner] Processed {i}/{len(msg_ids)} messages...")
            
            res, data = mail.fetch(m_id, '(RFC822)')
            if res != 'OK' or not data or not data[0]:
                continue
            
            raw_email = data[0][1]
            if isinstance(raw_email, bytes):
                msg_obj = email.message_from_bytes(raw_email)
            else:
                msg_obj = email.message_from_string(str(raw_email))
            
            sender_raw = msg_obj.get('From', 'Unknown')
            sender = parse_header_str(sender_raw)
            subject = parse_header_str(msg_obj.get('Subject', 'No Subject'))
            list_unsub = msg_obj.get('List-Unsubscribe', '')
            list_unsub_post = msg_obj.get('List-Unsubscribe-Post', '')
            
            unsub_links = extract_unsubscribe_links(list_unsub)
            
            # Extract body text/html for fallback link search
            body_link = None
            if not unsub_links['https']:
                body_content = ""
                if msg_obj.is_multipart():
                    for part in msg_obj.walk():
                        if part.get_content_type() in ['text/html', 'text/plain']:
                            try:
                                body_content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except Exception:
                                pass
                else:
                    try:
                        body_content = msg_obj.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except Exception:
                        pass
                body_link = extract_body_unsubscribe_link(body_content)

            email_match = re.search(r'<([^>]+)>', sender)
            sender_email = email_match.group(1) if email_match else sender
            
            if sender_email not in senders_dict:
                senders_dict[sender_email] = {
                    'sender_name_raw': sender,
                    'sender_email': sender_email,
                    'email_count': 0,
                    'latest_subject': subject,
                    'list_unsubscribe_raw': list_unsub,
                    'unsubscribe_https': unsub_links['https'] or body_link,
                    'unsubscribe_mailto': unsub_links['mailto'],
                    'supports_one_click': 'List-Unsubscribe=One-Click' in list_unsub_post,
                    'sample_message_ids': [m_id.decode('utf-8')]
                }
            
            entry = senders_dict[sender_email]
            entry['email_count'] += 1
            if not entry['unsubscribe_https']:
                entry['unsubscribe_https'] = unsub_links['https'] or body_link
            if not entry['unsubscribe_mailto'] and unsub_links['mailto']:
                entry['unsubscribe_mailto'] = unsub_links['mailto']
                
        mail.logout()
        return list(senders_dict.values())
