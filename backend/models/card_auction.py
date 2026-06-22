from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.sql import func

from ..database import Base


class CardAuction(Base):
    """卡牌拍卖模型 - 用户上架冠军卡牌进行拍卖"""

    __tablename__ = "card_auctions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    card_id = Column(Integer, nullable=False, comment="关联的冠军卡牌ID")
    event_id = Column(String(128), nullable=False, index=True, comment="历史事件ID")
    event_name = Column(String(256), nullable=False, comment="历史事件名称")

    seller_session_id = Column(String(64), nullable=False, index=True, comment="卖家会话ID")

    start_price = Column(Float, nullable=False, comment="起拍价")
    current_price = Column(Float, nullable=False, comment="当前价")
    min_increment = Column(Float, default=5.0, comment="最小加价幅度")

    end_time = Column(DateTime, nullable=False, comment="拍卖结束时间")

    status = Column(String(16), nullable=False, default="active", comment="状态: active/sold/expired/cancelled")

    sold_price = Column(Float, nullable=True, comment="成交价")
    platform_fee = Column(Float, nullable=True, comment="平台手续费")
    seller_revenue = Column(Float, nullable=True, comment="卖家实际收入")
    winner_session_id = Column(String(64), nullable=True, comment="获胜买家会话ID")

    description = Column(Text, nullable=True, comment="拍卖描述")

    bid_count = Column(Integer, default=0, comment="出价次数")

    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<CardAuction(id={self.id}, card_id={self.card_id}, status={self.status}, current_price={self.current_price})>"