from enum import Enum


class MessageType(Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"

class ProviderType(Enum):
    GMAIL = "GMAIL"
    OUTLOOK = "OUTLOOK"
    CUSTOM_SMTP = "CUSTOM_SMTP"
    TEXTBELT = "TEXTBELT"
    CONSOLE_SMS = "CONSOLE_SMS"
    FCM = "FCM"
    LOCAL = "LOCAL"

class NotificationStatus(Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ResourceType(Enum):
    ResourceNotification = "notification"
    ResourceUser = "user"
    ResourceWebhook = "webhook"


class ActionType(Enum):
    ActionCreate = "create"
    ActionUpdate = "update"
    ActionDelete = "delete"
