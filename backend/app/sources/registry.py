"""
Resolves a URL to the Source that should handle it. Routes call this and
never import a concrete source directly — this is the extension seam that
lets platforms be added without touching route code.

Spotify resolves to a matching YouTube video/track (see its fetch_info())
and then delegates download_track() straight to YouTubeSource — so it
doesn't need any ordering precedence relative to YouTube itself; its URL
domain is disjoint from youtube.com/youtu.be.
"""

from app.sources.base import Source
from app.sources.spotify import SpotifySource
from app.sources.youtube import YouTubeSource

_SOURCES: list[Source] = [
    YouTubeSource(),
    SpotifySource(),
]


def resolve(url: str) -> Source:
    for source in _SOURCES:
        if source.matches(url):
            return source
    raise ValueError("Unsupported URL. Paste a YouTube or Spotify link.")
