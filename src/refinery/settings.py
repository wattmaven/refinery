from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings for the application.
    """

    python_env: str | None = "production"
    refinery_domain: str
    log_level: str = "INFO"
    mistral_api_key: str
    openai_api_key: str
    refinery_s3_endpoint_url: str | None = None
    refinery_s3_access_key_id: str | None = None
    refinery_s3_secret_access_key: str | None = None

    model_config: SettingsConfigDict = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
