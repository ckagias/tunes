"""Spotify source: tags/art come from Spotify's embed pages, audio comes from a matched YouTube Music track."""

import re

from app.models import InfoResponse, TrackInfo
from app.services import spotify_client
from app.services.media import fmt_duration
from app.sources.base import Source
from app.sources.youtube import download_with_overrides, youtube_music_search_url

_URL_RE = re.compile(r"open\.spotify\.com/(track|album|playlist)/([A-Za-z0-9]+)")

# Populated by fetch_info, consumed by download_track — avoids re-fetching per track. Keyed by Spotify track URL.
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
        # Stash what download_track needs, keyed by the url DownloadRequest will send back.
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
        # Primary artist only for the search query — a full "A, B, C" string dilutes match quality.
        primary_artist = artist.split(",")[0].strip()
        query = f"{primary_artist} {title}".strip() if primary_artist else title

        overrides = {
            "artist": artist,
            "album": meta.get("album", ""),
            # Without this, libraries group by (album, artist) — a featured guest would split the album tile.
            "album_artist": primary_artist,
            # No genre data from Spotify's embed pages — clear it rather than inherit YouTube's generic tag.
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
