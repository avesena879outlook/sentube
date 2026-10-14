import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    YOUTUBE_API_KEY: str = ""
    APP_ENV: str = "development"
    
    # Path Artefak Model
    MODEL_A_PATH: Path = BASE_DIR / "artifacts" / "svm_mrmr_fast.joblib"
    MODEL_B_PATH: Path = BASE_DIR / "artifacts" / "svm_baseline_fast.joblib"
    
    class Config:
        env_file = BASE_DIR / ".env"
        extra = "ignore"

settings = Settings()
