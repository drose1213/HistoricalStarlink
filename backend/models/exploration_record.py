from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.sql import func

from ..database import Base


class ExplorationRecord(Base):
    """User exploration history for event/detail/dialogue flows."""

    __tablename__ = "exploration_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Primary key")

    session_id = Column(String(64), nullable=False, index=True, comment="Session ID")
    event_id = Column(String(128), nullable=False, index=True, comment="Historical event ID")
    event_name = Column(String(256), nullable=False, comment="Historical event name")
    event_year = Column(Integer, nullable=True, comment="Event year")
    event_region = Column(String(32), nullable=True, comment="Event region: china/foreign")

    parent_event_id = Column(String(128), nullable=True, comment="Parent event ID")
    depth = Column(Integer, default=0, comment="Exploration depth")
    explore_path = Column(JSON, nullable=True, comment="Structured exploration path")

    stay_duration = Column(Float, default=0.0, comment="Stay duration in seconds")
    notes = Column(Text, nullable=True, comment="Exploration notes and completion summary")
    from_direction = Column(String(16), nullable=True, comment="Source direction")

    user_agent = Column(String(512), nullable=True, comment="Browser user agent")
    ip_address = Column(String(64), nullable=True, comment="Client IP address")

    is_deleted = Column(Boolean, default=False, comment="Soft delete flag")
    created_at = Column(DateTime, server_default=func.now(), comment="Created time")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Updated time")

    def __repr__(self):
        return f"<ExplorationRecord(id={self.id}, event={self.event_name}, session={self.session_id})>"