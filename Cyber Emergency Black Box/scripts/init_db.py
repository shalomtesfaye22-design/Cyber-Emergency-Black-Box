"""
init_db.py — Standalone database initialisation script.

Usage:
    python scripts/init_db.py           # initialise database (safe, idempotent)
    python scripts/init_db.py --reset   # drop and recreate all tables (destructive!)

Run from the project root:
    cd cyber-emergency-black-box
    python scripts/init_db.py
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a standalone script
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


async def init(reset: bool = False) -> None:
    from backend.config import settings, ensure_directories
    from backend.database.engine import get_engine
    from backend.database.models import Base

    ensure_directories()

    engine = get_engine()

    async with engine.begin() as conn:
        if reset:
            print("WARNING: Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("Tables dropped.")

        await conn.run_sync(Base.metadata.create_all)
        print("Tables created (or already exist).")

    # Insert default settings rows
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from backend.database.crud import seed_default_settings

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        inserted = await seed_default_settings(session)
        if inserted:
            print(f"Default settings inserted: {inserted} rows.")
        else:
            print("Settings already present, skipping seed.")

    await engine.dispose()
    print(f"Database ready at: {settings.database_url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise the Black Box database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables. THIS DELETES ALL DATA.",
    )
    args = parser.parse_args()

    if args.reset:
        confirm = input("This will DELETE ALL DATA. Type 'yes' to confirm: ").strip()
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(init(reset=args.reset))


if __name__ == "__main__":
    main()
