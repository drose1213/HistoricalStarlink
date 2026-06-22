from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class ReviewLike(Base):
    """评价点赞模型 - 用户对卡牌评价的点赞记录"""

    __tablename__ = "review_likes"
    __table_args__ = (
        UniqueConstraint("review_id", "user_session_id", name="uq_review_user_like"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    review_id = Column(Integer, nullable=False, index=True, comment="评价ID")
    user_session_id = Column(String(64), nullable=False, index=True, comment="点赞者会话ID")

    is_deleted = Column(Boolean, default=False, comment="是否删除（软删：取消点赞）")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ReviewLike(id={self.id}, review_id={self.review_id}, user={self.user_session_id})>"
