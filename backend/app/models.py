from typing import Optional

from pydantic import BaseModel


class TrackInfo(BaseModel):
    id: str
    title: str
    url: str
    duration: str = ""
    thumbnail: str = ""
    uploader: str = ""
    source: str = ""  # "youtube" | "spotify"
    album: str = ""


class InfoRequest(BaseModel):
    url: str


class InfoResponse(BaseModel):
    type: str  # "single" | "playlist"
    title: str
    uploader: str = ""
    thumbnail: str = ""
    count: int
    tracks: list[TrackInfo]
    # True only for a real playlist, not an album (type is "playlist" for both) — drives .m3u8 generation.
    is_true_playlist: bool = False


class DownloadRequest(BaseModel):
    urls: list[str]
    titles: dict[str, str] = {}
    playlist_title: str = ""
    playlist_thumbnail: str = ""
    is_true_playlist: bool = False
    session_id: Optional[str] = None
    # None = defer to the server's AUTO_IMPORT_ITUNES setting; true/false overrides it.
    auto_import: Optional[bool] = None


class DownloadResponse(BaseModel):
    session_id: str
    is_playlist: bool


class ErrorResponse(BaseModel):
    error: str
