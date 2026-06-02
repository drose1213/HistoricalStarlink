from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(50), default="")
    avatar_url = Column(String(500), default="")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False, nullable=False,
                      comment="是否为管理员, 决定知识库管理页访问权限")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
