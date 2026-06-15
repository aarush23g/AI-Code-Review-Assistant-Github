from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Code Review Assistant"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    github_webhook_secret: str = "replace_me"
    github_app_id: str = "replace_me"
    github_private_key_path: str = "replace_me"
    github_client_id: str = "replace_me"
    github_client_secret: str = "replace_me"

    openai_api_key: str = "replace_me"
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"
    use_mock_llm: bool = False

    redis_url: str = "redis://localhost:6379/0"
    review_metrics_db_path: str = "data/review_metrics.sqlite3"

    max_review_files: int = 20
    max_review_chunks: int = 12
    large_pr_chunk_threshold: int = 20
    large_pr_file_threshold: int = 25
    max_inline_comments: int = 3
    min_inline_comment_confidence: float = 0.85
    default_review_mode: str = "quick"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def github_app_enabled(self) -> bool:
        return (
            self.github_app_id != "replace_me"
            and self.github_private_key_path != "replace_me"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
