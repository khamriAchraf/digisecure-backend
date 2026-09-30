from sqlalchemy import (Boolean, Column, Date, ForeignKey, Integer, String,
                        Table, Text, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.db.base import Base

# Association table for compliance events and users (many-to-many)
compliance_event_notify_users = Table(
    "compliance_event_notify_users",
    Base.metadata,
    Column(
        "compliance_event_id",
        Integer,
        ForeignKey("compliance_events.id"),
        primary_key=True,
    ),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)

# Association table for compliance events and groups (many-to-many)
compliance_event_notify_groups = Table(
    "compliance_event_notify_groups",
    Base.metadata,
    Column(
        "compliance_event_id",
        Integer,
        ForeignKey("compliance_events.id"),
        primary_key=True,
    ),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)


class ComplianceEvent(Base):
    __tablename__ = "compliance_events"
    __table_args__ = (
        UniqueConstraint("name", "scope_id", name="uq_compliance_events_name_scope"),
    )
    id = Column(Integer, primary_key=True, index=True)
    scope_id = Column(Integer, ForeignKey("compliance_scopes.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    next_due_date = Column(Date, nullable=True)
    last_done_date = Column(Date, nullable=True)
    notify = Column(Boolean, nullable=True)
    notified = Column(Boolean, nullable=True, default=False)
    remind_before_days = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    scope = relationship("ComplianceScope", back_populates="events")
    notify_users = relationship(
        "User",
        secondary=compliance_event_notify_users,
        backref="compliance_event_notifications",
    )
    notify_groups = relationship(
        "Group",
        secondary=compliance_event_notify_groups,
        backref="compliance_event_notifications",
    )
