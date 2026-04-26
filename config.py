from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-ada-002"
    llm_model: str = "gpt-3.5-turbo"

    vector_db_type: str = "chroma"
    vector_db_path: str = "./data/chroma_db"

    sqlite_db_path: str = "./data/app.db"

    max_memory_items: int = 5
    max_conversation_turns: int = 20

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
