from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    DATABASE_URL is required in production. For local/dev via Docker Compose,
    it will typically look like:

        postgresql+psycopg2://food_user:food_password@db:5432/food_db
    """

    app_name: str = "Food Ordering Backend"
    database_url: str

    # JWT settings for auth
    jwt_secret_key: str = "mcp-secret-ollama"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    class Config:
        env_prefix = "BACKEND_"
        # When running locally (not via Docker), you can create backend/.env
        # and this will be used as a fallback.
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 
