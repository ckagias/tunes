# scripts/sync_to_itunes.py

Adds downloaded MP3s to your iTunes library and syncs a connected iPhone,
so you don't have to manually drag files in and click Sync every time.

**Windows only.** This uses iTunes' COM automation interface, which only
exists on native Windows (not WSL, Linux, or macOS), and only for classic
**iTunes for Windows**. It will not work with the newer **Apple Devices**
app from the Microsoft Store, which doesn't expose the same interface.

## Setup (one-time, on Windows)

1. Make sure classic iTunes for Windows is installed and you've opened it
   at least once.
2. In iTunes, plug in your iPhone once and set its sync mode (Music tab →
   "Sync Music" → entire library or selected playlists). This script uses
   whatever mode is already configured; it doesn't change it.
3. Install the script's dependency (in a normal Windows Python install, not
   WSL):
   ```
   pip install -r scripts/requirements.txt
   ```

## Usage

```
python scripts/sync_to_itunes.py "C:\path\to\downloaded\songs"
```

Or with no argument, it defaults to your Downloads folder. It recursively
finds all `.mp3` files in the given folder, adds each to the iTunes
library, then triggers a device sync if an iPhone is connected.

## Known limitations

- iTunes must be running (the script launches it via COM if it isn't, but
  a visible window may still pop up).
- The "trigger sync" step (`UpdateIPod` via COM) mirrors clicking the Sync
  button, using your already-configured sync settings. It can't change
  what gets synced.
- Not tested against every iTunes version. If `UpdateIPod()` fails on your
  setup, click Sync manually in iTunes for that one run; file adding will
  have already worked.
