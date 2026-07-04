"""Resolves a URL to the Source that should handle it. Routes never import a concrete source directly."""

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
