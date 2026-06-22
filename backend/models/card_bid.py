from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Index
from sqlalchemy.sql import func

from ..database import Base


class CardBid(Base):
    """卡牌拍卖出价模型 - 用户对拍卖的出价记录"""

    __tablename__ = "card_bids"
    __table_args__ = (
        Index("ix_card_bids_auction_created", "auction_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    auction_id = Column(Integer, nullable=False, index=True, comment="关联的拍卖ID")
    bidder_session_id = Column(String(64), nullable=False, index=True, comment="出价者会话ID")

    amount = Column(Float, nullable=False, comment="出价金额")
    is_winning = Column(Boolean, default=False, comment="是否当前领先")

    created_at = Column(DateTime, server_default=func.now(), comment="出价时间")

    def __repr__(self):
        return f"<CardBid(id={self.id}, auction_id={self.auction_id}, amount={self.amount}, winning={self.is_winning})>"