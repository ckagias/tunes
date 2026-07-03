"""
The Source interface: everything a "place a song/playlist link can come from"
needs to implement. Routes only ever talk to this interface via the registry
(see registry.py) — they never import a concrete source directly. That's the
seam that lets Spotify/SoundCloud be added later without touching routes.
"""

from abc import ABC, abstractmethod

from app.models import InfoResponse


class Source(ABC):
    """One origin (YouTube, Spotify, SoundCloud, ...)."""

    name: str

    @abstractmethod
    def matches(self, url: str) -> bool:
        """Does this source own/handle the given URL?"""
        raise NotImplementedError

    @abstractmethod
    def fetch_info(self, url: str) -> InfoResponse:
        """
        Return normalized metadata for a single track or playlist at `url`.
        Must not download any media.
        """
        raise NotImplementedError

    @abstractmethod
    def download_track(
        self,
        url: str,
        title: str,
        music_dir: str,
        progress_hook,
        pp_hook,
    ) -> str | None:
        """
        Download+tag a single track into music_dir, calling progress_hook /
        pp_hook as yt-dlp (or an equivalent backend) reports progress.
        Returns the final file path, or None on failure.
        """
        raise NotImplementedError
