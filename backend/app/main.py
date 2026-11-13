import os
from typing import List

# Import necessary modules from FastAPI, Starlette, and SQLAlchemy
from fastapi import FastAPI, Depends, status, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Sponsor, SponsorHistory
from app.schemas import SponsorCreate, SponsorResponse, SponsorUpdate, SponsorHistoryResponse
from app.auth import verify_api_key

# OpenAPI tags metadata for clean documentation grouping
tags_metadata = [
    {
        "name": "health",
        "description": "API health and database connectivity checks",
    },
    {
        "name": "sponsors",
        "description": "Operations for creating, retrieving, and updating event sponsor commitments",
    },
    {
        "name": "history",
        "description": "Audit trail and historical logs of changes to sponsor commitments",
    },
]

# Create an instance of the FastAPI application with polished OpenAPI metadata
app = FastAPI(
    title="Event Second Brain — Sponsor API",
    description=(
        "Manages sponsor data and commitment history for a college event organizing team. "
        "Allows creating sponsors, updating their financial commitments, tracking complete audit history, "
        "and protecting write operations using API key authentication."
    ),
    version="1.0.0",
    contact={
        "name": "Member 3 — Backend & Database",
    },
    openapi_tags=tags_metadata,
)

# --- BRICK 14: CORS Setup ---
# Read allowed origins from environment (defaults to "*" for development)
raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


# --- BRICK 13: Centralized Error Handling ---
# 1. Validation error handler (HTTP 422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for error in exc.errors():
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        details.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation failed",
            "status_code": 422,
            "details": details,
        },
    )


# 2. HTTP exception handler (e.g., 404, 400, etc.)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "status_code": exc.status_code,
        },
    )


# 3. Global unhandled exception handler (HTTP 500)
# Sanitized so internal exceptions, SQL queries, or database credentials are never leaked
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
        },
    )


# Define a GET endpoint at the path "/health"
# This is a simple health-check route used to verify that the server is running properly
@app.get(
    "/health",
    tags=["health"],
    summary="Service health check",
    response_description="Returns operational status of the API",
)
def health_check():
    # Return a basic JSON response confirming status
    return {"status": "ok"}


# Define a GET endpoint at the path "/health/db"
# Verifies database connectivity by executing a lightweight query
@app.get(
    "/health/db",
    tags=["health"],
    summary="Database connectivity check",
    response_description="Returns database connection status",
)
def health_db_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Database connection failed",
                "status_code": 500,
            },
        )



# Define a POST endpoint at the path "/sponsors"
# Inserts a new sponsor record and returns the saved sponsor
# Protected by verify_api_key dependency
@app.post(
    "/sponsors",
    response_model=SponsorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["sponsors"],
    summary="Create a new sponsor commitment",
    response_description="The created sponsor record",
    dependencies=[Depends(verify_api_key)],
)
def create_sponsor(payload: SponsorCreate, db: Session = Depends(get_db)):
    new_sponsor = Sponsor(
        name=payload.name,
        original_commitment=payload.original_commitment,
        current_commitment=payload.current_commitment,
    )
    db.add(new_sponsor)
    db.commit()
    db.refresh(new_sponsor)
    return new_sponsor


# Define a GET endpoint at the path "/sponsors"
# Returns a list of all sponsors in the database (public read)
@app.get(
    "/sponsors",
    response_model=List[SponsorResponse],
    tags=["sponsors"],
    summary="List all sponsors",
    response_description="List of all sponsor records in the database",
)
def get_sponsors(db: Session = Depends(get_db)):
    sponsors = db.query(Sponsor).all()
    return sponsors


# Define a GET endpoint at the path "/sponsors/{sponsor_id}"
# Returns a single sponsor by its ID, or HTTP 404 if not found (public read)
@app.get(
    "/sponsors/{sponsor_id}",
    response_model=SponsorResponse,
    tags=["sponsors"],
    summary="Get sponsor by ID",
    response_description="The requested sponsor record",
)
def get_sponsor(sponsor_id: int, db: Session = Depends(get_db)):
    sponsor = db.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
    if not sponsor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )
    return sponsor


# Define a PATCH endpoint at the path "/sponsors/{sponsor_id}"
# Updates current_commitment and atomically logs change into sponsor_history
# Protected by verify_api_key dependency
@app.patch(
    "/sponsors/{sponsor_id}",
    response_model=SponsorResponse,
    tags=["sponsors"],
    summary="Update sponsor commitment and log history",
    response_description="The updated sponsor record",
    dependencies=[Depends(verify_api_key)],
)
def update_sponsor(sponsor_id: int, payload: SponsorUpdate, db: Session = Depends(get_db)):
    sponsor = db.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
    if not sponsor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )

    # Capture old commitment before applying change
    old_commitment = sponsor.current_commitment
    new_commitment = payload.current_commitment

    try:
        # Create history entry
        history_entry = SponsorHistory(
            sponsor_id=sponsor.id,
            old_commitment=old_commitment,
            new_commitment=new_commitment,
            note=payload.note,
        )
        db.add(history_entry)

        # Update sponsor record
        sponsor.current_commitment = new_commitment

        # Commit both changes in the same atomic database transaction
        db.commit()
        db.refresh(sponsor)

        return sponsor
    except Exception:
        db.rollback()
        raise



# Define a GET endpoint at the path "/sponsors/{sponsor_id}/history"
# Returns all change history rows for a sponsor, ordered newest first (public read)
@app.get(
    "/sponsors/{sponsor_id}/history",
    response_model=List[SponsorHistoryResponse],
    tags=["history"],
    summary="Get sponsor commitment history",
    response_description="Chronological audit history of commitment adjustments",
)
def get_sponsor_history(sponsor_id: int, db: Session = Depends(get_db)):
    # First verify that the sponsor exists
    sponsor = db.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
    if not sponsor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )

    history = (
        db.query(SponsorHistory)
        .filter(SponsorHistory.sponsor_id == sponsor_id)
        .order_by(SponsorHistory.changed_at.desc(), SponsorHistory.id.desc())
        .all()
    )
    return history





