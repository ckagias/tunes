"""Copies finished downloads into a persistent library folder and, on Windows, adds them
to classic iTunes. Both steps are no-ops when unconfigured/unsupported so callers can always
call through without special-casing the platform or settings."""

import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Optional

from app.config import settings

_SYNC_SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "sync_to_itunes.py"


def is_import_supported() -> bool:
    return sys.platform == "win32"


def _load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_to_itunes", _SYNC_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {_SYNC_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_session_to_library(music_dir: str, is_playlist: bool) -> Optional[Path]:
    """Copy a finished download's files into settings.library_path. For a single track,
    copies just the files in music_dir; for a playlist/album, copies the whole named
    subfolder (cover art, .m3u8, and all). Returns the destination folder, or None if
    library_dir isn't configured."""
    library_dir = settings.library_path
    if library_dir is None:
        return None

    source = Path(music_dir)
    if is_playlist:
        dest = library_dir / source.name
        dest.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            if item.is_file():
                shutil.copy2(item, dest / item.name)
        return dest

    for item in source.iterdir():
        if item.is_file():
            shutil.copy2(item, library_dir / item.name)
    return library_dir


def import_to_itunes(folder: Path) -> tuple[int, int]:
    """Add every MP3 in folder to iTunes. Returns (added, total); (0, 0) when unsupported
    or on failure — callers surface a message rather than treating this as fatal."""
    if not is_import_supported():
        return 0, 0

    module = _load_sync_module()
    return module.add_folder_to_itunes(folder)
