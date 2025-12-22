import uuid
import json
from datetime import timedelta, datetime, timezone
from configs.db import db
from helpers.custom_exceptions import DLQHandlerException
from helpers.helpers import now_ms
from helpers.enums import NotificationStatus
from models.notification import Notification
from models.notification_dlq import NotificationDLQ


class DLQHandler:
    def __init__(self):
        self.db = db
        if not self.db:
            raise DLQHandlerException("database not initialized")

    def move_to_dlq(self, notification_id: str, reason: str, error_details: str) -> None:
        if not notification_id:
            raise DLQHandlerException("notification id is required")
        session = self.db.session
        try:
            notification = Notification.query.filter_by(id=notification_id).first()
            if not notification:
                raise DLQHandlerException("notification not found")

            retry_history = {
                "total_attempts": notification.attempt_count,
                "last_error": error_details,
                "last_attempted": notification.last_attempted,
                "failure_reason": reason,
            }

            dlq_entry = NotificationDLQ(
                id=str(uuid.uuid4()),
                notification_id=notification_id,
                failure_reason=reason,
                retry_history=json.dumps(retry_history),
                resolved=False,
            )

            session.add(dlq_entry)
            notification.status = NotificationStatus.FAILED
            notification.failed_at = now_ms()
            session.commit()
        except Exception as e:
            session.rollback()
            raise DLQHandlerException(str(e))

    def retry_from_dlq(self, dlq_id: str) -> None:
        if not dlq_id:
            raise DLQHandlerException("dlq id is required")
        session = self.db.session
        try:
            dlq_entry = NotificationDLQ.query.filter_by(id=dlq_id).first()
            if not dlq_entry:
                raise DLQHandlerException("DLQ entry not found")
            if dlq_entry.resolved:
                raise DLQHandlerException("DLQ entry already resolved")

            notification = Notification.query.filter_by(id=dlq_entry.notification_id).first()
            if not notification:
                raise DLQHandlerException("notification not found")

            notification.status = NotificationStatus.PENDING
            notification.attempt_count = 0
            notification.failed_at = None
            notification.error_message = None
            notification.send_at = now_ms()
            session.commit()
        except Exception as e:
            session.rollback()
            raise DLQHandlerException(str(e))

    def resolve_dlq_entry(self, dlq_id: str, resolved_by: str | None = None) -> None:
        if not dlq_id:
            raise DLQHandlerException("dlq id is required")
        session = self.db.session
        try:
            dlq_entry = NotificationDLQ.query.filter_by(id=dlq_id).first()
            if not dlq_entry:
                raise DLQHandlerException("DLQ entry not found")

            dlq_entry.resolved = True
            dlq_entry.resolved_at = now_ms()
            if resolved_by:
                dlq_entry.resolved_by = resolved_by
            session.commit()
        except Exception as e:
            session.rollback()
            raise DLQHandlerException(str(e))

    def list_dlq_entries(self, resolved: bool | None = None, limit: int = 20, offset: int = 0):
        query = NotificationDLQ.query
        if resolved is not None:
            query = query.filter(NotificationDLQ.resolved == resolved)

        safe_limit = 20 if limit <= 0 or limit > 100 else limit
        safe_offset = 0 if offset < 0 else offset

        return (
            query.order_by(NotificationDLQ.moved_to_dlq_at.desc())
            .limit(safe_limit)
            .offset(safe_offset)
            .all()
        )

    def cleanup_old_dlq_entries(self, days_old: int) -> int:
        cutoff_ms = int((datetime.now(timezone.utc) - timedelta(days=days_old)).timestamp() * 1000)
        result = (
            NotificationDLQ.query
            .filter(NotificationDLQ.resolved.is_(True))
            .filter(NotificationDLQ.resolved_at < cutoff_ms)
            .delete()
        )
        self.db.session.commit()
        return result

    def get_dlq_stats(self) -> dict:
        total = NotificationDLQ.query.count()
        unresolved = NotificationDLQ.query.filter_by(resolved=False).count()
        return {
            "total_entries": total,
            "unresolved_entries": unresolved,
            "resolved_entries": total - unresolved,
        }
