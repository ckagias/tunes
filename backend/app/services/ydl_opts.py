"""
yt-dlp option builders. This is the core of the product: the postprocessor
chain here is what turns a raw stream into an Apple-Music-ready MP3 with
embedded title/artist/album tags and embedded cover art, so files can be
dragged straight into a music library with no manual editing.

Ported from the original Flask app (app.py) with no behavior changes.
"""

import os

from app.config import settings

# Fallback target bitrate (kbps) when a source's actual bitrate can't be
# determined. Used instead of always re-encoding to a fixed high bitrate
# like 320 — most YouTube audio sources are well below that, so forcing 320
# just inflates file size without recovering any real audio detail.
DEFAULT_AUDIO_QUALITY = 192


def base_ydl_opts() -> dict:
    """
    Shared yt-dlp options for both info lookups and downloads.

    player_client lists multiple YouTube clients in fallback order. The
    "web" client increasingly requires a JS runtime for signature decryption
    and/or a proof-of-origin (PO) token; "android"/"ios" are more resilient
    without either, at the cost of occasionally missing some formats. Using
    several gives yt-dlp room to fall back automatically.

    For heavier use (many requests, hitting bot-detection often), install the
    optional `bgutil-ytdlp-pot-provider` plugin and set BGU_POT_SERVER_HOST
    (see README "Advanced setup") — yt-dlp discovers the plugin automatically
    at runtime, no code change needed here.
    """
    return {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        # Caps any search-style URL (ytsearch:, music.youtube.com/search) to
        # its top result — irrelevant for direct video/track URLs.
        "playlist_items": "1",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "ios"],
            }
        },
    }


def info_ydl_opts() -> dict:
    """Options for metadata-only lookups (no download)."""
    return {
        **base_ydl_opts(),
        "extract_flat": "in_playlist",
        "skip_download": True,
    }


def build_audio_postprocessors(quality: int = DEFAULT_AUDIO_QUALITY) -> list[dict]:
    """
    The three-stage tagging chain:
      1. Extract audio to MP3 at `quality` kbps (should match the source's
         actual bitrate — re-encoding above it just inflates file size with
         no real quality gain, since you can't recover detail a lossy
         source never had)
      2. Embed title/artist/album/etc. metadata
      3. Embed cover art thumbnail

    This is the single source of truth for "Apple-Music-ready" output —
    reuse this everywhere audio is downloaded, regardless of source.

    Values above 10 are passed straight through to ffmpeg as an exact
    target kbps (`-b:a {quality}k`) — see yt-dlp's
    FFmpegExtractAudioPP._quality_args.
    """
    return [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": str(quality),
        },
        {
            "key": "FFmpegMetadata",
            "add_metadata": True,
        },
        {
            "key": "EmbedThumbnail",
            "already_have_thumbnail": False,
        },
    ]


def download_ydl_opts(
    music_dir: str, progress_hook, pp_hook, quality: int = DEFAULT_AUDIO_QUALITY
) -> dict:
    """Options for a single-track download, with hooks wired up."""
    return {
        **base_ydl_opts(),
        "format": "bestaudio/best",
        "writethumbnail": True,
        "postprocessors": build_audio_postprocessors(quality=quality),
        "outtmpl": os.path.join(music_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [pp_hook],
    }
