import os
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Samagra - Evidence-First Indian Standards Engine"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/samagra_db")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3.5:2b")
    RRF_K: int = 60
    TOP_K_RETRIEVAL: int = 15
    AMBIGUITY_SCORE_DELTA_THRESHOLD: float = 0.05
    MIN_CONFIDENCE_THRESHOLD: float = 0.30
    DATA_DIR: Path = DATA_DIR
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
