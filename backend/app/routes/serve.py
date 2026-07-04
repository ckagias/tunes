import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.sessions import store

router = APIRouter()


@router.get("/serve/{session_id}/{filename:path}")
async def serve_file(session_id: str, filename: str) -> FileResponse:
    """
    Stream a single MP3 to the browser. Like serve_zip, this does NOT delete
    the file or clean up the session afterwards — it should stay
    re-downloadable (repeat Save clicks, retry after a network blip) until
    the frontend explicitly ends the session (see DELETE /session/{id}),
    which fires on "Start over", starting a new lookup, or the page
    unloading.
    """
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
    """
    Stream the playlist zip to the browser. Unlike serve_file, this does NOT
    clean up the session afterwards — the zip should stay downloadable (e.g.
    a retry after a network blip, or just clicking Save again) until the
    frontend explicitly ends the session (see DELETE /session/{id} below),
    which fires on "Start over", starting a new lookup, or the page
    unloading.
    """
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
    """
    Explicitly end a session and delete its temp files. Called by the
    frontend when the user is done with a session (Start over, starting a
    new lookup, or leaving the page) rather than relying on every file
    download to trigger cleanup — a playlist zip should stay available for
    repeat downloads until the user is actually done with it.

    Accepts both DELETE (normal fetch calls) and POST (navigator.sendBeacon,
    used on page unload, always sends POST and can't set a custom method).
    """
    store.cleanup(session_id)
    return {"ok": True}
