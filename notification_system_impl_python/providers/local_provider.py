import json
from datetime import datetime
from typing import Dict, Any
from providers.base_provider import NotificationProvider
from dotenv import load_dotenv

load_dotenv()


class LocalProvider(NotificationProvider):
    def provider_name(self) -> str:
        return "local"

    def send(self, notification) -> Dict[str, Any]:
        try:
            payload = json.loads(notification.payload)
            message_type = notification.message_type.value if hasattr(notification.message_type, 'value') else str(notification.message_type)
            print("\n" + "-" * 55)
            print(f"LOCAL NOTIFICATION - {message_type.upper()}")
            print("-" * 55)
            print(f"Notification ID: {notification.id}")
            print(f"User ID:         {notification.user_id}")
            print(f"Type:            {message_type}")
            print(f"Provider:        {notification.provider.value if hasattr(notification.provider, 'value') else str(notification.provider)}")
            print(f"Time:            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 55)
            for key, value in payload.items():
                if key == 'body' and len(str(value)) > 100:
                    print(f"{key.capitalize()}: {str(value)[:100]}...")
                else:
                    print(f"{key.capitalize()}: {value}")

            print("-" * 55 + "\n")

            return {
                'success': True,
                'message': 'Notification logged locally',
                'response': {'notification_id': notification.id, 'payload': payload}
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Local provider failed: {str(e)}'
            }
