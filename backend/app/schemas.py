from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class SponsorCreate(BaseModel):
    name: str
    original_commitment: Decimal
    current_commitment: Decimal

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty or whitespace only")
        return v.strip()

    @field_validator("original_commitment")
    @classmethod
    def validate_original_commitment(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("original_commitment must be a positive number (> 0)")
        return v

    @field_validator("current_commitment")
    @classmethod
    def validate_current_commitment(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("current_commitment must be a positive number (> 0)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "TechCorp Pvt Ltd",
                "original_commitment": 200000,
                "current_commitment": 200000,
            }
        }
    )


class SponsorUpdate(BaseModel):
    current_commitment: Decimal
    note: Optional[str] = None

    @field_validator("current_commitment")
    @classmethod
    def validate_current_commitment(cls, v: Decimal) -> Decimal:
        if v is not None and v <= 0:
            raise ValueError("current_commitment must be a positive number (> 0)")
        return v

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("note must not be empty or whitespace only")
            return v.strip()
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_commitment": 120000,
                "note": "Sponsor reduced commitment due to budget cuts",
            }
        }
    )




class SponsorResponse(BaseModel):
    id: int
    name: str
    original_commitment: Decimal
    current_commitment: Decimal
    created_at: datetime
    updated_at: datetime

    # Enable ORM mode for Pydantic (from_attributes in Pydantic v2)
    model_config = ConfigDict(from_attributes=True)


class SponsorHistoryResponse(BaseModel):
    id: int
    sponsor_id: int
    old_commitment: Decimal
    new_commitment: Decimal
    changed_at: datetime
    note: Optional[str] = None

    # Enable ORM mode for Pydantic
    model_config = ConfigDict(from_attributes=True)

