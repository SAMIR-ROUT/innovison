from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Sponsor(Base):
    __tablename__ = "sponsors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    original_commitment = Column(Numeric(precision=12, scale=2), nullable=False)
    current_commitment = Column(Numeric(precision=12, scale=2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to history entries
    history = relationship("SponsorHistory", back_populates="sponsor", cascade="all, delete-orphan")


class SponsorHistory(Base):
    __tablename__ = "sponsor_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"), nullable=False, index=True)
    old_commitment = Column(Numeric(precision=12, scale=2), nullable=False)
    new_commitment = Column(Numeric(precision=12, scale=2), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    note = Column(String, nullable=True)

    # Relationship back to sponsor
    sponsor = relationship("Sponsor", back_populates="history")

