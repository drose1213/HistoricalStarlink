from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class Rating(Base):
    """评分模型 - 用户对历史事件的评分"""

    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("event_id", "session_id", name="uq_event_session_rating"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    event_id = Column(String(128), nullable=False, index=True, comment="历史事件ID")
    event_name = Column(String(256), nullable=False, comment="历史事件名称")
    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")

    score = Column(Float, nullable=False, comment="评分 1.0-10.0")
    comment = Column(Text, nullable=True, comment="评分备注")

    dimension_importance = Column(Float, nullable=True, comment="重要性维度评分")
    dimension_interest = Column(Float, nullable=True, comment="趣味性维度评分")
    dimension_impact = Column(Float, nullable=True, comment="影响力维度评分")

    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Rating(id={self.id}, event={self.event_name}, score={self.score})>"
