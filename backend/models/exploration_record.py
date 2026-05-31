from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.sql import func

from ..database import Base


class ExplorationRecord(Base):
    """探索记录模型 - 记录用户的星链探索路径"""

    __tablename__ = "exploration_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")
    event_id = Column(String(128), nullable=False, index=True, comment="历史事件ID")
    event_name = Column(String(256), nullable=False, comment="历史事件名称")
    event_year = Column(Integer, nullable=True, comment="事件年份")
    event_region = Column(String(32), nullable=True, comment="事件区域: china/foreign")

    parent_event_id = Column(String(128), nullable=True, comment="上级事件ID（探索来源）")
    depth = Column(Integer, default=0, comment="探索深度")
    explore_path = Column(JSON, nullable=True, comment="完整探索路径JSON")

    stay_duration = Column(Float, default=0.0, comment="停留时长（秒）")
    from_direction = Column(String(16), nullable=True, comment="来源方向: causes/consequences/initial")

    user_agent = Column(String(512), nullable=True, comment="用户浏览器标识")
    ip_address = Column(String(64), nullable=True, comment="用户IP地址")

    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ExplorationRecord(id={self.id}, event={self.event_name}, session={self.session_id})>"
