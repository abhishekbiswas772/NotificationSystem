from configs.db import db
from helpers.helpers import now_ms
import uuid
from sqlalchemy import Index
from enum import Enum


class RateLimit(db.Model):
    __tablename__ = "rate_limits"
    __table_args__ = (
        Index("idx_rate_limit_user_window", "user_id", "window_start", "limit_type", unique=True),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = db.relationship("Users", back_populates="rate_limits")
    window_start = db.Column(db.BigInteger, nullable=False)
    request_count = db.Column(db.Integer, nullable=False, default=0)
    limit_type = db.Column(db.String(20), nullable=False)
    createdAt = db.Column("created_at", db.BigInteger, nullable=False, default=now_ms)
    updatedAt = db.Column("updated_at", db.BigInteger, nullable=False, default=now_ms, onupdate=now_ms)

    def __repr__(self):
        return f"<RateLimit id={self.id}>"

    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                value = value.value
            data[column.name] = value
        return data
