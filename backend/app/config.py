from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):


    app_name: str = "Food Ordering Backend"
    database_url: str


    jwt_secret_key: str = "mcp-secret-ollama"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    class Config:
        env_prefix = "BACKEND_"
 
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 
