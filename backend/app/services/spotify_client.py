"""
Real Spotify metadata via Spotify's public embed pages — no developer
account, no OAuth, no bearer tokens, no API calls at all.

Mechanism: https://open.spotify.com/embed/{track,album,playlist}/{id} is the
page Spotify serves for embedded players (e.g. iframes on blogs). It's a
plain server-rendered Next.js page containing a <script id="__NEXT_DATA__">
tag with the full track/album/playlist JSON (title, artists, cover art,
duration, and for albums/playlists the full track list) — no auth needed at
all, just an HTTP GET.

This replaces an earlier version of this module that used Spotify's
anonymous web-player token endpoint (open.spotify.com/get_access_token) to
call api.spotify.com directly. That endpoint started returning HTTP 403 in
testing, apparently now gated in a way the embed page isn't. Embed pages
don't expose per-track genre, so genre tagging for Spotify tracks was
dropped instead of trying to resurrect it from a separate source.

CAVEAT: this depends on Spotify continuing to server-render this JSON blob
into the embed page. It could change if Spotify redesigns that page. All
functions here fail by raising, and callers (sources/spotify.py) should
translate failures into a clear user-facing error rather than crashing.
"""

import json
import re
import urllib.error
import urllib.request

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


def _track_from_tracklist_item(item: dict, album: str = "") -> dict:
    # subtitle is a raw "Artist A,\xa0Artist B" string (non-breaking spaces
    # after each comma) — normalize so it matches _artists_str's plain
    # ", "-joined format used elsewhere, and doesn't poison search queries.
    artist = (item.get("subtitle") or "").replace("\xa0", " ")
    return {
        "id": (item.get("uri") or "").rsplit(":", 1)[-1],
        "title": item.get("title") or "Unknown",
        "artist": artist,
        "album": album,
        "duration_ms": item.get("duration") or 0,
        "thumbnail": "",
    }


def get_album(album_id: str) -> tuple[str, str, list[dict]]:
    """Returns (album_title, album_thumbnail, [track dicts]) for every track on the album."""
    entity = _fetch_entity("album", album_id)
    title = entity.get("name") or "Album"
    thumb = _best_image((entity.get("visualIdentity") or {}).get("image", []))
    tracks = [
        _track_from_tracklist_item(item, album=title)
        for item in entity.get("trackList") or []
    ]
    return title, thumb, tracks


def get_playlist(playlist_id: str) -> tuple[str, str, list[dict]]:
    """Returns (playlist_title, playlist_thumbnail, [track dicts]) for every track on the playlist."""
    entity = _fetch_entity("playlist", playlist_id)
    title = entity.get("name") or "Playlist"
    thumb = _best_image((entity.get("coverArt") or {}).get("sources", []))
    tracks = [_track_from_tracklist_item(item) for item in entity.get("trackList") or []]
    return title, thumb, tracks
