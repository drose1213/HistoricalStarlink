from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func

from ..database import Base


class DialogueSession(Base):

    __tablename__ = "dialogue_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    event_id = Column(String(128), nullable=False, index=True)
    event_name = Column(String(256), nullable=False, comment="")
    npc_name = Column(String(128), nullable=True, comment="")
    dialogue_history = Column(JSON, nullable=True, comment="")
    choices_made = Column(JSON, nullable=True, comment="")
    timeline_branches = Column(JSON, nullable=True, comment="")
    current_round = Column(Integer, default=1, comment="")
    path_depth = Column(Integer, default=0, comment="")
    is_completed = Column(Boolean, default=False, comment="")
    outcome_summary = Column(Text, nullable=True, comment="")
    is_dynamic = Column(Boolean, default=False, comment="True 表示由任意话题动态生成的对话")
    topic = Column(String(256), nullable=True, comment="dynamic 对话的用户原始 topic (替代 event_name 字符串解析)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<DialogueSession(id={self.id}, event={self.event_name}, npc={self.npc_name})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_id": self.event_id,
            "event_name": self.event_name,
            "npc_name": self.npc_name,
            "dialogue_history": self.dialogue_history or [],
            "choices_made": self.choices_made or [],
            "timeline_branches": self.timeline_branches or [],
            "current_round": self.current_round or 1,
            "path_depth": self.path_depth or 0,
            "is_completed": bool(self.is_completed),
            "is_dynamic": bool(self.is_dynamic),
            "topic": self.topic,
            "outcome_summary": self.outcome_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
