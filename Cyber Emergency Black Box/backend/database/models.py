"""SQLAlchemy models for the local black-box database."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EventModel(Base):
    __tablename__ = "events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[str | None] = mapped_column(String)
    process_name: Mapped[str | None] = mapped_column(String)
    action: Mapped[str | None] = mapped_column(String)
    target: Mapped[str | None] = mapped_column(String)
    source_ip: Mapped[str | None] = mapped_column(String)
    destination_ip: Mapped[str | None] = mapped_column(String)
    destination_port: Mapped[int | None] = mapped_column(Integer)
    protocol: Mapped[str | None] = mapped_column(String)
    metadata_json: Mapped[str] = mapped_column("metadata", Text, default="{}")
    severity: Mapped[str] = mapped_column(String, default="INFO", index=True)
    raw_hash: Mapped[str | None] = mapped_column(String)
    previous_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preserved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_events_timestamp_type", "timestamp", "event_type"),
    )


class IncidentModel(Base):
    __tablename__ = "incidents"
    incident_id: Mapped[str] = mapped_column(String, primary_key=True)
    detection_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    rule_name: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="OPEN", index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    interpretation: Mapped[str | None] = mapped_column(Text)
    evidence_path: Mapped[str | None] = mapped_column(String)
    event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class IncidentEventModel(Base):
    __tablename__ = "incident_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.incident_id"), index=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.event_id"), index=True)


class SystemSnapshotModel(Base):
    __tablename__ = "system_snapshots"
    snapshot_id: Mapped[str] = mapped_column(String, primary_key=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String)
    os_name: Mapped[str | None] = mapped_column(String)
    os_version: Mapped[str | None] = mapped_column(String)
    cpu_count: Mapped[int | None] = mapped_column(Integer)
    memory_total_gb: Mapped[float | None] = mapped_column(Float)
    uptime_seconds: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[str] = mapped_column("metadata", Text, default="{}")


class SettingsModel(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

