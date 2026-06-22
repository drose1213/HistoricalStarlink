from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class UserCardCollection(Base):
    """用户卡牌收藏模型 - 记录用户从探索/拍卖等渠道收藏的卡牌"""

    __tablename__ = "user_card_collections"
    __table_args__ = (
        UniqueConstraint("user_session_id", "card_id", name="uq_user_card"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    user_session_id = Column(String(64), nullable=False, index=True, comment="用户会话ID")
    card_id = Column(Integer, ForeignKey("champion_cards.id"), nullable=False, comment="关联的冠军卡牌ID")

    event_id = Column(String(128), nullable=False, index=True, comment="历史事件ID")
    event_name = Column(String(256), nullable=False, comment="历史事件名称")

    is_high_rated = Column(Boolean, default=False, comment="是否高分卡牌（评分>=8.0）")
    source = Column(String(16), nullable=False, default="explore", comment="来源: explore/auction/system")

    collected_at = Column(DateTime, server_default=func.now(), comment="收藏时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")

    def __repr__(self):
        return f"<UserCardCollection(id={self.id}, user={self.user_session_id}, card={self.card_id}, source={self.source})>"