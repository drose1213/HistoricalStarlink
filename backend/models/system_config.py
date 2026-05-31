from sqlalchemy import Column, String, Text
from ..database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String(100), primary_key=True, comment="配置键")
    value = Column(Text, nullable=True, comment="配置值")
    group = Column(String(50), nullable=False, default="general", comment="配置分组")
    label = Column(String(200), nullable=True, comment="中文说明")
    value_type = Column(String(20), nullable=False, default="string", comment="值类型: string/int/bool/json")
