from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class Vote(Base):
    """投票模型 - 用户对历史事件进行赞踩投票"""

    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("event_id", "session_id", name="uq_event_session_vote"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    event_id = Column(String(128), nullable=False, index=True, comment="历史事件ID")
    event_name = Column(String(256), nullable=False, comment="历史事件名称")
    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")

    vote_type = Column(Integer, nullable=False, comment="投票类型: 1=点赞, -1=踩")

    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Vote(id={self.id}, event={self.event_name}, type={self.vote_type})>"
