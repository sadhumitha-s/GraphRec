import os

class Settings:
    PROJECT_NAME: str = "GraphRec API"
    PROJECT_VERSION: str = "1.0.0"

    # DATABASE_URL: str = "postgresql://postgres:.."

    # (Comment out the line below while testing with the hardcoded URL above)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./graphrec.db")

settings = Settings()