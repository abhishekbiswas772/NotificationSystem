from configs.db import db
from helpers.helpers import now_ms
import uuid
from sqlalchemy import Index
from helpers.enums import MessageType
from enum import Enum


class NotificationTemplate(db.Model):
    __tablename__ = "notification_templates"
    __table_args__ = (
        Index("idx_template_name", "name", unique=True),
        Index("idx_template_type", "message_type"),
        Index("idx_template_active", "is_active"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    message_type = db.Column(
        db.Enum(
            MessageType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    subject = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"))
    creator = db.relationship("Users", back_populates="templates", passive_deletes=True)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    def __repr__(self):
        return f"<NotificationTemplate id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
