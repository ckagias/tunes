"""
SoundCloud source — Phase 3, not yet implemented.

SoundCloud tracks can typically be extracted directly with yt-dlp (it has a
built-in SoundCloud extractor), so this source would likely reuse the same
download_ydl_opts()/tagging pipeline as YouTube with only the info-fetching
logic swapped. Left as a stub until phase 3 so the registry can recognize
SoundCloud URLs and return a clear "not yet supported" error.
"""

from app.models import InfoResponse
from app.sources.base import Source


class SoundCloudSource(Source):
    name = "soundcloud"

    def matches(self, url: str) -> bool:
        return "soundcloud.com" in url

    def fetch_info(self, url: str) -> InfoResponse:
        raise NotImplementedError(
            "SoundCloud support is planned (Phase 3) but not yet implemented. "
            "See app/sources/soundcloud.py for the design notes."
        )

    def download_track(self, url, title, music_dir, progress_hook, pp_hook):
        raise NotImplementedError(
            "SoundCloud support is planned (Phase 3) but not yet implemented."
        )
