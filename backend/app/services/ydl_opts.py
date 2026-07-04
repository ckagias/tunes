"""yt-dlp option builders — the postprocessor chain here tags/embeds art into the final MP3."""

import os

# Fallback re-encode bitrate (kbps) when the source's actual bitrate is unknown.
DEFAULT_AUDIO_QUALITY = 192


def base_ydl_opts() -> dict:
    """Shared yt-dlp options. player_client lists fallback clients since "web" often needs a PO token."""
    return {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
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
    """Extract to MP3 at `quality` kbps, embed metadata, embed cover art."""
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
    """Options for a single-track download. outtmpl embeds the video id to avoid same-title collisions."""
    return {
        **base_ydl_opts(),
        "format": "bestaudio/best",
        "writethumbnail": True,
        "postprocessors": build_audio_postprocessors(quality=quality),
        "outtmpl": os.path.join(music_dir, "%(title)s [%(id)s].%(ext)s"),
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [pp_hook],
    }
