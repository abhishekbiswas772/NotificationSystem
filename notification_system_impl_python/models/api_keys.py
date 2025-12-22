from configs.db import db
from helpers.helpers import now_ms
import uuid
from sqlalchemy import Index
from enum import Enum


class APIKeys(db.Model):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_api_key_user", "user_id"),
        Index("idx_api_key_active", "isActive"),
    )

    id = db.Column(db.String(36), nullable=False, primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    scopes = db.Column(db.Text)
    isActive = db.Column(db.Boolean, nullable=False, default=True)
    expireAt = db.Column(db.BigInteger)
    lastUsedAt = db.Column(db.BigInteger)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = db.relationship("Users", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKeys id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
