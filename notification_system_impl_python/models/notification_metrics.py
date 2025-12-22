from configs.db import db
from helpers.helpers import now_ms
import uuid
from datetime import date
from sqlalchemy import Index
from helpers.enums import MessageType
from enum import Enum


class NotificationMetrics(db.Model):
    __tablename__ = "notification_metrics"
    __table_args__ = (
        Index("idx_metrics_date", "date", "hour"),
        Index("idx_metrics_provider", "provider"),
        Index("idx_metrics_type", "message_type"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.Date, nullable=False, default=date.today)
    hour = db.Column(db.Integer)
    provider = db.Column(db.String(20), nullable=False)
    message_type = db.Column(
        db.Enum(
            MessageType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    total_sent = db.Column(db.Integer, nullable=False, default=0)
    total_failed = db.Column(db.Integer, nullable=False, default=0)
    total_pending = db.Column(db.Integer, nullable=False, default=0)
    avg_delivery_ms = db.Column(db.BigInteger)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    def __repr__(self):
        return f"<NotificationMetrics id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
