from configs.db import db
from helpers.helpers import now_ms
import uuid
from sqlalchemy import Index
from enum import Enum


class ProviderConfig(db.Model):
    __tablename__ = "provider_configs"
    __table_args__ = (
        Index("idx_provider_name", "provider_name", unique=True),
        Index("idx_provider_active", "is_active"),
        Index("idx_provider_priority", "priority"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_name = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    api_secret = db.Column(db.String(255))
    config_json = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    rate_limit = db.Column(db.Integer)
    timeout_seconds = db.Column(db.Integer, nullable=False, default=30)
    priority = db.Column(db.Integer, nullable=False, default=0)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    def __repr__(self):
        return f"<ProviderConfig id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
