from sqlalchemy import Column, Integer, String, Text, Float, Boolean, JSON
from ..database import Base


class HistoryEvent(Base):
    __tablename__ = "history_events"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    region = Column(String(20), nullable=False, comment="china 或 foreign")
    importance = Column(Integer, nullable=False, comment="1-10")
    description = Column(Text, nullable=False)
    causes = Column(JSON, nullable=False, default=list)
    consequences = Column(JSON, nullable=False, default=list)
    related_concepts = Column(JSON, nullable=False, default=list)
    figures = Column(JSON, nullable=False, default=list)
    tags = Column(JSON, nullable=False, default=list)
