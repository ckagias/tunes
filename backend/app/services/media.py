"""Stateless helpers for URL/text normalization, cover-art fetching, and zip/playlist building."""

import os
import urllib.request
import zipfile


def normalise_url(url: str) -> str:
    return url.strip()


def fmt_duration(seconds) -> str:
    if not seconds:
        return ""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fetch_cover(thumbnail_url: str, dest_path: str) -> bool:
    """Download a thumbnail image to dest_path. Returns True on success."""
    if not thumbnail_url:
        return False
    try:
        req = urllib.request.Request(
            thumbnail_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False


def cover_extension(thumbnail_url: str) -> str:
    if ".png" in thumbnail_url:
        return "png"
    if ".webp" in thumbnail_url:
        return "webp"
    return "jpg"


def build_zip(music_dir: str, session_dir: str, zip_path: str) -> None:
    """Zip music_dir's contents (relative to session_dir) into zip_path."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(music_dir):
            for fname in sorted(files):
                abs_path = os.path.join(root, fname)
                arc_name = os.path.relpath(abs_path, session_dir)
                zf.write(abs_path, arc_name)


def build_m3u8(
    files: dict[str, str], urls: list[str], titles: dict[str, str], music_dir: str, playlist_name: str
) -> None:
    """Write "<playlist_name>.m3u8" into music_dir, listing downloaded tracks in playlist order.
    Duration is omitted (-1) — players read it from the file's own tags instead."""
    lines = ["#EXTM3U"]
    for url in urls:
        path = files.get(url)
        if not path or not os.path.isfile(path):
            continue  # skip tracks that errored out — nothing to reference
        title = titles.get(url, os.path.splitext(os.path.basename(path))[0])
        lines.append(f"#EXTINF:-1,{title}")
        lines.append(os.path.basename(path))

    if len(lines) == 1:
        return  # nothing downloaded successfully — no point writing an empty playlist

    m3u8_path = os.path.join(music_dir, f"{playlist_name}.m3u8")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
