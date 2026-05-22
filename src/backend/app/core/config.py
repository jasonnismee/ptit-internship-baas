import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    KUBE_CONFIG_PATH: str
    GEMINI_API_KEY: Optional[str] = None
    class Config:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(current_dir, "..", "..", ".env")
        env_file = env_path
        env_file_encoding = "utf-8"
settings = Settings()