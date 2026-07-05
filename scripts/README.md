# scripts/sync_to_itunes.py

Adds downloaded MP3s to your iTunes library, so you don't have to manually
drag files in every time. To sync a connected iPhone afterward, click Sync
in iTunes yourself — this script doesn't do that.

This logic also backs two other entry points in this repo, all sharing the
same `add_folder_to_itunes()` function so there's one implementation of the
"add these MP3s to iTunes" step:

- **The app's built-in auto-import** (see the main [README](../README.md#automatic-itunes-import-optional)):
  set `LIBRARY_DIR` and check "Add to iTunes automatically" in the app, and
  `backend/app/services/library.py` calls this script for you after each
  download — no folder to point at manually.
- **`import_to_itunes.sh`** (below): a standalone wrapper for running the same
  import from the command line against any folder, without the web app.

**Windows only.** This uses iTunes' COM automation interface, which only
exists on native Windows, and only for classic **iTunes for Windows**. It
will not work with the newer **Apple Devices** app from the Microsoft Store,
which doesn't expose the same interface, and it doesn't work on macOS or
Linux at all — iTunes' COM interface simply doesn't exist there.

## Setup (one-time, on Windows)

1. Make sure classic iTunes for Windows is installed and you've opened it
   at least once.
2. Install the script's dependency:
   ```
   pip install -r scripts/requirements.txt
   ```

## Usage

```
python scripts/sync_to_itunes.py "C:\path\to\downloaded\songs"
```

Or with no argument, it defaults to your Downloads folder. It recursively
finds all `.mp3` files in the given folder and adds each to the iTunes
library. To sync a connected iPhone afterward, click Sync in iTunes.

## Known limitations

- iTunes must be running (the script launches it via COM if it isn't, but
  a visible window may still pop up).
- Not tested against every iTunes version.

---

# scripts/import_to_itunes.sh

A thin standalone wrapper around `sync_to_itunes.py`'s add-to-library step,
driven by a params file instead of a command-line arg — useful if you want
to re-run an import without typing a path each time, or wire it into your
own tooling.

**Windows only**, same constraints as above: run it from a shell backed by
native Windows Python (e.g. Git Bash).

## Setup

1. Edit `scripts/import_to_itunes.conf`:
   ```
   SONGS_DIR="C:/Users/you/Music/Tunes"
   PYTHON="python"
   ```
2. Complete the one-time iTunes setup above (`pip install -r scripts/requirements.txt`, iTunes installed).

## Usage

```
./scripts/import_to_itunes.sh                # uses SONGS_DIR from the .conf file
./scripts/import_to_itunes.sh "C:\path\to\songs"   # overrides SONGS_DIR for this run
```

This only adds files to the iTunes library. To sync a connected iPhone
afterward, click Sync in iTunes yourself.

Note: the app itself can also do this automatically after every download —
see [Automatic iTunes import](../README.md#automatic-itunes-import-optional)
in the main README. This script is for running the same import by hand,
outside the app.
