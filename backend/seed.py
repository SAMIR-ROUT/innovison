import os
import sys
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load .env file
load_dotenv(dotenv_path=backend_dir / ".env")

from app.database import SessionLocal
from app.models import Sponsor, SponsorHistory


def seed_database():
    db = SessionLocal()
    try:
        # Check if sponsors table already has data
        existing_count = db.query(Sponsor).count()
        if existing_count > 0:
            print("Database already seeded. Skipping.")
            return

        sponsors_to_seed = [
            {
                "name": "TechCorp Pvt Ltd",
                "original_commitment": Decimal("200000"),
                "current_commitment": Decimal("120000"),
            },
            {
                "name": "InnovateSoft",
                "original_commitment": Decimal("150000"),
                "current_commitment": Decimal("150000"),
            },
            {
                "name": "BuildFast Solutions",
                "original_commitment": Decimal("100000"),
                "current_commitment": Decimal("75000"),
            },
            {
                "name": "NextGen Ventures",
                "original_commitment": Decimal("80000"),
                "current_commitment": Decimal("80000"),
            },
            {
                "name": "CloudBase India",
                "original_commitment": Decimal("50000"),
                "current_commitment": Decimal("50000"),
            },
        ]

        inserted_names = []
        for item in sponsors_to_seed:
            sponsor = Sponsor(
                name=item["name"],
                original_commitment=item["original_commitment"],
                current_commitment=item["current_commitment"],
            )
            db.add(sponsor)
            db.flush()  # Flush to generate sponsor.id

            # For sponsors where original_commitment != current_commitment, log history
            if item["original_commitment"] != item["current_commitment"]:
                history_entry = SponsorHistory(
                    sponsor_id=sponsor.id,
                    old_commitment=item["original_commitment"],
                    new_commitment=item["current_commitment"],
                    note="Initial seeded history entry",
                )
                db.add(history_entry)

            inserted_names.append(sponsor.name)

        db.commit()
        print("Database seeded successfully! Inserted sponsors:")
        for name in inserted_names:
            print(f" - {name}")

    except Exception as exc:
        db.rollback()
        print(f"Error seeding database: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
