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
    # True only for an actual playlist link (a curated, user-ordered track
    # list). type is "playlist" for albums too, but albums don't set this —
    # "is_playlist" elsewhere in the API (DownloadRequest/DownloadResponse)
    # already means "is a zip-producing collection" (playlist OR album), so
    # this is deliberately a different name to avoid colliding with that.
    # Drives whether the download zip gets an .m3u8 alongside the MP3s,
    # since an album's track order is already implied by its own metadata.
    is_true_playlist: bool = False


class DownloadRequest(BaseModel):
    urls: list[str]
    titles: dict[str, str] = {}
    playlist_title: str = ""
    playlist_thumbnail: str = ""
    is_true_playlist: bool = False
    session_id: str | None = None


class DownloadResponse(BaseModel):
    session_id: str
    is_playlist: bool


class ErrorResponse(BaseModel):
    error: str
