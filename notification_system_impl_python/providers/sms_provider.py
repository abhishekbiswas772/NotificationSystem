import json
import os
import requests
from datetime import datetime
from typing import Dict, Any
from providers.base_provider import NotificationProvider
from dotenv import load_dotenv

load_dotenv()



class ConsoleSMSProvider(NotificationProvider):
    def provider_name(self) -> str:
        return "console_sms"

    def send(self, notification) -> Dict[str, Any]:
        try:
            payload = json.loads(notification.payload)

            to = payload.get('to')
            body = payload.get('body', '')

            if not to:
                return {'success': False, 'message': 'Missing "to" field in payload'}

            if not body:
                return {'success': False, 'message': 'Missing "body" field in payload'}

            print("\n" + "-" * 55)
            print("SMS NOTIFICATION")
            print("-" * 55)
            print(f"To:      {to}")
            print(f"Message: {body}")
            print(f"Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 55 + "\n")

            return {
                'success': True,
                'message': f'SMS logged to console for {to}',
                'response': {'to': to, 'body': body}
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Console SMS failed: {str(e)}'
            }


class TextbeltProvider(NotificationProvider):
    def __init__(self, api_key: str = "textbelt"):
        self.api_key = api_key or "textbelt"  
        self.api_url = "https://textbelt.com/text"

    def provider_name(self) -> str:
        return "textbelt"

    def send(self, notification) -> Dict[str, Any]:
        try:
            payload = json.loads(notification.payload)

            to = payload.get('to')
            body = payload.get('body', '')

            if not to:
                return {'success': False, 'message': 'Missing "to" field in payload'}

            if not body:
                return {'success': False, 'message': 'Missing "body" field in payload'}

            request_data = {
                'phone': to,
                'message': body,
                'key': self.api_key
            }

            response = requests.post(
                self.api_url,
                json=request_data,
                timeout=10
            )

            result = response.json()
            if result.get('success'):
                return {
                    'success': True,
                    'message': f'SMS sent via Textbelt to {to}',
                    'response': result
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    'success': False,
                    'message': f'Textbelt error: {error_msg}',
                    'response': result
                }

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Textbelt request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Textbelt send failed: {str(e)}'
            }


def load_sms_provider_from_env() -> NotificationProvider:
    provider = os.getenv("SMS_PROVIDER", "console").lower()

    if provider == "textbelt":
        api_key = os.getenv("TEXTBELT_API_KEY", "textbelt")
        return TextbeltProvider(api_key)
    else:
        return ConsoleSMSProvider()
