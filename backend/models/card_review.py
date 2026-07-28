from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class CardReview(Base):
    """卡牌拍卖评价模型 - 买家对成交拍卖的评价"""

    __tablename__ = "card_reviews"
    __table_args__ = (
        UniqueConstraint("auction_id", "reviewer_session_id", name="uq_auction_reviewer"),
        UniqueConstraint("card_id", "reviewer_session_id", name="uq_card_reviewer"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    auction_id = Column(Integer, nullable=True, index=True, comment="关联的拍卖ID（拍卖评价时使用）")
    card_id = Column(Integer, nullable=True, index=True, comment="关联的卡牌ID（卡牌评价时使用）")
    reviewer_session_id = Column(String(64), nullable=False, index=True, comment="评价者会话ID")
    user_id = Column(Integer, nullable=True, index=True, comment="登录用户ID(登录态下记录归集到账号)")

    stars = Column(Integer, nullable=False, comment="星级 1-5")
    comment = Column(String(500), nullable=True, comment="评价内容")

    # 扩展：点赞/回复支持（spec rating-system-enhancement）
    parent_review_id = Column(Integer, nullable=True, index=True, comment="回复的父评价ID，NULL 表示顶级评价")
    likes_count = Column(Integer, nullable=False, default=0, comment="点赞数（冗余存储）")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<CardReview(id={self.id}, auction_id={self.auction_id}, stars={self.stars})>"