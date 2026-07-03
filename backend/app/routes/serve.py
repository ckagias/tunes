import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.services.sessions import store

router = APIRouter()


def _cleanup_single_file(session_id: str, filepath: str) -> None:
    try:
        os.remove(filepath)
    except Exception:
        pass
    session = store.get(session_id)
    if not session:
        return
    try:
        if os.path.isdir(session.session_dir):
            remaining_mp3s = any(
                f.endswith(".mp3")
                for _, _, files in os.walk(session.session_dir)
                for f in files
            )
            if not remaining_mp3s:
                store.cleanup(session_id)
    except Exception:
        pass


@router.get("/serve/{session_id}/{filename:path}")
async def serve_file(session_id: str, filename: str) -> FileResponse:
    """Stream a single MP3 to the browser, then delete it."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    filepath = None
    for path in session.files.values():
        if os.path.basename(path) == filename:
            filepath = path
            break

    if not filepath or not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        filename=filename,
        background=BackgroundTask(_cleanup_single_file, session_id, filepath),
    )


@router.get("/serve-zip/{session_id}")
async def serve_zip(session_id: str) -> FileResponse:
    """Stream the playlist zip to the browser, then delete the entire session."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not session.zip_path or not os.path.isfile(session.zip_path):
        raise HTTPException(status_code=404, detail="Zip not ready")

    return FileResponse(
        session.zip_path,
        media_type="application/zip",
        filename=session.zip_name or "playlist.zip",
        background=BackgroundTask(store.cleanup, session_id),
    )
