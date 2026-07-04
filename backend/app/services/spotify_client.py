"""Spotify metadata via public embed pages (open.spotify.com/embed/...) — no OAuth or API calls needed.

Parses the __NEXT_DATA__ JSON blob Spotify server-renders into that page. Fragile to a Spotify redesign;
callers should treat failures as user-facing errors, not crashes.
"""

import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# Bounded pool for concurrent per-track cover art fetches in get_playlist — I/O bound, mirrors jobs.MAX_CONCURRENT_DOWNLOADS.
_THUMBNAIL_FETCH_WORKERS = 8

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

_NEXT_DATA_RE = re.compile(
    r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)


def _fetch_entity(kind: str, spotify_id: str) -> dict:
    """GET the embed page for a track/album/playlist and return its `entity` JSON."""
    url = f"https://open.spotify.com/embed/{kind}/{spotify_id}"
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Could not fetch Spotify embed page (HTTP {e.code}). "
            "The link may be invalid, private, or Spotify may have changed this page."
        ) from e

    match = _NEXT_DATA_RE.search(html)
    if not match:
        raise RuntimeError(
            "Could not parse Spotify's embed page — it may have changed format."
        )

    data = json.loads(match.group(1))
    entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity")
    if not entity:
        raise RuntimeError("Spotify embed page did not contain track data.")
    return entity


def _best_image(images: list) -> str:
    if not images:
        return ""
    # Track/album covers use maxWidth/maxHeight; playlist covers use width/height.
    def size(i: dict) -> int:
        return i.get("maxWidth") or i.get("width") or i.get("maxHeight") or i.get("height") or 0

    best = max(images, key=size)
    return best.get("url", "")


def _artists_str(artists: list) -> str:
    return ", ".join(a.get("name", "") for a in (artists or []) if a.get("name"))


def get_track(track_id: str) -> dict:
    """A single track's metadata (title, artist, cover, duration). No album name — embed pages don't expose it for standalone tracks."""
    entity = _fetch_entity("track", track_id)
    images = (entity.get("visualIdentity") or {}).get("image", [])
    return {
        "id": entity.get("id") or track_id,
        "title": entity.get("name") or entity.get("title") or "Unknown",
        "artist": _artists_str(entity.get("artists")),
        "album": "",
        "duration_ms": entity.get("duration") or 0,
        "thumbnail": _best_image(images),
    }


def _track_from_tracklist_item(item: dict, album: str = "", thumbnail: str = "") -> dict:
    # subtitle uses non-breaking spaces after commas — normalize to match _artists_str's format.
    artist = (item.get("subtitle") or "").replace("\xa0", " ")
    return {
        "id": (item.get("uri") or "").rsplit(":", 1)[-1],
        "title": item.get("title") or "Unknown",
        "artist": artist,
        "album": album,
        "duration_ms": item.get("duration") or 0,
        "thumbnail": thumbnail,
    }


def _track_thumbnail(track_id: str) -> str:
    """Best-effort fetch of a single track's own cover art."""
    try:
        return get_track(track_id)["thumbnail"]
    except Exception:
        return ""


def get_album(album_id: str) -> tuple[str, str, list[dict]]:
    """Returns (album_title, album_thumbnail, [track dicts]) for every track on the album."""
    entity = _fetch_entity("album", album_id)
    title = entity.get("name") or "Album"
    thumb = _best_image((entity.get("visualIdentity") or {}).get("image", []))
    # Every track on an album shares the same cover — no per-track lookup needed, unlike playlists.
    tracks = [
        _track_from_tracklist_item(item, album=title, thumbnail=thumb)
        for item in entity.get("trackList") or []
    ]
    return title, thumb, tracks


def get_playlist(playlist_id: str) -> tuple[str, str, list[dict]]:
    """Returns (playlist_title, playlist_thumbnail, [track dicts]) for every track on the playlist."""
    entity = _fetch_entity("playlist", playlist_id)
    title = entity.get("name") or "Playlist"
    thumb = _best_image((entity.get("coverArt") or {}).get("sources", []))
    items = entity.get("trackList") or []

    # Playlist items don't carry their own cover art — fetch each track's real art concurrently,
    # falling back to the playlist's own cover if a fetch fails.
    track_ids = [(item.get("uri") or "").rsplit(":", 1)[-1] for item in items]
    with ThreadPoolExecutor(max_workers=_THUMBNAIL_FETCH_WORKERS) as pool:
        thumbnails = list(pool.map(_track_thumbnail, track_ids))

    tracks = [
        _track_from_tracklist_item(item, thumbnail=thumbnails[i] or thumb)
        for i, item in enumerate(items)
    ]
    return title, thumb, tracks
