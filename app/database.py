from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost/dbname")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)
