from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.sql import func

from ..database import Base


class ChampionCard(Base):
    """冠军卡片模型 - 用户探索成就与历史卡片收集"""

    __tablename__ = "champion_cards"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")
    nickname = Column(String(64), nullable=True, comment="用户昵称")

    event_id = Column(String(128), nullable=False, index=True, comment="历史事件ID")
    event_name = Column(String(256), nullable=False, comment="历史事件名称")
    event_year = Column(Integer, nullable=True, comment="事件年份")
    event_region = Column(String(32), nullable=True, comment="事件区域")
    event_description = Column(Text, nullable=True, comment="事件描述")

    card_level = Column(Integer, default=1, comment="卡片等级: 1=普通, 2=稀有, 3=史诗, 4=传说")
    explore_count = Column(Integer, default=1, comment="该事件累计探索次数")
    total_stay_duration = Column(Float, default=0.0, comment="该事件累计停留时长（秒）")

    related_events = Column(JSON, nullable=True, comment="关联事件数据快照JSON")
    achievements = Column(JSON, nullable=True, comment="已解锁成就列表JSON")

    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 卡牌拍卖与收藏扩展字段
    owner_session_id = Column(String(64), nullable=True, index=True, comment="当前持有人会话ID")
    is_on_auction = Column(Boolean, default=False, index=True, comment="是否正在拍卖中")
    is_high_rated = Column(Boolean, default=False, index=True, comment="是否高分卡牌(评分>=8.0)")

    def __repr__(self):
        return f"<ChampionCard(id={self.id}, event={self.event_name}, level={self.card_level})>"
