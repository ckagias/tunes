"""
YouTube source. Ports the /api/info and download logic from the original
Flask app (app.py) with no behavior changes: same yt-dlp options, same
single-vs-playlist branching, same tagging postprocessor chain.

SpotifySource builds its own InfoResponse/TrackInfo from Spotify's real
metadata (see sources/spotify.py), but delegates download_track() straight
to download_with_overrides() below — so a Spotify link is really just
"find the equivalent YouTube Music track, then act exactly like that
YouTube URL was pasted directly, with Spotify's real tags/art embedded
instead of YouTube's own."
"""

import os
import re
import urllib.parse

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


def info_response_from_ytdlp(info: dict, url: str, source_name: str) -> InfoResponse:
    """
    Build an InfoResponse/TrackInfo tree from a yt-dlp info dict for a
    direct YouTube URL. `source_name` is stamped onto each TrackInfo so the
    frontend can tell which link type the user actually pasted.
    """
    if "entries" in info:
        return _playlist_info(info, source_name)
    return _single_info(info, url, source_name)


def _entry_thumbnail(entry: dict) -> str:
    """
    Best thumbnail URL for a flat-playlist entry. info_ydl_opts() uses
    extract_flat="in_playlist", under which yt-dlp never populates the plain
    `thumbnail` field on playlist/album entries (confirmed empirically: it's
    always None) — only the `thumbnails` list (sized variants, no field
    guaranteed pre-sorted) is populated. Falls back to `thumbnail` anyway in
    case a future yt-dlp version (or a non-flat entry) does set it directly.
    """
    if entry.get("thumbnail"):
        return entry["thumbnail"]
    thumbs = entry.get("thumbnails") or []
    if not thumbs:
        return ""
    best = max(thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0))
    return best.get("url", "")


def _playlist_info(info: dict, source_name: str) -> InfoResponse:
    playlist_thumbnail = info.get("thumbnail") or ""
    first_entry_thumb = ""
    entries = info.get("entries") or []
    for entry in entries:
        if entry and _entry_thumbnail(entry):
            first_entry_thumb = _entry_thumbnail(entry)
            break

    tracks: list[TrackInfo] = []
    for entry in entries:
        if not entry:
            continue
        vid_id = entry.get("id") or entry.get("url", "")
        vid_url = entry.get("url") or (
            f"https://www.youtube.com/watch?v={vid_id}" if vid_id else None
        )
        if not vid_url:
            continue
        tracks.append(
            TrackInfo(
                id=vid_id,
                title=entry.get("title") or vid_id,
                url=vid_url,
                duration=fmt_duration(entry.get("duration")),
                thumbnail=_entry_thumbnail(entry),
                uploader=entry.get("uploader") or entry.get("channel") or "",
                source=source_name,
            )
        )

    return InfoResponse(
        type="playlist",
        title=info.get("title", "Playlist"),
        uploader=info.get("uploader") or info.get("channel") or "",
        thumbnail=playlist_thumbnail or first_entry_thumb,
        count=len(tracks),
        tracks=tracks,
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


# How many flat search results to consider before giving up on a track.
# 5 missed real matches in practice — e.g. "On Sight" only appeared at
# position 6-7 behind several same-artist decoys (Lift Yourself, Black
# Skinhead, ...) that the title filter correctly rejected, leaving no valid
# candidate. 10 costs a bit more (each rejected/failing candidate is a
# wasted flat-list entry, but only candidates that pass the title filter
# get a full probe) in exchange for meaningfully fewer false "no match"
# outcomes.
SEARCH_CANDIDATES = 10


def youtube_music_search_url(query: str) -> str:
    """
    Build a music.youtube.com/search URL for `query`. yt-dlp's older
    `ytmsearch:` prefix no longer resolves in current versions — the
    YouTube Music search extractor now only matches this URL form
    (`youtube:music:search_url`, no _SEARCH_KEY).
    """
    return f"https://music.youtube.com/search?q={urllib.parse.quote(query)}"


_FEATURE_CREDIT_RE = re.compile(
    r"[\(\[][^)\]]*\b(feat|featuring|ft)\b[^)\]]*[\)\]]|\b(feat|featuring|ft)\.?\s.*$",
    re.IGNORECASE,
)


def _normalize_title(title: str) -> str:
    """
    Strip feature-credit annotations (parenthetical or trailing "feat./ft."
    text — these vary in wording between Spotify and YouTube titles for the
    literal same song, e.g. "(ft. Snoop Doggy Dogg)" vs "(feat. Snoop
    Dogg)"), then lowercase and strip remaining punctuation/whitespace for
    loose comparison.
    """
    base = _FEATURE_CREDIT_RE.sub("", title)
    return "".join(ch for ch in base.lower() if ch.isalnum())


_UNDESIRABLE_VARIANT_RE = re.compile(
    r"\b(instrumental|karaoke|lyrics?|acoustic|reaction|sped\s*up|slowed|nightcore|8d\s*audio)\b",
    re.IGNORECASE,
)


def _is_undesirable_variant(candidate_title: str) -> bool:
    """
    Reject titles that pass the plain title-match check (the extra word is
    often just appended, e.g. "On Sight (Instrumental)" still contains "On
    Sight") but are clearly not the actual song a listener wants. Seen in
    practice: YouTube Music search ranking an instrumental-only upload above
    the real vocal track for some queries, non-deterministically between
    calls — the album-tag preference alone doesn't protect against this
    since these variant uploads sometimes carry real album metadata too.
    """
    return bool(_UNDESIRABLE_VARIANT_RE.search(candidate_title))


def _title_plausibly_matches(candidate_title: str, expected_title: str) -> bool:
    """
    Reject candidates whose title has nothing to do with what we searched
    for. This is deliberately loose (substring match after stripping
    feature credits, punctuation, and case) since YouTube titles commonly
    add "(Official Video)", differently-worded feat. credits, remix tags,
    etc. — but it catches the real failure mode seen in practice: YouTube
    Music's search returning a totally different song by the same artist as
    the top (or a later) "result", which a metadata-only check (e.g. "does
    it have an album tag") would happily accept since the wrong song can
    have perfectly real album metadata too.
    """
    if not expected_title:
        return True
    norm_candidate = _normalize_title(candidate_title)
    norm_expected = _normalize_title(expected_title)
    if not norm_expected:
        return True
    return norm_expected in norm_candidate or norm_candidate in norm_expected


def resolve_best_search_result(search_url: str, expected_title: str = "") -> dict | None:
    """
    The plain top-1 search result is sometimes a bad match: an
    age/region-restricted upload that fails outright, a fan upload with no
    Content-ID album tag when an official one exists further down the
    results, or — seen in practice — an entirely different song by the same
    artist that YouTube Music's search ranked first. Pull the top few flat
    results, drop any whose title doesn't plausibly match `expected_title`
    (the track title actually being searched for), fully probe the rest in
    order, and return the first one that both resolves successfully AND has
    an album tag — falling back to the first one that merely resolves if
    none do. Returns None if every candidate fails or none has a plausible
    title match.
    """
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
        # YouTube Music search results sometimes include an album/artist
        # "browse" page (ie_key "YoutubeTab", id prefixed "MPREb_...") mixed
        # in with actual song results. It isn't a video at all, so probing
        # it as https://www.youtube.com/watch?v=MPREb_... always fails with
        # "Video unavailable" — filter it out here instead of wasting a
        # probe (and a misleading error) on something that was never a song.
        and e.get("ie_key") != "YoutubeTab"
        and _title_plausibly_matches(e.get("title") or "", expected_title)
    ]
    if not candidates:
        return None

    # Push instrumental/karaoke/lyrics-video/etc. variants to the back
    # (stable sort keeps each group's original relative order) rather than
    # dropping them outright — YouTube Music's ranking is non-deterministic
    # enough that one of these can otherwise outrank the real vocal track,
    # and an undesirable variant still beats no match at all.
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
    """
    Resolve `url_or_search` to a single concrete video info dict — the one
    piece of resolution logic shared by both quality-probing and the actual
    download, so they never disagree about which video was picked.

    For a music.youtube.com/search URL, delegates to
    resolve_best_search_result() (skips age-restricted/unplayable results,
    rejects candidates that don't plausibly match `expected_title`, prefers
    one with a real album tag). For a direct URL or a ytsearch1: string,
    just extracts it directly (single result, no candidates to pick
    between).
    """
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
    """
    Pick the ffmpeg re-encode target from the resolved video's actual
    bitrate, so it matches the source instead of a fixed high value.
    Re-encoding above the source's real bitrate doesn't recover any detail —
    it just produces a larger file for no gain. Falls back to
    DEFAULT_AUDIO_QUALITY if the bitrate isn't present on `info`.
    """
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
    Download+tag a track, optionally overriding tag fields (album, genre,
    artist, ...) and/or the cover art before the tagging postprocessors run —
    used by SpotifySource to inject its real metadata instead of whatever
    (if anything) YouTube itself provides for that field.

    Mechanism (verified): FFmpegMetadata reads tag values straight out of
    yt-dlp's info dict at postprocessing time, so extracting the info dict
    ourselves, mutating it, then handing it to process_ie_result(download=True)
    (instead of the simpler ydl.download([url])) makes the postprocessor
    chain embed our overridden values. With overrides=None/{} and
    thumbnail_url=None this is byte-for-byte the same download path as
    before — only keys actually present in `overrides` are changed, and the
    thumbnail is only swapped if thumbnail_url is given (verified: replacing
    info['thumbnails']/info['thumbnail'] with a real https URL lets yt-dlp's
    own writethumbnail/EmbedThumbnail machinery fetch and embed it normally —
    confirmed byte-identical to the source image via md5sum).

    `url_or_search` can be a direct URL, a ytsearch1: search string, or a
    music.youtube.com/search?q=... URL. For the last case, the naive top
    search result is sometimes a bad match (age-restricted, missing album
    tags an official upload further down has, or — seen in practice — a
    totally different song by the same artist) — see
    resolve_best_search_result(), which is used here instead of blindly
    taking result #1. `expected_title` (the real track title being searched
    for) lets it reject wrong-song candidates; pass it whenever
    `url_or_search` is a search URL.
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
                # FFmpegMetadata falls back through genre -> genres ->
                # categories -> tags (see its `add('genre', (...))` call),
                # so YouTube's generic categories=['Music'] silently becomes
                # the genre tag unless all of these are cleared too. Used
                # when a source knows it has no real genre and that generic
                # fallback would be worse than no tag at all.
                for k in ("genre", "genres", "categories", "tags"):
                    info.pop(k, None)
        if thumbnail_url:
            info["thumbnails"] = [{"url": thumbnail_url, "id": "override"}]
            info["thumbnail"] = thumbnail_url
        ydl.process_ie_result(info, download=True)

    if captured_path:
        return captured_path[0]

    # Fall back to scanning music_dir for a new .mp3 (mirrors original app.py behavior).
    for fname in os.listdir(music_dir):
        if fname.endswith(".mp3"):
            candidate = os.path.join(music_dir, fname)
            if os.path.isfile(candidate):
                return candidate
    return None


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
