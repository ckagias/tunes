import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.sessions import store

router = APIRouter()


@router.get("/serve/{session_id}/{filename:path}")
async def serve_file(session_id: str, filename: str) -> FileResponse:
    """Stream a single MP3. Doesn't clean up the session — stays re-downloadable until DELETE /session/{id}."""
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
    )


@router.get("/serve-zip/{session_id}")
async def serve_zip(session_id: str) -> FileResponse:
    """Stream the playlist zip. Doesn't clean up the session — stays re-downloadable until DELETE /session/{id}."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not session.zip_path or not os.path.isfile(session.zip_path):
        raise HTTPException(status_code=404, detail="Zip not ready")

    return FileResponse(
        session.zip_path,
        media_type="application/zip",
        filename=session.zip_name or "playlist.zip",
    )


@router.api_route("/session/{session_id}", methods=["DELETE", "POST"])
async def end_session(session_id: str) -> dict:
    """End a session and delete its temp files. POST is for navigator.sendBeacon on page unload."""
    store.cleanup(session_id)
    return {"ok": True}
