import smtplib
import ssl
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from providers.base_provider import NotificationProvider
from dotenv import load_dotenv

load_dotenv()



class SMTPProvider(NotificationProvider):
    def __init__(self, host: str, port: int, username: str, password: str, from_email: str = None, use_tls: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email or username
        self.use_tls = use_tls

    def provider_name(self) -> str:
        return "smtp"

    def send(self, notification) -> Dict[str, Any]:
        try:
            payload = json.loads(notification.payload)

            to_email = payload.get('to')
            subject = payload.get('subject', 'Notification')
            body = payload.get('body', '')
            from_email = payload.get('from', self.from_email)

            if not to_email:
                return {'success': False, 'message': 'Missing "to" field in payload'}

            if not body:
                return {'success': False, 'message': 'Missing "body" field in payload'}

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to_email

            html_part = MIMEText(body, "html")
            message.attach(html_part)
            context = ssl.create_default_context()
            if self.use_tls:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls(context=context)
                    server.login(self.username, self.password)
                    server.send_message(message)
            else:
                with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                    server.login(self.username, self.password)
                    server.send_message(message)

            return {
                'success': True,
                'message': f'Email sent via SMTP to {to_email}',
                'response': {'to': to_email, 'subject': subject}
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'SMTP send failed: {str(e)}'
            }


class GmailProvider(SMTPProvider):

    def __init__(self, email: str, app_password: str):
        super().__init__(
            host="smtp.gmail.com",
            port=587,
            username=email,
            password=app_password,
            from_email=email,
            use_tls=True
        )

    def provider_name(self) -> str:
        return "gmail"


class OutlookProvider(SMTPProvider):

    def __init__(self, email: str, password: str):
        super().__init__(
            host="smtp-mail.outlook.com",
            port=587,
            username=email,
            password=password,
            from_email=email,
            use_tls=True
        )

    def provider_name(self) -> str:
        return "outlook"


def load_smtp_provider_from_env() -> Optional[SMTPProvider]:
    provider = os.getenv("SMTP_PROVIDER", "").lower()

    if provider == "gmail":
        email = os.getenv("GMAIL_EMAIL")
        password = os.getenv("GMAIL_APP_PASSWORD")
        if email and password:
            return GmailProvider(email, password)

    elif provider == "outlook":
        email = os.getenv("OUTLOOK_EMAIL")
        password = os.getenv("OUTLOOK_PASSWORD")
        if email and password:
            return OutlookProvider(email, password)

    elif provider == "custom":
        return SMTPProvider(
            host=os.getenv("SMTP_HOST", "localhost"),
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM_EMAIL"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        )

    return None
