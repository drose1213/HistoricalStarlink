from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func

from ..database import Base


class Signature(Base):
    """签名模型 - 用户上传的签名图片"""

    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")
    nickname = Column(String(64), nullable=True, comment="用户昵称")

    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    file_name = Column(String(256), nullable=False, comment="原始文件名")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_type = Column(String(32), nullable=False, comment="文件MIME类型")
    file_url = Column(String(1024), nullable=False, comment="文件访问URL")

    width = Column(Integer, nullable=True, comment="图片宽度")
    height = Column(Integer, nullable=True, comment="图片高度")

    event_id = Column(String(128), nullable=True, index=True, comment="关联的历史事件ID")
    context = Column(Text, nullable=True, comment="签名附带的文字内容")

    is_approved = Column(Boolean, default=True, comment="是否审核通过")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Signature(id={self.id}, file={self.file_name}, session={self.session_id})>"
