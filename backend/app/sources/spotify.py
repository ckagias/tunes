"""
Spotify source — Phase 2, not yet implemented.

Spotify's API does not expose downloadable audio streams. The correct design
(same approach as spotdl) is:
  1. Use the Spotify Web API to resolve track/album/playlist metadata
     (title, artist, album, cover art) — requires Spotify API credentials.
  2. Search YouTube for a matching upload and download the audio from there.
  3. Tag the resulting file with the *Spotify* metadata (more reliable than
     YouTube's freeform titles), using the same tagging pipeline as the
     YouTube source (see services/ydl_opts.py).

This stub only implements `matches()` so the registry can recognize Spotify
URLs and return a clear "not yet supported" error instead of a confusing
mismatch.
"""

from app.models import InfoResponse
from app.sources.base import Source


class SpotifySource(Source):
    name = "spotify"

    def matches(self, url: str) -> bool:
        return "open.spotify.com" in url or url.startswith("spotify:")

    def fetch_info(self, url: str) -> InfoResponse:
        raise NotImplementedError(
            "Spotify support is planned (Phase 2) but not yet implemented. "
            "See app/sources/spotify.py for the design notes."
        )

    def download_track(self, url, title, music_dir, progress_hook, pp_hook):
        raise NotImplementedError(
            "Spotify support is planned (Phase 2) but not yet implemented."
        )
