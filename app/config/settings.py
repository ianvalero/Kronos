from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class RedisSettings(BaseSettings):
    host: str
    port: int = 6379
    db: int = 0
    password: str | None = None
    max_connections: int = 20
    decode_responses: bool = True

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

class CelerySettings(BaseSettings):
    broker_url: str | None = None
    result_backend: str | None = None
    task_serializer: str = "json"
    result_serializer: str = "json"
    result_expires: int = 86400
    task_track_started: bool = True
    worker_max_tasks_per_child: int = 200

    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    log_level: str = "INFO"
    proxy_url: str | None = None
    qdrant_url: str
    postgresql_url: str
    embedding_model_name: str
    embedding_base_url: str
    embedding_chunk_size: int
    embedding_chunk_overlap: int
    files_storage_path: str = "files/"

    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)

    @model_validator(mode="after")
    def assemble_celery_urls(self):
        base_redis_url = f"redis://{self.redis.host}:{self.redis.port}"
        if self.redis.password:
            base_redis_url = f"redis://{self.redis.password}@{self.redis.host}:{self.redis.port}"

        if not self.celery.broker_url:
            self.celery.broker_url = f"{base_redis_url}/2"
        if not self.celery.result_backend:
            self.celery.result_backend = f"{base_redis_url}/3"

        return self

    @model_validator(mode="after")
    def create_files_storage_path(self):
        Path(self.files_storage_path).parent.mkdir(parents=True, exist_ok=True)
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()