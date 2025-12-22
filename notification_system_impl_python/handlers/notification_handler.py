from configs.db import db
from configs.redis import get_redis_pool
from helpers.custom_exceptions import NotificationHandlerException
from helpers.enums import MessageType, ProviderType, NotificationStatus
from helpers.helpers import now_ms
from models.notification import Notification
from typing import List, Optional
import uuid
import json
from enum import Enum


class NotificationHandler:
    def __init__(self):
        self.db = db
        self.redis_client = get_redis_pool()
        if not self.db:
            raise NotificationHandlerException("cannot connect to database")
        if not self.redis_client:
            raise NotificationHandlerException("redis client is cannot be connected")
        

    def _reserve_idempotency(self, key: str, ttl_seconds: int = 86400) -> bool:
        return self.redis_client.set(name=f"notification:idemp:{key}", value="1", nx=True, ex=ttl_seconds)

    def create_notification(
        self,
        user_id: str,
        message_type: MessageType,
        provider: ProviderType,
        payload: str,
        idempotency_key: Optional[str] = None,
        send_at: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> Notification:
        if not user_id or not payload:
            raise NotificationHandlerException("user_id, payload, message_type, and provider are required")

        # Accept raw strings for enums and normalize
        if isinstance(message_type, str):
            try:
                message_type = MessageType(message_type.upper())
            except Exception:
                raise NotificationHandlerException("invalid message_type")
        if isinstance(provider, str):
            try:
                provider = ProviderType(provider.upper())
            except Exception:
                raise NotificationHandlerException("invalid provider")

        if not isinstance(message_type, Enum) or not isinstance(provider, Enum):
            raise NotificationHandlerException("message_type and provider are required")

        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            message_type=message_type,
            provider=provider,
            status=NotificationStatus.PENDING,
            payload=payload,
            max_retries=max_retries if max_retries is not None else 5,
            attempt_count=0,
            send_at=send_at,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

        if self.redis_client:
            reserved = self._reserve_idempotency(notif.idempotency_key)
            if not reserved:
                raise NotificationHandlerException("duplicate notification (idempotency)")

        try:
            self.db.session.add(notif)
            self.db.session.commit()
            return notif
        except Exception as e:
            self.db.session.rollback()
            raise NotificationHandlerException(str(e))

    def bulk_create(self, notifications: List[dict]) -> List[Notification]:
        created = []
        for payload in notifications:
            created.append(
                self.create_notification(
                    user_id=payload.get("user_id"),
                    message_type=payload.get("message_type"),
                    provider=payload.get("provider"),
                    payload=payload.get("payload"),
                    idempotency_key=payload.get("idempotency_key"),
                    send_at=payload.get("send_at"),
                    max_retries=payload.get("max_retries"),
                )
            )
        return created

    def get_notification(self, notification_id: str) -> Notification:
        notif = Notification.query.filter_by(id=notification_id).first()
        if not notif:
            raise NotificationHandlerException("notification not found")
        return notif

    def list_notifications(
        self,
        user_id: Optional[str] = None,
        status: Optional[NotificationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Notification]:
        query = Notification.query
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        if status:
            query = query.filter(Notification.status == status)

        safe_limit = 20 if limit <= 0 or limit > 100 else limit
        safe_offset = 0 if offset < 0 else offset
        return (
            query.order_by(Notification.createdAt.desc())
            .limit(safe_limit)
            .offset(safe_offset)
            .all()
        )

    def cancel_notification(self, notification_id: str):
        notif = Notification.query.with_for_update().filter_by(id=notification_id).first()
        if not notif:
            raise NotificationHandlerException("notification not found")
        if notif.status != NotificationStatus.PENDING:
            raise NotificationHandlerException("only pending notifications can be cancelled")

        notif.status = NotificationStatus.CANCELLED
        notif.failed_at = now_ms()
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            raise NotificationHandlerException(str(e))

    def enqueue_for_send(self, notification_id: str):
        notif = self.get_notification(notification_id)
        if self.redis_client:
            payload = json.dumps({"id": notif.id, "action": "send"})
            self.redis_client.lpush("notification:queue", payload)
        return notif
