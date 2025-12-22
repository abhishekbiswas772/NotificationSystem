from providers.base_provider import NotificationProvider
from providers.provider_factory import get_provider_map
from helpers.enums import ProviderType
from typing import Dict


class NotificationHandler:
    def __init__(self):
        self.providers: Dict[ProviderType, NotificationProvider] = {}
        self._load_providers()

    def _load_providers(self):
        try:
            self.providers = get_provider_map()
            print(f"Loaded {len(self.providers)} notification providers")
        except Exception as e:
            print(f"Failed to load providers: {str(e)}")
            raise

    def get_provider(self, provider_type: ProviderType) -> NotificationProvider:
        return self.providers.get(provider_type)

    def send_notification(self, notification):
        provider = self.get_provider(notification.provider)

        if not provider:
            print(f"No provider found for {notification.provider}")
            return {
                'success': False,
                'message': f'No provider configured for {notification.provider.value}'
            }

        return provider.send(notification)
