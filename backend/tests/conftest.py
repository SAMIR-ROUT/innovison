import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv(dotenv_path=backend_dir / ".env")

from app.main import app
from app.database import SessionLocal
from app.models import Sponsor


@pytest.fixture(scope="session")
def client():
    """Single TestClient instance shared across all tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def api_key():
    """Loads API_KEY from .env once and exposes it as a fixture."""
    key = os.getenv("API_KEY")
    assert key, "API_KEY must be set in .env file"
    return key


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically cleans up test sponsors created during test execution."""
    yield
    db = SessionLocal()
    try:
        test_rows = db.query(Sponsor).filter(Sponsor.name.like("TEST_%")).all()
        for r in test_rows:
            db.delete(r)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
