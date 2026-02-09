from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # Oracle
    db_username: str = Field(default="", alias="DB_USERNAME")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=1521, alias="DB_PORT")
    db_service_name: str = Field(default="", alias="DB_SERVICE_NAME")

    @computed_field
    @property
    def oracle_dsn(self) -> str:
        if self.db_host and self.db_service_name:
            return f"{self.db_host}:{self.db_port}/{self.db_service_name}"
        return ""

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Chat streaming settings
    chat_prompt_preview_length: int = Field(
        default=50, description="Length of prompt preview in logs"
    )
    chat_paragraph_flush_threshold: int = Field(
        default=200, description="Minimum buffer size for paragraph mode"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
