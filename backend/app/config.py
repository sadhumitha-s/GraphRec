import os

class Settings:
    PROJECT_NAME: str = "GraphRec API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Defaults to a local SQLite file for testing. 
    # Change to "mysql+pymysql://user:pass@localhost/dbname" for MySQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./graphrec.db")

settings = Settings()