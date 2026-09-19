from fastapi import APIRouter, HTTPException, Request

from app.models import DownloadRequest, DownloadResponse
from app.services import jobs
from app.services.notifier import notify_event

router = APIRouter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.headers.get("x-real-ip"):
        return request.headers["x-real-ip"].strip()
    if request.client:
        return request.client.host
    return ""


@router.post("/download", response_model=DownloadResponse)
async def start_download(request: Request, payload: DownloadRequest) -> DownloadResponse:
    if not payload.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    session, is_playlist = await jobs.start_download(
        session_id=payload.session_id,
        urls=payload.urls,
        titles=payload.titles,
        playlist_title=payload.playlist_title,
        playlist_thumbnail=payload.playlist_thumbnail,
        is_true_playlist=payload.is_true_playlist,
        auto_import=payload.auto_import,
    )

    session.client_ip = _client_ip(request)
    session.title = payload.playlist_title or payload.titles.get(payload.urls[0], payload.urls[0])

    item_type = "playlist" if payload.is_true_playlist else ("album" if is_playlist else "track")
    notify_event(
        event="request_started",
        client_ip=session.client_ip,
        title=session.title,
        item_type=item_type,
        tracks_count=len(payload.urls),
        session_id=session.session_id,
    )

    return DownloadResponse(session_id=session.session_id, is_playlist=is_playlist)
