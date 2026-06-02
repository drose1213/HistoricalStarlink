from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, LargeBinary, Float, DateTime,
    Index, ForeignKey
)
from ..database import Base


class EventEmbedding(Base):
    """知识条目 embedding 向量持久化表 — 解决冷启动重算问题"""

    __tablename__ = "event_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    knowledge_entry_id = Column(
        Integer, ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
        comment="关联知识条目ID（一对一）",
    )
    model_name = Column(String(64), nullable=False, default="embo-01",
                        comment="embedding模型标识, 用于模型升级时强制重算")
    dim = Column(Integer, nullable=False, comment="向量维度, 用于校验")
    vector_blob = Column(LargeBinary(length=8192), nullable=False,
                         comment="float32向量二进制(numpy.tobytes)")
    vector_norm = Column(Float, nullable=False, default=1.0,
                         comment="L2范数, 避免重复计算")
    content_hash = Column(String(64), nullable=False,
                          comment="对应条目内容哈希, 内容变更触发重算")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                        nullable=False)

    __table_args__ = (
        Index("ix_emb_model", "model_name"),
    )

    def __repr__(self):
        return f"<EventEmbedding(id={self.id}, entry_id={self.knowledge_entry_id}, model={self.model_name})>"
