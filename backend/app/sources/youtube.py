"""
YouTube source — the only implemented source for now (Spotify/SoundCloud
were tried and rolled back; revisit them later, see README roadmap).

Ports the /api/info and download logic from the original Flask app (app.py)
with no behavior changes: same yt-dlp options, same single-vs-playlist
branching, same tagging postprocessor chain.
"""

import os

import yt_dlp
import yt_dlp.utils

from app.models import InfoResponse, TrackInfo
from app.services.media import fmt_duration
from app.services.ydl_opts import download_ydl_opts, info_ydl_opts
from app.sources.base import Source


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

        if "entries" in info:
            return self._playlist_info(info)
        return self._single_info(info, url)

    def _playlist_info(self, info: dict) -> InfoResponse:
        playlist_thumbnail = info.get("thumbnail") or ""
        first_entry_thumb = ""
        entries = info.get("entries") or []
        for entry in entries:
            if entry and entry.get("thumbnail"):
                first_entry_thumb = entry["thumbnail"]
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
                    thumbnail=entry.get("thumbnail") or "",
                    uploader=entry.get("uploader") or entry.get("channel") or "",
                    source=self.name,
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

    def _single_info(self, info: dict, url: str) -> InfoResponse:
        vid_id = info.get("id", "")
        track = TrackInfo(
            id=vid_id,
            title=info.get("title") or vid_id,
            url=url,
            duration=fmt_duration(info.get("duration")),
            thumbnail=info.get("thumbnail") or "",
            uploader=info.get("uploader") or info.get("channel") or "",
            source=self.name,
        )
        return InfoResponse(
            type="single",
            title=info.get("title") or vid_id,
            thumbnail=info.get("thumbnail") or "",
            count=1,
            tracks=[track],
        )

    def download_track(
        self,
        url: str,
        title: str,
        music_dir: str,
        progress_hook,
        pp_hook,
    ) -> str | None:
        captured_path: list[str] = []

        def wrapped_pp_hook(d):
            if d.get("status") == "finished":
                fp = d.get("info_dict", {}).get("filepath") or d.get("filepath", "")
                if fp and fp.endswith(".mp3") and os.path.isfile(fp):
                    captured_path.clear()
                    captured_path.append(fp)
            pp_hook(d)

        ydl_opts = download_ydl_opts(music_dir, progress_hook, wrapped_pp_hook)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if captured_path:
            return captured_path[0]

        # Fall back to scanning music_dir for a new .mp3 (mirrors original app.py behavior).
        for fname in os.listdir(music_dir):
            if fname.endswith(".mp3"):
                candidate = os.path.join(music_dir, fname)
                if os.path.isfile(candidate):
                    return candidate
        return None


def sanitize_filename(name: str) -> str:
    return yt_dlp.utils.sanitize_filename(name, is_id=False)
