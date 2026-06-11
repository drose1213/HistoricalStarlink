from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func

from ..database import Base


class UserExplorationProfile(Base):
    """用户探索画像模型 - 一次对话结束时写一条, 4 维画像 + 路径签名 + 结局类型"""

    __tablename__ = "user_exploration_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")
    event_id = Column(String(128), nullable=False, index=True, comment="事件ID")
    ending_type = Column(String(32), nullable=False, comment="结局类型: historical/altered/rag_fallback/rag_dynamic")

    # 4 维画像
    reform_score = Column(Integer, default=0, comment="改革倾向 0-100")
    conservative_score = Column(Integer, default=0, comment="保守倾向 0-100")
    empathy_score = Column(Integer, default=0, comment="共情倾向 0-100")
    radicalism_score = Column(Integer, default=0, comment="激进倾向 0-100")

    choices_signature = Column(String(64), nullable=True, index=True, comment="路径签名 A/D/T/N")
    choices_made = Column(JSON, nullable=True, comment="完整选择序列")

    is_deleted = Column(Boolean, default=False, comment="软删标记")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<UserExplorationProfile(id={self.id}, event={self.event_id}, ending={self.ending_type})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_id": self.event_id,
            "ending_type": self.ending_type,
            "reform_score": self.reform_score or 0,
            "conservative_score": self.conservative_score or 0,
            "empathy_score": self.empathy_score or 0,
            "radicalism_score": self.radicalism_score or 0,
            "choices_signature": self.choices_signature,
            "choices_made": self.choices_made or [],
            "is_deleted": bool(self.is_deleted),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
