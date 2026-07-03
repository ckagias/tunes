import asyncio

from fastapi import APIRouter, HTTPException

from app.models import InfoRequest, InfoResponse
from app.services.media import normalise_url
from app.sources import registry

router = APIRouter()


@router.post("/info", response_model=InfoResponse)
async def get_info(payload: InfoRequest) -> InfoResponse:
    url = normalise_url(payload.url)
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    try:
        source = registry.resolve(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    loop = asyncio.get_running_loop()
    try:
        # yt-dlp's extract_info is blocking network I/O — keep it off the event loop.
        info = await loop.run_in_executor(None, source.fetch_info, url)
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return info
