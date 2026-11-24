import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQLite database file in the project folder
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dashboard_review.db")

if DATABASE_URL.startswith("sqlite"):
    sqlite_prefix = "sqlite:///"
    if DATABASE_URL.startswith(sqlite_prefix):
        database_path = DATABASE_URL[len(sqlite_prefix):]
        if database_path and not database_path.startswith(":"):
            Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

engine_options = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
