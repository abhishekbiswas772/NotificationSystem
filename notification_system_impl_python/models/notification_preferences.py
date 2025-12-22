from configs.db import db
from helpers.helpers import now_ms
import uuid
from helpers.enums import MessageType
from sqlalchemy import Index
from enum import Enum


class NotificationPreferences(db.Model):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        Index("idx_user_channel", "user_id", "channel"),
        Index("idx_preference_enabled", "enabled"),
    )

    id = db.Column(db.String(36), nullable=False, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = db.relationship("Users", back_populates="preferences")
    channel = db.Column(
        db.Enum(
            MessageType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    frequency_cap = db.Column(db.Integer)
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)
    timezone = db.Column(db.String(50), nullable=False, default="UTC")
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    def __repr__(self):
        return f"<NotificationPreferences id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
