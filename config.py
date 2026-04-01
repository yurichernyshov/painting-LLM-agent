from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "users.db"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_HOST: str = "http://localhost:11434"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
