"""
Resolves a URL to the Source that should handle it. Routes call this and
never import a concrete source directly — this is the extension seam for
adding more platforms later (Spotify/SoundCloud were tried and rolled back;
revisit in a few months, see README roadmap) without touching route code.
"""

from app.sources.base import Source
from app.sources.youtube import YouTubeSource

_SOURCES: list[Source] = [
    YouTubeSource(),
]


def resolve(url: str) -> Source:
    for source in _SOURCES:
        if source.matches(url):
            return source
    raise ValueError("Unsupported URL. Currently only YouTube links are supported.")
