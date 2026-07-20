from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost/chat_app_dev"
    secret_key: str = "dev-secret-change-me"
    socket_origins: str = "http://localhost,http://127.0.0.1"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.socket_origins.split(",") if o.strip()]


settings = Settings()
