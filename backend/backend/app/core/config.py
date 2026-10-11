from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FutureFund Backend"
    API_V1_STR: str = "/api/v1"
    
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    
    AI_PROVIDER: str = "gemini" # 'gemini' or 'groq'
    
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    
    DATABASE_URL: str = "postgresql+psycopg://futurefund_user:CHANGE_ME@localhost:5432/futurefund"
    
    SECRET_KEY: str = "development_secret_do_not_use_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

settings = Settings()
