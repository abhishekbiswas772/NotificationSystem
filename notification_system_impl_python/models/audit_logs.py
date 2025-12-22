from configs.db import db
from helpers.helpers import now_ms
import uuid
from helpers.enums import ResourceType, ActionType
from sqlalchemy import Index
from enum import Enum


class AuditLogs(db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_created", "created_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    user = db.relationship("Users", back_populates="audit_logs", passive_deletes=True)
    action = db.Column(
        db.Enum(
            ActionType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    resource_type = db.Column(
        db.Enum(
            ResourceType,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    resource_id = db.Column(db.String(36))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    changes = db.Column(db.Text)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    def __repr__(self):
        return f"<AuditLogs id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
