import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    App-wide configuration, loaded from environment variables (and .env if present).
    See .env.example for the full list of supported variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    allowed_origins: str = "http://localhost:5173"
    bgu_pot_server_host: str | None = None

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def base_temp_dir(self) -> Path:
        path = Path(tempfile.gettempdir()) / "tunes-sessions"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
