"""
Adds downloaded MP3s to the iTunes library and syncs a connected iPhone.

Windows-only: drives classic iTunes for Windows via its COM interface.
Requires: iTunes for Windows installed, pywin32 (`pip install pywin32`).

This does NOT work with the newer "Apple Devices" app (Microsoft Store) —
that app does not expose the same automation interface. If you've moved to
Apple Devices + a separate Apple Music app, this script will not find
iTunes and will exit with an error.

Usage:
    python scripts/sync_to_itunes.py <folder>
    python scripts/sync_to_itunes.py                # defaults to DEFAULT_FOLDER below

Sync behavior: this triggers iTunes' sync using whatever "Sync Music" mode
is already configured on the device in iTunes (entire library / selected
playlists). It does not change that setting — set it once yourself in
iTunes' device page first (see README).
"""

import sys
from pathlib import Path

DEFAULT_FOLDER = Path.home() / "Downloads"

try:
    import win32com.client
except ImportError:
    print(
        "pywin32 is required. Install it with: pip install pywin32\n"
        "Note: this script only runs on native Windows Python, not WSL/Linux.",
        file=sys.stderr,
    )
    sys.exit(1)


def find_mp3s(folder: Path) -> list[Path]:
    return sorted(folder.rglob("*.mp3"))


def connect_itunes():
    try:
        return win32com.client.Dispatch("iTunes.Application")
    except Exception as e:
        print(
            "Could not connect to iTunes via COM. Make sure classic iTunes for "
            "Windows is installed (this does not work with the newer 'Apple "
            f"Devices' app). Underlying error: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


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


def find_connected_device(itunes):
    """
    iTunes exposes connected iOS devices as Sources of kind
    ITSourceKindIPod (=4). Returns the first one found, or None.
    """
    IT_SOURCE_KIND_IPOD = 4
    for source in itunes.Sources:
        if source.Kind == IT_SOURCE_KIND_IPOD:
            return source
    return None


def sync_device(itunes) -> bool:
    device = find_connected_device(itunes)
    if not device:
        print("No connected iPhone/iPod found in iTunes. Plug it in and try again.")
        return False

    print(f"Found device: {device.Name}. Starting sync…")
    try:
        # UpdateIPod() triggers the same sync classic iTunes runs when you
        # click "Sync" on the device page, using its currently configured
        # sync settings (entire library / selected playlists).
        itunes.UpdateIPod()
        print("Sync started. Check the iTunes window for progress.")
        return True
    except Exception as e:
        print(
            "Could not trigger sync via COM (UpdateIPod). You may need to "
            f"click 'Sync' manually in iTunes this time. Error: {e}",
            file=sys.stderr,
        )
        return False


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

    itunes = connect_itunes()
    added = add_files_to_library(itunes, files)
    print(f"Added {added}/{len(files)} file(s) to the iTunes library.")

    if added:
        sync_device(itunes)


if __name__ == "__main__":
    main()
