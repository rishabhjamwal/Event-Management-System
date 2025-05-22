# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ems.core.config import settings

# Convert the PostgresDsn to a string
database_url = str(settings.DATABASE_URI)

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()