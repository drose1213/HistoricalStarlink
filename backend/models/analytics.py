from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from ..database import Base


class AnalyticsEvent(Base):
    """埋点事件模型 - 记录前端用户行为事件"""

    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    event_name = Column(String(50), nullable=False, index=True, comment="事件名")
    user_agent = Column(String(500), nullable=True, comment="用户浏览器标识")
    topic = Column(String(200), nullable=True, index=True, comment="关联话题/事件")
    payload = Column(JSON, default=dict, comment="事件附加数据")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, event={self.event_name}, topic={self.topic})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_name": self.event_name,
            "user_agent": self.user_agent,
            "topic": self.topic,
            "payload": self.payload or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
