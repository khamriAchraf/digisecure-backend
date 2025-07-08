from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(
        String, unique=True, index=True, nullable=False
    )  # JWT ID (jti claim)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False)  # Hashed version of the token
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used_at = Column(DateTime, nullable=True)  # When the token was last used
    ip_address = Column(String, nullable=True)  # IP address when token was created
    user_agent = Column(String, nullable=True)  # User agent when token was created

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")
