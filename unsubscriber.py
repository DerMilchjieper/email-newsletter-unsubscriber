import requests
import urllib.parse
from typing import Dict, Any

class Unsubscriber:
    def __init__(self, gmail_service=None):
        self.gmail_service = gmail_service

    def unsubscribe(self, newsletter_item: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to unsubscribe using HTTPS RFC 8058, standard HTTP, or mailto."""
        sender = newsletter_item.get('sender_email', 'Unknown')
        sender_name = newsletter_item.get('sender_name_raw', sender)
        https_link = newsletter_item.get('unsubscribe_https')
        mailto_link = newsletter_item.get('unsubscribe_mailto')
        supports_one_click = newsletter_item.get('supports_one_click', False)

        result = {
            'sender': sender,
            'sender_name': sender_name,
            'status': 'FAILED',
            'method_used': None,
            'details': '',
            'url': https_link or mailto_link
        }

        # Method 1: RFC 8058 One-Click HTTPS POST
        if https_link and supports_one_click:
            try:
                resp = requests.post(
                    https_link,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    data={'List-Unsubscribe': 'One-Click'},
                    timeout=10
                )
                if resp.status_code in [200, 202, 204]:
                    result['status'] = 'SUCCESS'
                    result['method_used'] = 'RFC 8058 One-Click HTTPS POST'
                    result['details'] = f"HTTP {resp.status_code}"
                    return result
            except Exception as e:
                result['details'] += f"One-Click POST failed: {str(e)}; "

        # Method 2: Standard HTTPS GET/POST
        if https_link:
            try:
                resp = requests.get(https_link, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    result['status'] = 'SUCCESS'
                    result['method_used'] = 'Standard HTTPS GET'
                    result['details'] = f"HTTP {resp.status_code} (Opened unsubscribe page)"
                    return result
            except Exception as e:
                result['details'] += f"HTTPS GET failed: {str(e)}; "

        # Method 3: Mailto Unsubscribe via Gmail API
        if mailto_link and self.gmail_service:
            try:
                parsed_mailto = urllib.parse.urlparse(mailto_link)
                recipient = parsed_mailto.path
                query_params = urllib.parse.parse_qs(parsed_mailto.query)
                subject = query_params.get('subject', ['unsubscribe'])[0]
                
                import base64
                from email.mime.text import MIMEText
                
                message = MIMEText('unsubscribe')
                message['to'] = recipient
                message['subject'] = subject
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                self.gmail_service.users().messages().send(userId='me', body={'raw': raw}).execute()
                
                result['status'] = 'SUCCESS'
                result['method_used'] = 'Mailto Email via Gmail API'
                result['details'] = f"Sent mail to {recipient} with subject '{subject}'"
                return result
            except Exception as e:
                result['details'] += f"Mailto send failed: {str(e)}; "

        if not result['details']:
            result['details'] = 'Kein direkter Ein-Klick-Header vorhanden (Manuelle Abmeldung erforderlich)'
        
        return result
