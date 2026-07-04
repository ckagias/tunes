"""YouTube source: /api/info and download logic. SpotifySource also delegates
download_track() here, resolving a matched YouTube Music track instead."""

import os
import re
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
import yt_dlp.utils

from app.models import InfoResponse, TrackInfo
from app.services.media import fmt_duration
from app.services.ydl_opts import (
    DEFAULT_AUDIO_QUALITY,
    base_ydl_opts,
    download_ydl_opts,
    info_ydl_opts,
)
from app.sources.base import Source

MIN_AUDIO_QUALITY = 64
MAX_AUDIO_QUALITY = 320

# Bounded worker pool for per-entry uploader resolution — I/O bound, mirrors jobs.MAX_CONCURRENT_DOWNLOADS.
_UPLOADER_FETCH_WORKERS = 8


def info_response_from_ytdlp(info: dict, url: str, source_name: str) -> InfoResponse:
    """Build an InfoResponse/TrackInfo tree from a yt-dlp info dict."""
    if "entries" in info:
        return _playlist_info(info, url, source_name)
    return _single_info(info, url, source_name)


def _is_youtube_music_album(url: str) -> bool:
    """YT Music album playlists always use a list=OLAK5uy_... id, unlike real playlists (PL...) or mixes (RD...)."""
    query = urllib.parse.urlparse(url).query
    list_id = urllib.parse.parse_qs(query).get("list", [""])[0]
    return list_id.startswith("OLAK5uy_")


def _entry_thumbnail(entry: dict) -> str:
    """Best thumbnail for a flat-playlist entry — extract_flat entries never set `thumbnail`, only `thumbnails`."""
    if entry.get("thumbnail"):
        return entry["thumbnail"]
    thumbs = entry.get("thumbnails") or []
    if not thumbs:
        return ""
    best = max(thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0))
    return best.get("url", "")


def _resolve_uploader(vid_url: str) -> str:
    """Best-effort fetch of a single video's real uploader/channel name."""
    try:
        with yt_dlp.YoutubeDL({**base_ydl_opts(), "extract_flat": False, "skip_download": True}) as ydl:
            full = ydl.extract_info(vid_url, download=False)
        if not full:
            return ""
        return full.get("uploader") or full.get("channel") or ""
    except Exception:
        return ""


def _playlist_info(info: dict, url: str, source_name: str) -> InfoResponse:
    entries = info.get("entries") or []

    valid_entries = []
    vid_urls: list[str] = []
    thumbnails: list[str] = []
    for entry in entries:
        if not entry:
            continue
        vid_id = entry.get("id") or entry.get("url", "")
        vid_url = entry.get("url") or (
            f"https://www.youtube.com/watch?v={vid_id}" if vid_id else None
        )
        if not vid_url:
            continue
        valid_entries.append((entry, vid_id, vid_url))
        vid_urls.append(vid_url)
        thumbnails.append(_entry_thumbnail(entry))

    # extract_flat never populates uploader/channel, so each entry needs a full resolve.
    with ThreadPoolExecutor(max_workers=_UPLOADER_FETCH_WORKERS) as pool:
        uploaders = list(pool.map(_resolve_uploader, vid_urls))

    tracks: list[TrackInfo] = [
        TrackInfo(
            id=vid_id,
            title=entry.get("title") or vid_id,
            url=vid_url,
            duration=fmt_duration(entry.get("duration")),
            thumbnail=thumbnails[i],
            uploader=uploaders[i],
            source=source_name,
        )
        for i, (entry, vid_id, vid_url) in enumerate(valid_entries)
    ]

    playlist_thumbnail = info.get("thumbnail") or next((t for t in thumbnails if t), "")

    return InfoResponse(
        type="playlist",
        title=info.get("title", "Playlist"),
        uploader=info.get("uploader") or info.get("channel") or "",
        thumbnail=playlist_thumbnail,
        count=len(tracks),
        tracks=tracks,
        is_true_playlist=not _is_youtube_music_album(url),
    )


def _single_info(info: dict, url: str, source_name: str) -> InfoResponse:
    vid_id = info.get("id", "")
    track = TrackInfo(
        id=vid_id,
        title=info.get("title") or vid_id,
        url=url,
        duration=fmt_duration(info.get("duration")),
        thumbnail=info.get("thumbnail") or "",
        uploader=info.get("uploader") or info.get("channel") or "",
        source=source_name,
    )
    return InfoResponse(
        type="single",
        title=info.get("title") or vid_id,
        thumbnail=info.get("thumbnail") or "",
        count=1,
        tracks=[track],
    )


# Flat search results to consider before giving up on a track match.
SEARCH_CANDIDATES = 10


def youtube_music_search_url(query: str) -> str:
    """Build a music.youtube.com/search URL — yt-dlp's ytmsearch: prefix no longer resolves."""
    return f"https://music.youtube.com/search?q={urllib.parse.quote(query)}"


_FEATURE_CREDIT_RE = re.compile(
    r"[\(\[][^)\]]*\b(feat|featuring|ft)\b[^)\]]*[\)\]]|\b(feat|featuring|ft)\.?\s.*$",
    re.IGNORECASE,
)


def _normalize_title(title: str) -> str:
    """Strip feature-credit annotations, lowercase, and drop punctuation for loose comparison."""
    base = _FEATURE_CREDIT_RE.sub("", title)
    return "".join(ch for ch in base.lower() if ch.isalnum())


_UNDESIRABLE_VARIANT_RE = re.compile(
    r"\b(instrumental|karaoke|lyrics?|acoustic|reaction|sped\s*up|slowed|nightcore|8d\s*audio)\b",
    re.IGNORECASE,
)


def _is_undesirable_variant(candidate_title: str) -> bool:
    """True for instrumental/karaoke/etc. uploads that pass the title check but aren't the real track."""
    return bool(_UNDESIRABLE_VARIANT_RE.search(candidate_title))


# Marks a title as a distinct, differently-timed version (e.g. "Song (Interlude)" vs "Song") rather than decoration.
_VARIANT_MARKER_RE = re.compile(
    r"\b(interlude|intro|outro|skit|reprise|prelude)\b", re.IGNORECASE
)


def _title_plausibly_matches(candidate_title: str, expected_title: str) -> bool:
    """Loose substring match after normalization, but require matching variant markers (interlude/intro/etc.)."""
    if not expected_title:
        return True
    norm_candidate = _normalize_title(candidate_title)
    norm_expected = _normalize_title(expected_title)
    if not norm_expected:
        return True

    expected_markers = set(m.lower() for m in _VARIANT_MARKER_RE.findall(expected_title))
    if expected_markers:
        candidate_markers = set(m.lower() for m in _VARIANT_MARKER_RE.findall(candidate_title))
        if not expected_markers & candidate_markers:
            return False

    return norm_expected in norm_candidate or norm_candidate in norm_expected


def resolve_best_search_result(search_url: str, expected_title: str = "") -> dict | None:
    """Probe the top search candidates in order, preferring one with a plausible title match and an album tag."""
    flat_opts = {**base_ydl_opts(), "extract_flat": True, "playlist_items": f"1-{SEARCH_CANDIDATES}"}
    try:
        with yt_dlp.YoutubeDL(flat_opts) as ydl:
            flat = ydl.extract_info(search_url, download=False)
    except Exception:
        return None
    if flat is None:
        return None

    candidates = [
        e for e in (flat.get("entries") or [])
        if e
        and e.get("id")
        # Skip album/artist browse pages (ie_key "YoutubeTab") mixed into search results — not real videos.
        and e.get("ie_key") != "YoutubeTab"
        and _title_plausibly_matches(e.get("title") or "", expected_title)
    ]
    if not candidates:
        return None

    # Deprioritize (not drop) instrumental/karaoke/etc. variants — still better than no match.
    candidates.sort(key=lambda e: _is_undesirable_variant(e.get("title") or ""))

    first_playable: dict | None = None
    probe_opts = {**base_ydl_opts()}
    for entry in candidates:
        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
        try:
            with yt_dlp.YoutubeDL(probe_opts) as ydl:
                full = ydl.extract_info(video_url, download=False)
        except Exception:
            continue
        if full is None:
            continue
        if first_playable is None:
            first_playable = full
        if full.get("album"):
            return full

    return first_playable


def resolve_download_target(url_or_search: str, expected_title: str = "") -> dict | None:
    """Resolve to a single concrete video info dict, shared by quality-probing and the actual download."""
    if "music.youtube.com/search" in url_or_search:
        return resolve_best_search_result(url_or_search, expected_title)

    try:
        probe_opts = {**base_ydl_opts(), "format": "bestaudio/best"}
        with yt_dlp.YoutubeDL(probe_opts) as ydl:
            info = ydl.extract_info(url_or_search, download=False)
    except Exception:
        return None
    if info is None:
        return None
    if "entries" in info:
        entries = info.get("entries") or []
        return entries[0] if entries and entries[0] else None
    return info


def resolve_target_quality(info: dict) -> int:
    """Pick the ffmpeg re-encode target from the source's actual bitrate instead of a fixed value."""
    abr = info.get("abr") if info else None
    if abr:
        return max(MIN_AUDIO_QUALITY, min(round(abr), MAX_AUDIO_QUALITY))
    return DEFAULT_AUDIO_QUALITY


def download_with_overrides(
    url_or_search: str,
    music_dir: str,
    progress_hook,
    pp_hook,
    overrides: dict | None = None,
    thumbnail_url: str | None = None,
    expected_title: str = "",
) -> str | None:
    """
    Download+tag a track, optionally overriding tag fields and/or cover art
    before the postprocessors run (used by SpotifySource for real metadata).
    Mutates the resolved info dict and feeds it through process_ie_result()
    so FFmpegMetadata picks up the overrides. `url_or_search` can be a
    direct URL, a ytsearch1: string, or a music.youtube.com/search URL.
    """
    overrides = overrides or {}
    captured_path: list[str] = []

    def wrapped_pp_hook(d):
        if d.get("status") == "finished":
            fp = d.get("info_dict", {}).get("filepath") or d.get("filepath", "")
            if fp and fp.endswith(".mp3") and os.path.isfile(fp):
                captured_path.clear()
                captured_path.append(fp)
        pp_hook(d)

    info = resolve_download_target(url_or_search, expected_title)
    if info is None:
        return None

    quality = resolve_target_quality(info)
    ydl_opts = download_ydl_opts(music_dir, progress_hook, wrapped_pp_hook, quality=quality)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for key, value in overrides.items():
            if value:
                info[key] = value
            elif value is None and key == "genre":
                # Clear genre's fallback chain too, or YouTube's generic categories=['Music'] leaks through.
                for k in ("genre", "genres", "categories", "tags"):
                    info.pop(k, None)
        if thumbnail_url:
            info["thumbnails"] = [{"url": thumbnail_url, "id": "override"}]
            info["thumbnail"] = thumbnail_url
        ydl.process_ie_result(info, download=True)

    if captured_path:
        return _strip_id_suffix(captured_path[0])

    # Fall back to scanning music_dir for a new .mp3.
    for fname in os.listdir(music_dir):
        if fname.endswith(".mp3"):
            candidate = os.path.join(music_dir, fname)
            if os.path.isfile(candidate):
                return _strip_id_suffix(candidate)
    return None


_ID_SUFFIX_RE = re.compile(r" \[[^\[\]]+\](\.\w+)$")

# Guards the rename below against two concurrent same-titled downloads racing on the same clean filename.
_rename_lock = threading.Lock()


def _strip_id_suffix(path: str) -> str:
    """Rename "Title [video_id].mp3" back to "Title.mp3", falling back to a numeric suffix on collision."""
    match = _ID_SUFFIX_RE.search(path)
    if not match:
        return path
    clean = path[: match.start()] + match.group(1)
    base, ext = os.path.splitext(clean)
    with _rename_lock:
        if not os.path.exists(clean):
            os.rename(path, clean)
            return clean
        n = 2
        while os.path.exists(f"{base} ({n}){ext}"):
            n += 1
        numbered = f"{base} ({n}){ext}"
        os.rename(path, numbered)
        return numbered


class YouTubeSource(Source):
    name = "youtube"

    def matches(self, url: str) -> bool:
        return "youtube.com" in url or "youtu.be" in url

    def fetch_info(self, url: str) -> InfoResponse:
        with yt_dlp.YoutubeDL(info_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)

        if info is None:
            raise ValueError(
                "Could not fetch info. The video may be unavailable, private, or age-restricted."
            )

        return info_response_from_ytdlp(info, url, self.name)

    def download_track(
        self,
        url: str,
        title: str,
        music_dir: str,
        progress_hook,
        pp_hook,
    ) -> str | None:
        return download_with_overrides(url, music_dir, progress_hook, pp_hook)


def sanitize_filename(name: str) -> str:
    return yt_dlp.utils.sanitize_filename(name, is_id=False)
