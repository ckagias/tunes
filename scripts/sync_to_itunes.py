"""
Adds downloaded MP3s to the iTunes library.

Windows-only: drives classic iTunes for Windows via its COM interface.
Requires: iTunes for Windows installed, pywin32 (`pip install pywin32`).

This does NOT work with the newer "Apple Devices" app (Microsoft Store) —
that app does not expose the same automation interface. If you've moved to
Apple Devices + a separate Apple Music app, this script will not find
iTunes and will exit with an error.

Usage:
    python scripts/sync_to_itunes.py <folder>
    python scripts/sync_to_itunes.py                # defaults to DEFAULT_FOLDER below

This only adds files to the iTunes library. To sync a connected iPhone
afterward, click Sync in iTunes yourself.
"""

import sys
import time
from pathlib import Path
from typing import Optional

DEFAULT_FOLDER = Path.home() / "Downloads"

# When iTunes has to cold-start (it wasn't already running), Dispatch() returns
# a COM handle before iTunes has finished initializing its library/playlist
# source. Calling ImportPlaylist/AddFile too soon fails with a generic
# "<unknown>.ImportPlaylist" COM error. Poll LibrarySource until it's ready.
_STARTUP_TIMEOUT_SECONDS = 30
_STARTUP_POLL_INTERVAL_SECONDS = 0.5


def find_mp3s(folder: Path) -> list[Path]:
    return sorted(folder.rglob("*.mp3"))


def connect_itunes():
    """Lazily imports pywin32 so this module can be imported (e.g. by the backend)
    on any OS without raising — only calling this function requires Windows + pywin32."""
    try:
        import pythoncom
        import win32com.client
    except ImportError as e:
        raise RuntimeError(
            "pywin32 is required. Install it with: pip install pywin32\n"
            "Note: this only works on native Windows Python."
        ) from e

    # This runs on an asyncio executor thread, which never calls CoInitialize.
    # Without it, Dispatch() fails with "CoInitialize has not been called."
    pythoncom.CoInitialize()

    try:
        # Early-bound dispatch (vs. plain Dispatch's late/dynamic binding) generates
        # real method wrappers from iTunes' type library. Method calls that fail under
        # dynamic dispatch surface as opaque "<unknown>.MethodName" errors with no
        # detail; early binding gives us the actual HRESULT/description instead.
        itunes = win32com.client.gencache.EnsureDispatch("iTunes.Application")
    except Exception as e:
        raise RuntimeError(
            "Could not connect to iTunes via COM. Make sure classic iTunes for "
            "Windows is installed (this does not work with the newer 'Apple "
            f"Devices' app). Underlying error: {e}"
        ) from e

    _wait_until_ready(itunes)
    return itunes


def _wait_until_ready(itunes) -> None:
    """Block until iTunes' library/playlist source responds, so a cold-started
    iTunes (it wasn't already running) doesn't get an ImportPlaylist/AddFile
    call before its COM server has actually finished initializing."""
    deadline = time.monotonic() + _STARTUP_TIMEOUT_SECONDS
    last_error: Exception = RuntimeError("timed out waiting for iTunes to start")
    while time.monotonic() < deadline:
        try:
            _ = itunes.LibrarySource.Playlists.Count
            return
        except Exception as e:
            last_error = e
            time.sleep(_STARTUP_POLL_INTERVAL_SECONDS)
    raise RuntimeError(
        f"iTunes did not finish starting up within {_STARTUP_TIMEOUT_SECONDS}s. "
        f"Underlying error: {last_error}"
    )


def add_files_to_library(itunes, files: list[Path]) -> int:
    library = itunes.LibraryPlaylist
    added = 0
    for f in files:
        try:
            library.AddFile(str(f))
            added += 1
            print(f"Added: {f.name}")
        except Exception as e:
            print(f"Failed to add {f.name}: {e}", file=sys.stderr)
    return added


def find_m3u8(folder: Path) -> Optional[Path]:
    matches = sorted(folder.glob("*.m3u8"))
    return matches[0] if matches else None


def import_playlist(itunes, m3u8_path: Path, files: list[Path]) -> int:
    """Import an .m3u8 as an iTunes playlist — this both adds the referenced tracks
    to the library and creates a playlist from them, in track order, in one step.

    Classic iTunes' ImportPlaylist is finicky about the .m3u8 file itself (encoding,
    non-ASCII titles, etc.) and fails with an opaque "<unknown>.ImportPlaylist" COM
    error that gives no real diagnostic. If that happens, fall back to adding each
    file directly via AddFile (known reliable) and building the playlist by hand
    through COM instead of trusting iTunes' .m3u8 parser.
    """
    try:
        playlist = itunes.LibrarySource.Playlists.ImportPlaylist(str(m3u8_path))
        return playlist.Tracks.Count
    except Exception as e:
        print(
            f"ImportPlaylist failed ({e}); falling back to manual playlist creation.",
            file=sys.stderr,
        )
        return _build_playlist_manually(itunes, m3u8_path.stem, files)


def _build_playlist_manually(itunes, playlist_name: str, files: list[Path]) -> int:
    """Create a playlist and add each file to it directly — used when ImportPlaylist
    itself fails.

    CreatePlaylist returns a plain IITPlaylist, which doesn't expose AddFile/AddTrack
    — those live on the more specific IITUserPlaylist interface, so the object must
    be cast via win32com.client.CastTo. AddFile on the playlist (rather than on
    itunes.LibraryPlaylist) adds the track to the library and this playlist in one
    step, in call order — matching what ImportPlaylist would have done.
    """
    import win32com.client

    playlist = itunes.CreatePlaylist(playlist_name)
    playlist = win32com.client.CastTo(playlist, "IITUserPlaylist")
    added = 0
    for f in files:
        try:
            playlist.AddFile(str(f))
            added += 1
            print(f"Added: {f.name}")
        except Exception as e:
            print(f"Failed to add {f.name}: {e}", file=sys.stderr)
    return added


def add_folder_to_itunes(folder: Path) -> tuple[int, int]:
    """Add a finished download to the iTunes library.
    If folder contains an .m3u8 (a playlist/album download), import that instead of
    adding each MP3 individually — it both adds the tracks and creates a matching
    iTunes playlist in track order, in one step. Otherwise (a single track), add the
    lone MP3 directly. Returns (added, total). Raises RuntimeError if iTunes/pywin32
    aren't available."""
    m3u8_path = find_m3u8(folder)
    if m3u8_path:
        files = find_mp3s(folder)
        itunes = connect_itunes()
        added = import_playlist(itunes, m3u8_path, files)
        return added, len(files)

    files = find_mp3s(folder)
    if not files:
        return 0, 0
    itunes = connect_itunes()
    added = add_files_to_library(itunes, files)
    return added, len(files)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDER
    if not folder.is_dir():
        print(f"Not a folder: {folder}", file=sys.stderr)
        sys.exit(1)

    files = find_mp3s(folder)
    if not files:
        print(f"No .mp3 files found in {folder}")
        return

    print(f"Found {len(files)} MP3 file(s) in {folder}")

    try:
        itunes = connect_itunes()
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    m3u8_path = find_m3u8(folder)
    if m3u8_path:
        added = import_playlist(itunes, m3u8_path, files)
        print(f"Imported playlist '{m3u8_path.stem}' with {added}/{len(files)} track(s).")
    else:
        added = add_files_to_library(itunes, files)
        print(f"Added {added}/{len(files)} file(s) to the iTunes library.")


if __name__ == "__main__":
    main()
