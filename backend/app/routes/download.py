from fastapi import APIRouter, HTTPException

from app.models import DownloadRequest, DownloadResponse
from app.services import jobs

router = APIRouter()


@router.post("/download", response_model=DownloadResponse)
async def start_download(payload: DownloadRequest) -> DownloadResponse:
    if not payload.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    session, is_playlist = await jobs.start_download(
        session_id=payload.session_id,
        urls=payload.urls,
        titles=payload.titles,
        playlist_title=payload.playlist_title,
        playlist_thumbnail=payload.playlist_thumbnail,
        is_true_playlist=payload.is_true_playlist,
    )

    return DownloadResponse(session_id=session.session_id, is_playlist=is_playlist)
