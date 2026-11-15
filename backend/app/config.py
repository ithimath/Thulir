import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_DB_PATH = str(BASE_DIR / "thulir.db").replace("\\", "/")

class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "thulir-dev-secret-key-min-32-chars-long-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
    AI_ENABLED: bool = os.getenv("AI_ENABLED", "false").lower() in ("true", "1")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-1.5-flash")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")

settings = Settings()
