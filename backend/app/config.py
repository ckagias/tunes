import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App-wide config, loaded from env vars and .env — see .env.example."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def base_temp_dir(self) -> Path:
        path = Path(tempfile.gettempdir()) / "tunes-sessions"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
