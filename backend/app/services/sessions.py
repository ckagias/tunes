"""
In-memory session registry. Each session tracks a temp directory, a progress
queue, and the files produced during a download job. Nothing is persisted —
sessions live only as long as the process and are wiped once their files are
served to the browser (or the process restarts).

Ported from the original Flask app's `sessions` dict + BASE_TEMP_DIR model.
"""

import os
import queue
import shutil
import uuid
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class Session:
    session_id: str
    session_dir: str
    queue: "queue.Queue" = field(default_factory=queue.Queue)
    files: dict[str, str] = field(default_factory=dict)  # url -> filepath
    zip_path: str | None = None
    zip_name: str | None = None


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, session_id: str | None, music_subdir: str | None) -> Session:
        session_id = session_id or str(uuid.uuid4())
        session_dir = os.path.join(str(settings.base_temp_dir), session_id)
        os.makedirs(session_dir, exist_ok=True)
        session = Session(session_id=session_id, session_dir=session_dir)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def cleanup(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session and os.path.isdir(session.session_dir):
            shutil.rmtree(session.session_dir, ignore_errors=True)


# Module-level singleton, mirroring the Flask app's global `sessions` dict.
store = SessionStore()
