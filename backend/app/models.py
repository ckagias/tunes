from pydantic import BaseModel


class TrackInfo(BaseModel):
    id: str
    title: str
    url: str
    duration: str = ""
    thumbnail: str = ""
    uploader: str = ""


class InfoRequest(BaseModel):
    url: str


class InfoResponse(BaseModel):
    type: str  # "single" | "playlist"
    title: str
    uploader: str = ""
    thumbnail: str = ""
    count: int
    tracks: list[TrackInfo]


class DownloadRequest(BaseModel):
    urls: list[str]
    titles: dict[str, str] = {}
    playlist_title: str = ""
    playlist_thumbnail: str = ""
    session_id: str | None = None


class DownloadResponse(BaseModel):
    session_id: str
    is_playlist: bool


class ErrorResponse(BaseModel):
    error: str
