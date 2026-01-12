import os
from dotenv import load_dotenv

# 1. Load the .env file immediately
# This searches for a file named .env and loads the variables into the system
load_dotenv()

class Settings:
    PROJECT_NAME: str = "GraphRec API"
    PROJECT_VERSION: str = "1.0.0"

    # 2. Get the Database URL
    # It first looks for "DATABASE_URL" in your .env file (Supabase).
    # If it can't find it, it falls back to the local sqlite file.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./graphrec.db")

    # 3. Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = Settings()