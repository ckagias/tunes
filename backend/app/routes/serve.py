import os
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.services.notifier import notify_event
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

    size_bytes = os.path.getsize(filepath)
    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        filename=filename,
        background=BackgroundTask(
            notify_event,
            event="mp3_downloaded",
            client_ip=session.client_ip,
            title=filename,
            item_type="track",
            size_bytes=size_bytes,
            session_id=session_id,
        ),
    )


@router.get("/serve-zip/{session_id}")
async def serve_zip(session_id: str) -> FileResponse:
    """Stream the playlist zip. Doesn't clean up the session — stays re-downloadable until DELETE /session/{id}."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not session.zip_path or not os.path.isfile(session.zip_path):
        raise HTTPException(status_code=404, detail="Zip not ready")

    size_bytes = os.path.getsize(session.zip_path)
    duration = time.time() - session.start_time
    return FileResponse(
        session.zip_path,
        media_type="application/zip",
        filename=session.zip_name or "playlist.zip",
        background=BackgroundTask(
            notify_event,
            event="zip_downloaded",
            client_ip=session.client_ip,
            title=session.title or session.zip_name or "playlist",
            item_type="album",
            tracks_count=len(session.files),
            size_bytes=size_bytes,
            duration_seconds=duration,
            session_id=session_id,
        ),
    )


@router.api_route("/session/{session_id}", methods=["DELETE", "POST"])
async def end_session(request: Request, session_id: str) -> dict:
    """End a session and delete its temp files. POST is for navigator.sendBeacon on page unload."""
    session = store.get(session_id)
    if session:
        notify_event(
            event="session_ended",
            client_ip=session.client_ip,
            title=session.title or session.zip_name or "",
            session_id=session_id,
        )
    store.cleanup(session_id)
    return {"ok": True}
