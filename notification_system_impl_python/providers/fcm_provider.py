import json
import os
from typing import Dict, Any, Optional
from providers.base_provider import NotificationProvider
import requests
from dotenv import load_dotenv

load_dotenv()


class FCMProvider(NotificationProvider):
    def __init__(self, server_key: str):
        self.server_key = server_key
        self.api_url = "https://fcm.googleapis.com/fcm/send"

    def provider_name(self) -> str:
        return "fcm"

    def send(self, notification) -> Dict[str, Any]:
        try:
            payload = json.loads(notification.payload)
            token = payload.get('token')
            topic = payload.get('topic')

            if not token and not topic:
                return {'success': False, 'message': 'Missing "token" or "topic" field in payload'}
            fcm_message = {
                'notification': {
                    'title': payload.get('title', 'Notification'),
                    'body': payload.get('body', '')
                }
            }
            if 'data' in payload:
                fcm_message['data'] = payload['data']

            if token:
                fcm_message['to'] = token
            else:
                fcm_message['to'] = f'/topics/{topic}'

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'key={self.server_key}'
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=fcm_message,
                timeout=10
            )
            if response.status_code >= 400:
                return {
                    'success': False,
                    'message': f'FCM returned error status {response.status_code}: {response.text}'
                }

            result = response.json()
            success_count = result.get('success', 0)
            failure_count = result.get('failure', 0)

            if success_count > 0:
                return {
                    'success': True,
                    'message': 'Push notification sent via FCM',
                    'response': result
                }
            error_msg = 'Unknown error'
            if failure_count > 0 and 'results' in result:
                results = result['results']
                if results and 'error' in results[0]:
                    error_msg = results[0]['error']

            return {
                'success': False,
                'message': f'FCM error: {error_msg}',
                'response': result
            }

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'FCM request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'FCM send failed: {str(e)}'
            }


def load_fcm_provider_from_env() -> Optional[FCMProvider]:
    server_key = os.getenv("FCM_SERVER_KEY")
    if server_key:
        return FCMProvider(server_key)
    return None
