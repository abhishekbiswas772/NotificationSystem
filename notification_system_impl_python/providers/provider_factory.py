import os
from typing import Dict
from helpers.enums import ProviderType
from providers.base_provider import NotificationProvider
from providers.smtp_provider import GmailProvider, OutlookProvider, SMTPProvider
from providers.sms_provider import ConsoleSMSProvider, TextbeltProvider
from providers.fcm_provider import FCMProvider
from providers.local_provider import LocalProvider
from dotenv import load_dotenv

load_dotenv()


def get_provider_map() -> Dict[ProviderType, NotificationProvider]:
    """Creates a map of providers based on environment configuration"""
    providers = {}
    smtp_provider = os.getenv("SMTP_PROVIDER", "").lower()

    if smtp_provider == "gmail":
        email = os.getenv("GMAIL_EMAIL")
        password = os.getenv("GMAIL_APP_PASSWORD")
        if email and password:
            print("Using Gmail SMTP for email notifications")
            providers[ProviderType.GMAIL] = GmailProvider(email, password)
        else:
            print("Gmail credentials not found")

    elif smtp_provider == "outlook":
        email = os.getenv("OUTLOOK_EMAIL")
        password = os.getenv("OUTLOOK_PASSWORD")
        if email and password:
            print("Using Outlook SMTP for email notifications")
            providers[ProviderType.OUTLOOK] = OutlookProvider(email, password)
        else:
            print("Outlook credentials not found")

    elif smtp_provider == "custom":
        host = os.getenv("SMTP_HOST")
        port = os.getenv("SMTP_PORT", "587")
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL")
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        if host and username and password:
            print(f"Using custom SMTP ({host}:{port}) for email notifications")
            providers[ProviderType.CUSTOM_SMTP] = SMTPProvider(
                host=host,
                port=int(port),
                username=username,
                password=password,
                from_email=from_email,
                use_tls=use_tls
            )
        else:
            print("Custom SMTP credentials not found")
    sms_provider = os.getenv("SMS_PROVIDER", "console").lower()

    if sms_provider == "console":
        print("Using Console SMS provider (logs to terminal)")
        providers[ProviderType.CONSOLE_SMS] = ConsoleSMSProvider()

    elif sms_provider == "textbelt":
        api_key = os.getenv("TEXTBELT_API_KEY", "textbelt")
        print("Using Textbelt for SMS notifications (1 free SMS/day)")
        providers[ProviderType.TEXTBELT] = TextbeltProvider(api_key)

    fcm_key = os.getenv("FCM_SERVER_KEY")
    if fcm_key:
        print("Using Firebase FCM for push notifications")
        providers[ProviderType.FCM] = FCMProvider(fcm_key)
    else:
        print("FCM server key not found")

    if ProviderType.GMAIL not in providers and ProviderType.OUTLOOK not in providers and ProviderType.CUSTOM_SMTP not in providers:
        print("Using local provider for email (configure SMTP_PROVIDER in .env)")
        providers[ProviderType.LOCAL] = LocalProvider()

    if ProviderType.CONSOLE_SMS not in providers and ProviderType.TEXTBELT not in providers:
        print("Using console SMS provider (configure SMS_PROVIDER in .env)")
        providers[ProviderType.CONSOLE_SMS] = ConsoleSMSProvider()

    if ProviderType.FCM not in providers:
        print("Using local provider for push (configure FCM_SERVER_KEY in .env)")
        providers[ProviderType.LOCAL] = LocalProvider()

    return providers


def validate_provider_configuration():
    smtp_provider = os.getenv("SMTP_PROVIDER", "").lower()

    if smtp_provider == "gmail":
        if not os.getenv("GMAIL_EMAIL") or not os.getenv("GMAIL_APP_PASSWORD"):
            print("Warning: Gmail SMTP configured but credentials missing")

    sms_provider = os.getenv("SMS_PROVIDER", "console").lower()
    if sms_provider == "textbelt":
        print("Note: Textbelt free tier allows 1 SMS per day")

    if not os.getenv("FCM_SERVER_KEY"):
        print("Note: FCM not configured. Push notifications will use local provider")
