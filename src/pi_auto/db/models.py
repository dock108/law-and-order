"""SQLAlchemy models for the database schema."""

from sqlalchemy import (
    NUMERIC,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Client(Base):
    """Model representing a client."""

    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    dob = Column(Date, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    incidents = relationship(
        "Incident", back_populates="client", cascade="all, delete-orphan"
    )


class Incident(Base):
    """Model representing a personal injury incident."""

    __tablename__ = "incident"

    id = Column(Integer, primary_key=True)
    client_id = Column(
        Integer, ForeignKey("client.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(Date, nullable=True)
    location = Column(Text, nullable=True)
    police_report_url = Column(String(255), nullable=True)
    injuries = Column(JSON, nullable=True)
    vehicle_damage_text = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Settlement and disbursement related fields
    settlement_amount = Column(NUMERIC(precision=10, scale=2), nullable=True)
    attorney_fee_pct = Column(
        NUMERIC(precision=5, scale=2), nullable=False, server_default="33.33"
    )
    lien_total = Column(
        NUMERIC(precision=10, scale=2), nullable=False, server_default="0"
    )
    disbursement_status = Column(String(50), nullable=False, server_default="pending")

    # Relationships
    client = relationship("Client", back_populates="incidents")
    insurances = relationship(
        "Insurance", back_populates="incident", cascade="all, delete-orphan"
    )
    providers = relationship(
        "Provider", back_populates="incident", cascade="all, delete-orphan"
    )
    docs = relationship("Doc", back_populates="incident", cascade="all, delete-orphan")
    tasks = relationship(
        "Task", back_populates="incident", cascade="all, delete-orphan"
    )
    fee_adjustments = relationship(
        "FeeAdjustment", back_populates="incident", cascade="all, delete-orphan"
    )


class Insurance(Base):
    """Model representing insurance information."""

    __tablename__ = "insurance"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer, ForeignKey("incident.id", ondelete="CASCADE"), nullable=False
    )
    carrier_name = Column(String(255), nullable=False)
    policy_number = Column(String(100), nullable=True)
    claim_number = Column(String(100), nullable=True)
    is_client_side = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="insurances")


class Provider(Base):
    """Model representing a medical provider."""

    __tablename__ = "provider"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer, ForeignKey("incident.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    fax = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="providers")


class Doc(Base):
    """Model representing a document."""

    __tablename__ = "doc"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer, ForeignKey("incident.id", ondelete="CASCADE"), nullable=False
    )
    type = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, server_default="pending")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="docs")


class Task(Base):
    """Model representing a task."""

    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer, ForeignKey("incident.id", ondelete="CASCADE"), nullable=False
    )
    type = Column(String(100), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")
    assignee_email = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="tasks")


class FeeAdjustment(Base):
    """Model representing fee adjustments for a settlement."""

    __tablename__ = "fee_adjustments"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer, ForeignKey("incident.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(String(255), nullable=False)
    amount = Column(NUMERIC(precision=10, scale=2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="fee_adjustments")
