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
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<DialogueSession(id={self.id}, event={self.event_name}, npc={self.npc_name})>"
