from abc import ABC, abstractmethod
from typing import Dict, Any


class NotificationProvider(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def send(self, notification) -> Dict[str, Any]:
        pass
