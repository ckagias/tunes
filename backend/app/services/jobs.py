"""
Download job orchestration: bridges FastAPI's async world with yt-dlp's
blocking calls, and bridges the resulting progress events to an SSE stream.

Approach (see README/plan for rationale): the actual download runs in a
background thread (via run_in_executor), reporting progress into a plain
queue.Queue. The SSE route reads that same queue. This mirrors the proven
pattern from the original Flask app rather than fighting asyncio — yt-dlp's
hooks are synchronous callbacks and a thread-safe queue is the simplest
correct bridge.

Event contract (unchanged from the original app, so the frontend can consume
it identically): started, progress, converting, track_done, track_error,
zipping, zip_ready, all_done.

Tracks within a single job download concurrently (bounded worker pool, see
MAX_CONCURRENT_DOWNLOADS) rather than one at a time — most per-track time is
network I/O wait, not CPU, so this gives a roughly proportional speedup on
large playlists. This is safe because: session.queue is a stdlib
queue.Queue (thread-safe for concurrent put()); each worker writes a
different session.files[url] key, never the same key concurrently; and each
download_track() call constructs its own fresh yt-dlp instance, so there's
no shared mutable state across workers.
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from app.services import media
from app.services.sessions import Session, store
from app.sources import registry
from app.sources.youtube import sanitize_filename

MAX_CONCURRENT_DOWNLOADS = 8


def _make_hooks(q, url: str, title: str):
    def progress_hook(d):
        status = d.get("status")
        if status == "downloading":
            pct_str = d.get("_percent_str", "").strip().replace("%", "")
            try:
                pct = float(pct_str)
            except ValueError:
                pct = 0
            q.put(
                {
                    "type": "progress",
                    "url": url,
                    "title": title,
                    "percent": pct,
                    "speed": d.get("_speed_str", "").strip(),
                    "eta": d.get("_eta_str", "").strip(),
                }
            )
        elif status == "finished":
            q.put({"type": "converting", "url": url, "title": title})
        elif status == "error":
            q.put(
                {
                    "type": "track_error",
                    "url": url,
                    "title": title,
                    "message": str(d.get("error", "Unknown")),
                }
            )

    def pp_hook(d):
        # Presence kept for parity with the source interface; the concrete
        # source (e.g. YouTubeSource) wraps this to capture the final path.
        pass

    return progress_hook, pp_hook


def _download_one(
    session: Session,
    url: str,
    title: str,
    music_dir: str,
    is_playlist: bool,
) -> None:
    """Download+tag a single track and report its events. Runs on a pool worker."""
    q = session.queue
    progress_hook, pp_hook = _make_hooks(q, url, title)

    try:
        q.put({"type": "started", "url": url, "title": title})
        source = registry.resolve(url)
        final_path = source.download_track(url, title, music_dir, progress_hook, pp_hook)

        if final_path and os.path.isfile(final_path):
            session.files[url] = final_path
            if is_playlist:
                q.put({"type": "track_done", "url": url, "title": title})
            else:
                q.put(
                    {
                        "type": "track_done",
                        "url": url,
                        "title": title,
                        "filename": os.path.basename(final_path),
                        "session_id": session.session_id,
                    }
                )
        else:
            q.put(
                {
                    "type": "track_error",
                    "url": url,
                    "title": title,
                    "message": "Output file not found after conversion.",
                }
            )
    except Exception as e:
        q.put({"type": "track_error", "url": url, "title": title, "message": str(e)})


def run_download_job(
    session: Session,
    urls: list[str],
    titles: dict[str, str],
    music_dir: str,
    is_playlist: bool,
    playlist_thumbnail: str,
) -> None:
    """
    Synchronous job body — runs on a worker thread via run_in_executor.
    Mirrors the original Flask app's do_download() closely, but downloads
    tracks concurrently (bounded pool) instead of one at a time.
    """
    q = session.queue

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as pool:
        futures = [
            pool.submit(_download_one, session, url, titles.get(url, url), music_dir, is_playlist)
            for url in urls
        ]
        for future in futures:
            future.result()  # propagate any unexpected exception; also waits for completion

    if is_playlist:
        q.put({"type": "zipping", "message": "Creating archive…"})

        if playlist_thumbnail:
            ext = media.cover_extension(playlist_thumbnail)
            media.fetch_cover(playlist_thumbnail, os.path.join(music_dir, f"cover.{ext}"))

        safe_name = os.path.basename(music_dir)
        zip_path = os.path.join(session.session_dir, f"{safe_name}.zip")
        media.build_zip(music_dir, session.session_dir, zip_path)

        session.zip_path = zip_path
        session.zip_name = f"{safe_name}.zip"

        q.put(
            {
                "type": "zip_ready",
                "session_id": session.session_id,
                "filename": f"{safe_name}.zip",
            }
        )

    q.put({"type": "all_done", "session_id": session.session_id})


async def start_download(
    session_id: str | None,
    urls: list[str],
    titles: dict[str, str],
    playlist_title: str,
    playlist_thumbnail: str,
) -> tuple[Session, bool]:
    """Create a session and fire off the download job without awaiting it."""
    is_playlist = bool(playlist_title.strip())

    music_subdir = None
    if is_playlist:
        music_subdir = sanitize_filename(playlist_title) or "playlist"
    session = store.create(session_id, music_subdir)

    if is_playlist:
        music_dir = os.path.join(session.session_dir, music_subdir)
    else:
        music_dir = session.session_dir
    os.makedirs(music_dir, exist_ok=True)

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        None,
        run_download_job,
        session,
        urls,
        titles,
        music_dir,
        is_playlist,
        playlist_thumbnail,
    )

    return session, is_playlist
