from configs.db import db
from helpers.helpers import now_ms
import uuid
from sqlalchemy import Index
from helpers.enums import MessageType, ProviderType, NotificationStatus
from enum import Enum


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_user_type", "user_id", "message_type"),
        Index("idx_user_status", "user_id", "status"),
        Index("idx_status_created", "status", "created_at"),
        Index("idx_send_at", "send_at"),
        Index("idx_idempotency", "idempotency_key", unique=True),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = db.relationship("Users", back_populates="notifications")
    idempotency_key = db.Column(db.String(64), nullable=False)
    message_type = db.Column(
        db.Enum(
            MessageType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    provider = db.Column(
        db.Enum(
            ProviderType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    status = db.Column(
        db.Enum(
            NotificationStatus,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=NotificationStatus.PENDING,
    )
    payload = db.Column(db.Text, nullable=False)
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    max_retries = db.Column(db.Integer, nullable=False, default=5)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)
    last_attempted = db.Column(db.BigInteger)
    send_at = db.Column(db.BigInteger)
    failed_at = db.Column(db.BigInteger)
    sent_at = db.Column(db.BigInteger)
    error_message = db.Column(db.Text)
    provider_response = db.Column(db.Text)

    dlq = db.relationship("NotificationDLQ", back_populates="notification", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    webhook_deliveries = db.relationship("WebhookDelivery", back_populates="notification", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<Notification id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
