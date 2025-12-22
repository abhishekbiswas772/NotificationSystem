from configs.db import db
from helpers.helpers import now_ms
import uuid
from sqlalchemy import Index
from enum import Enum


class NotificationDLQ(db.Model):
    __tablename__ = "notification_dlq"
    __table_args__ = (
        Index("idx_notification_dlq", "notification_id", unique=True),
        Index("idx_moved_at", "moved_to_dlq_at"),
        Index("idx_resolved", "resolved"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = db.Column(db.String(36), db.ForeignKey("notifications.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    failure_reason = db.Column(db.Text, nullable=False)
    retry_history = db.Column(db.Text)
    moved_to_dlq_at = db.Column(db.BigInteger, nullable=False, default=now_ms)
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    resolved_at = db.Column(db.BigInteger)
    resolved_by = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"))

    notification = db.relationship("Notification", back_populates="dlq")
    resolver = db.relationship("Users", back_populates="resolved_dlq")

    def __repr__(self):
        return f"<NotificationDLQ id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
