from configs.db import db
from helpers.helpers import now_ms
import uuid
from sqlalchemy import Index
from enum import Enum


class WebhookDelivery(db.Model):
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("idx_webhook_delivery", "webhook_id", "notification_id"),
        Index("idx_delivery_status", "delivered"),
        Index("idx_next_retry", "next_retry_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = db.Column(db.String(36), db.ForeignKey("notification_webhooks.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    notification_id = db.Column(db.String(36), db.ForeignKey("notifications.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    webhook = db.relationship("NotificationWebhook", back_populates="deliveries")
    notification = db.relationship("Notification", back_populates="webhook_deliveries")
    event_type = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    attempt_count = db.Column(db.Integer, nullable=False, default=1)
    delivered = db.Column(db.Boolean, nullable=False, default=False)
    delivered_at = db.Column(db.BigInteger)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)
    next_retry_at = db.Column(db.BigInteger)

    def __repr__(self):
        return f"<WebhookDelivery id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
