from configs.db import db
import uuid
from helpers.helpers import now_ms
from sqlalchemy import Index
from enum import Enum


class NotificationWebhook(db.Model):
    __tablename__ = "notification_webhooks"
    __table_args__ = (
        Index("idx_webhook_user", "user_id"),
        Index("idx_webhook_active", "is_active"),
    )

    id = db.Column(db.String(36), nullable=False, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = db.relationship("Users", back_populates="webhooks")
    url = db.Column(db.String(500), nullable=False)
    secret_key = db.Column(db.String(64), nullable=False)
    events = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    retry_count = db.Column(db.Integer, nullable=False, default=3)
    timeout_seconds = db.Column(db.Integer, nullable=False, default=10)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    deliveries = db.relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<NotificationWebhook id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
