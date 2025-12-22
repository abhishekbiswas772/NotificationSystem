from configs.db import db
from helpers.helpers import now_ms
import uuid
from enum import Enum

class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    username = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms, index=True)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    api_keys = db.relationship("APIKeys", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    audit_logs = db.relationship("AuditLogs", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    preferences = db.relationship("NotificationPreferences", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    templates = db.relationship("NotificationTemplate", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True)
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    webhooks = db.relationship("NotificationWebhook", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    rate_limits = db.relationship("RateLimit", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    resolved_dlq = db.relationship("NotificationDLQ", back_populates="resolver", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<Users id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            if column.name == "password":
                continue
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
