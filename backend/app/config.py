import tempfile
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App-wide config, loaded from env vars and .env — see .env.example."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    allowed_origins: str = "http://localhost:5173"

    # Persistent folder downloads get copied into for iTunes import. Empty disables the feature.
    library_dir: str = ""
    # Master switch: auto-add finished downloads to iTunes (classic, Windows-only) after copying
    # them to library_dir. A per-request toggle from the frontend can still override this.
    auto_import_itunes: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def base_temp_dir(self) -> Path:
        path = Path(tempfile.gettempdir()) / "tunes-sessions"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def library_path(self) -> Optional[Path]:
        raw = self.library_dir.strip()
        if not raw:
            return None
        path = Path(raw)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
