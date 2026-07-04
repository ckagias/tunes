"""
Spotify source. Spotify doesn't expose downloadable audio, so the actual
audio always comes from a YouTube Music search match — but the TAGS (title,
artist, album, cover art) come from Spotify's own public embed pages (see
services/spotify_client.py), not from whatever (if anything) YouTube
provides for the matched video.

No developer account, no OAuth, no API calls at all — just an HTTP GET
against open.spotify.com/embed/.... See spotify_client.py's module
docstring for the important caveat: this depends on Spotify continuing to
server-render that page the same way.

Supports single tracks, full albums, and full playlists. Embed pages don't
expose per-track genre, so unlike the previous token-API-based version,
Spotify tracks are downloaded without a genre tag.
"""

import re

from app.models import InfoResponse, TrackInfo
from app.services import spotify_client
from app.services.media import fmt_duration
from app.sources.base import Source
from app.sources.youtube import download_with_overrides, youtube_music_search_url

_URL_RE = re.compile(r"open\.spotify\.com/(track|album|playlist)/([A-Za-z0-9]+)")

# Populated by fetch_info, consumed by download_track — avoids re-fetching
# the Spotify embed page per track at download time. Keyed by the Spotify
# track URL (what TrackInfo.url carries for this source).
_track_metadata_cache: dict[str, dict] = {}


class SpotifySource(Source):
    name = "spotify"

    def matches(self, url: str) -> bool:
        return "open.spotify.com" in url or url.startswith("spotify:")

    def fetch_info(self, url: str) -> InfoResponse:
        match = _URL_RE.search(url)
        if not match:
            raise ValueError(
                "Unrecognised Spotify URL. Paste a track, album, or playlist link."
            )
        kind, spotify_id = match.group(1), match.group(2)

        try:
            if kind == "track":
                return self._single(spotify_id)
            if kind == "album":
                return self._collection(
                    *spotify_client.get_album(spotify_id), kind="album"
                )
            return self._collection(
                *spotify_client.get_playlist(spotify_id), kind="playlist"
            )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Could not fetch Spotify info: {e}") from e

    def _single(self, track_id: str) -> InfoResponse:
        track = spotify_client.get_track(track_id)
        info = self._track_to_info(track)
        return InfoResponse(
            type="single",
            title=info.title,
            uploader=info.uploader,
            thumbnail=info.thumbnail,
            count=1,
            tracks=[info],
        )

    def _collection(self, title: str, thumbnail: str, tracks: list[dict], kind: str) -> InfoResponse:
        if not tracks:
            raise ValueError(f"This {kind} has no tracks, or is unavailable in your region.")

        track_infos = [self._track_to_info(t) for t in tracks]

        return InfoResponse(
            type="playlist",
            title=title,
            uploader="",
            thumbnail=thumbnail,
            count=len(track_infos),
            tracks=track_infos,
            is_true_playlist=kind == "playlist",
        )

    def _track_to_info(self, track: dict) -> TrackInfo:
        track_url = f"https://open.spotify.com/track/{track['id']}"
        info = TrackInfo(
            id=track["id"],
            title=track["title"],
            url=track_url,
            duration=fmt_duration(round(track["duration_ms"] / 1000) if track["duration_ms"] else None),
            thumbnail=track["thumbnail"],
            uploader=track["artist"],
            source=self.name,
            album=track["album"],
        )
        # Stash everything download_track needs, keyed by the same url the
        # frontend will send back in DownloadRequest — avoids re-fetching the
        # Spotify embed page per track at download time.
        _track_metadata_cache[track_url] = {
            "artist": track["artist"],
            "album": track["album"],
            "thumbnail": track["thumbnail"],
        }
        return info

    def download_track(
        self,
        url: str,
        title: str,
        music_dir: str,
        progress_hook,
        pp_hook,
    ) -> str | None:
        meta = _track_metadata_cache.get(url, {})
        artist = meta.get("artist", "")
        # Use only the primary (first) artist for the search query — a full
        # "Artist A, Artist B, Artist C" string dilutes the match quality on
        # multi-artist collabs, even though the full string is still used
        # for the artist tag itself (see overrides below).
        primary_artist = artist.split(",")[0].strip()
        query = f"{primary_artist} {title}".strip() if primary_artist else title

        overrides = {
            "artist": artist,
            "album": meta.get("album", ""),
            # Without album_artist, media libraries (iTunes/Music.app
            # confirmed) group by (album, artist) instead of just album —
            # so a "Graduation" track with a guest feature (artist="Kanye
            # West, Chris Martin") splits into a separate album tile from
            # one without a feature (artist="Kanye West"). album_artist
            # fixes the grouping key regardless of per-track guest features.
            "album_artist": primary_artist,
            # Spotify's embed pages don't expose genre, and letting it fall
            # through to YouTube's generic categories=["Music"] tag is worse
            # than no genre at all — explicitly clear it instead.
            "genre": None,
        }

        return download_with_overrides(
            youtube_music_search_url(query),
            music_dir,
            progress_hook,
            pp_hook,
            overrides=overrides,
            thumbnail_url=meta.get("thumbnail") or None,
            expected_title=title,
        )
