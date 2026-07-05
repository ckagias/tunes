# Tunes

### A self-hosted music downloader built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), FastAPI, and React

[About](#about) • [Features](#features) • [How it works](#how-it-works) • [Installation](#installation) • [Usage](#usage) • [Automatic iTunes import](#automatic-itunes-import-optional) • [Legal and intended use](#legal-and-intended-use) • [Project layout](#project-layout) • [Dependencies](#dependencies) • [Contributing](#contributing) • [License](#license)

---

## About

Paste a link to a YouTube video, playlist, or album, or a Spotify track, album, or playlist, and get back MP3s with title, artist, and cover art already embedded.

Manually renaming files, hunting down cover art, and fixing tags for every downloaded track is tedious. Tunes automates that part.

---

## Features

- **Paste a link:** YouTube and YouTube Music videos, playlists, and albums; Spotify tracks, albums, and playlists.
- **Real tags for Spotify links:** Tunes finds the matching audio on YouTube Music automatically, but tags the file with the real metadata from Spotify (title, artist, album, cover art) instead of YouTube's own limited metadata. See [How it works](#how-it-works) for details.
- **Bad-match protection:** YouTube Music search sometimes ranks a wrong song, an instrumental or karaoke upload, or a non-video browse result above the actual track. Tunes checks several results per track, rejects titles that don't plausibly match, deprioritizes instrumental/karaoke/lyrics-video variants, and prefers whichever result has real album metadata.
- **Automatic tagging:** every track comes out as an MP3 with title, artist, album, album artist, and embedded cover art, with correct album grouping in players like iTunes and Music.app even when individual tracks have different featured artists.
- **Live progress:** per-track download and convert progress streamed to the page in real time over server-sent events.
- **Playlists and albums:** select exactly which tracks you want, then download the rest as a single zip with cover art included. Real playlists also get an `.m3u8` file so the zip imports as a ready-made playlist in iTunes, Apple Music, or VLC. Files stay downloadable until you start a new lookup or leave the page.
- **Concurrent, quality-matched downloads:** up to 8 tracks download at once, each re-encoded at its actual source bitrate (capped at 320kbps) instead of a fixed rate.
- **Ephemeral by design:** nothing is stored server-side beyond the current session. Files are cleaned up once you start a new lookup or leave the page, not after every single download.
- **Automatic iTunes import (optional, Windows only):** set `LIBRARY_DIR` and check "Add to iTunes automatically" before downloading, and finished tracks get copied to that folder and added to classic iTunes for Windows. See [Automatic iTunes import](#automatic-itunes-import-optional) below.
- **Pluggable source architecture:** download logic sits behind a small interface so other platforms can be added later without touching routes. See [Project layout](#project-layout).

---

## How it works

1. Paste a URL. The backend fetches metadata (title, thumbnail, duration, artist) without downloading anything.
2. Pick which tracks you want, for playlists and albums, then hit download.
3. The backend downloads up to 8 tracks at once, converts each to an MP3 matching its source bitrate (capped at 320kbps), embeds ID3 tags and cover art, and reports live progress back to the page.
4. Single tracks download directly as an `.mp3`. Playlists and albums download as a `.zip`; unzip it, then drag the folder into your music library. Both stay downloadable for repeat clicks until you start a new lookup or leave the page.

### Spotify links

Pasting a Spotify link doesn't download from Spotify directly. Spotify doesn't expose downloadable audio the way YouTube does. Instead, Tunes resolves the track's real metadata from Spotify, searches YouTube Music for the matching audio, downloads it, then tags the file with the real metadata (title, artist, album artist, album where available, cover art) instead of YouTube's own.

Metadata comes from Spotify's public embed pages (`open.spotify.com/embed/...`), the same page Spotify serves for embedded players such as iframes on blogs. No developer account, API key, login, or bearer tokens: just a plain HTTP GET. Full playlists and albums are supported.

**Finding the right YouTube Music match:** a plain "take the first search result" approach fails more often than expected. The top result can be an age or region restricted upload, an unrelated song by the same artist, a non-video browse page mixed into search results, or an instrumental/karaoke/lyrics-video upload ranked above the real track. Tunes checks several results per track and:

- filters out anything that isn't actually a video, such as YouTube Music album or artist browse pages,
- rejects titles that don't plausibly match the real track title, while tolerating differently worded feature credits and suffixes like "(Official Video)",
- rejects a candidate if the expected title marks a specific version (interlude, intro, outro, skit, reprise, prelude) that the candidate doesn't share,
- deprioritizes instrumental, karaoke, lyrics-video, sped-up, and slowed variants,
- and among what's left, prefers whichever result carries real album metadata.

This meaningfully cuts down wrong-song downloads and "Output file not found" failures, but YouTube Music's search ranking isn't perfectly stable. An occasional imperfect match, such as a fan upload instead of the cleanest official one, is still possible for less common tracks.

**Other caveats:**

- This relies on Spotify continuing to server-render track, album, and playlist data into the embed page's HTML. If Spotify changes the page format, Spotify links will stop resolving until this is updated. Plain YouTube links are unaffected either way.
- Spotify's embed pages don't expose per-track genre, so Spotify-sourced downloads don't get a genre tag, and YouTube's own generic "Music" genre fallback is explicitly suppressed rather than used as a stand-in.
- Album name is only available when the link itself is an album, or when Spotify's own data for that track's containing collection includes it. A standalone track or playlist link doesn't always carry the album name from Spotify, so it may fall back to whatever YouTube's matched video provides, if anything.
- Album artist is always set from the track's primary artist, not the full featured-artist list, so tracks from the same album group correctly in players like iTunes and Music.app even when individual tracks credit different guest features.
- Playlist track thumbnails are fetched individually since a Spotify playlist can mix tracks from many different albums; album tracks all share the album's own cover.

Cover art for Spotify-sourced tracks is the real album or track art from Spotify, not YouTube's video thumbnail.

---

## Installation

Pick your platform: [Windows](#windows) or [macOS / Linux](#macos--linux). Both end up
running the same app; only how you install prerequisites and launch the two processes
differs.

### Windows

1. Download the project: click the green **Code** button on this repository's page →
   **Download ZIP**, then extract it anywhere. (Have Git? `git clone
   https://github.com/ckagias/tunes.git` works too.)
2. Open the extracted `tunes` folder and double-click **`setup.bat`**.

`setup.bat` installs anything missing (Python, Node.js, ffmpeg, all via
`winget`), sets up the project, and opens the app in your browser at
`http://localhost:5173`.

A couple of things are normal and not errors:

- It may relaunch itself once in a new window right after installing something, to pick
  up the updated PATH, just let it continue.
- Windows may show a User Account Control prompt if it installs something new; click
  "Yes".

From then on, just double-click `dev.bat` to start the app again, it's faster since it
skips the setup checks. (`setup.bat` still works too; it just re-checks everything
first.)

<details>
<summary>setup.bat didn't work for me / I want to install things manually</summary>

This is exactly what `setup.bat` automates, spelled out step by step.

#### 1. Install prerequisites

- **Python 3.11+.** Check if you already have it, open PowerShell (search "PowerShell" in
  the Start menu) and run:
  ```powershell
  python --version
  ```
  If that prints `Python 3.11` or higher, you're set. If it errors, prints something
  older, or opens the Microsoft Store, install it:
  ```powershell
  winget install Python.Python.3.12
  ```
  Then **close and reopen PowerShell** (so it picks up the new PATH) and re-run
  `python --version` to confirm.

- **Node.js 18+.** Check the same way:
  ```powershell
  node --version
  ```
  If missing or too old:
  ```powershell
  winget install OpenJS.NodeJS.LTS
  ```
  Close and reopen PowerShell, then confirm with `node --version` again.

- **ffmpeg**, used for audio extraction, tagging, and embedding cover art:
  ```powershell
  winget install Gyan.FFmpeg
  ```
  Close and reopen PowerShell, then confirm with:
  ```powershell
  ffmpeg -version
  ```
  If `winget` itself isn't recognized, you're on an old Windows build without App
  Installer. Get it from the
  [Microsoft Store "App Installer" page](https://apps.microsoft.com/detail/9nblggh4nns1)
  first, or install Python/Node/ffmpeg manually from
  [python.org](https://www.python.org/downloads/windows/),
  [nodejs.org](https://nodejs.org/), and the
  [ffmpeg Windows builds page](https://www.gyan.dev/ffmpeg/builds/) (unzip it somewhere
  and add its `bin` folder to your PATH).

- **Git**, to clone the repository. Check with `git --version`; if missing:
  ```powershell
  winget install Git.Git
  ```
  Close and reopen PowerShell afterward. (Alternatively, skip Git entirely and download
  the repo as a ZIP from GitHub's green "Code" button, then extract it.)

#### 2. Clone the repository

```powershell
git clone https://github.com/ckagias/tunes.git
cd tunes
```

#### 3. Install and start the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If `.venv\Scripts\activate` fails with a message about execution policies (PowerShell
only, not cmd.exe), run this once in that PowerShell window and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Leave this window open, it's your running backend. You should see
`Uvicorn running on http://0.0.0.0:8000`.

#### 4. Install and start the frontend

Open a **second** PowerShell (or cmd) window:

```powershell
cd tunes\frontend
npm install
npm run dev
```

Leave this window open too. You should see a `Local: http://localhost:5173/` line.

#### 5. Open the app

Go to `http://localhost:5173` in your browser. The Vite dev server proxies `/api`
requests to the backend on port 8000, so no extra configuration is needed.

#### From now on

Once steps 1–4 are done once, just double-click **`dev.bat`** in the project folder,
it runs both the backend and frontend in that one window with interleaved output,
equivalent to steps 3–4 together; Ctrl+C stops both. If you'd rather run it straight
from PowerShell, `dev.ps1` does the same thing, but if it refuses to run with an
execution policy error, either use `dev.bat` instead (it bypasses the policy for
itself) or run the `Set-ExecutionPolicy` command from step 3 once. `setup.bat` also
works here, it detects everything is already installed and just launches the app.

</details>

Running the backend as native Windows Python (rather than under WSL) is required for
[automatic iTunes import](#automatic-itunes-import-optional) to actually add songs to
iTunes, not just copy them to a folder (see that section for details). Both `setup.bat`
and the manual steps above already do this correctly.

### macOS / Linux

#### Prerequisites

- Python 3.11+
- Node.js 18+
- **ffmpeg** on your PATH:
  - macOS: `brew install ffmpeg`
  - Debian/Ubuntu: `sudo apt install ffmpeg`

#### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ckagias/tunes.git
   cd tunes
   ```
2. **Install and start the backend**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
3. **Install and start the frontend** (in a second terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend on port 8000, so no CORS configuration is needed for local development.

Once both are installed once, `make dev` (or `./dev.sh`) starts both together.

Note: [automatic iTunes import](#automatic-itunes-import-optional) is a Windows-only
feature (it drives classic iTunes for Windows via COM automation, which doesn't exist
on macOS/Linux). Everything else in Tunes works the same on every platform.

### Advanced setup: YouTube bot detection

YouTube periodically tightens anti-bot measures against tools like yt-dlp. The backend already tries several YouTube player clients as fallbacks, but if you hit persistent extraction errors, you can run the optional [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) plugin to supply proof-of-origin tokens:

1. Install and run the provider's Node server, see its README.
2. Set `BGU_POT_SERVER_HOST` in `backend/.env` (copy from `.env.example`) to point at it, for example `localhost:4416`.
3. Uncomment `bgutil-ytdlp-pot-provider` in `backend/requirements.txt` and reinstall.

This isn't required for normal, occasional personal use.

---

## Usage

Open the app, paste a YouTube or Spotify link, and hit fetch. For a single track you'll get one MP3; for a playlist or album you can pick which tracks to include before downloading. See [scripts/README.md](scripts/README.md) for an optional Windows helper that adds downloaded songs to your iTunes library from the command line.

---

## Automatic iTunes import (optional)

By default, downloads disappear once you leave the page, you save the zip/MP3
yourself. Turn this on and Tunes will instead copy finished downloads into a folder you
choose and add them straight to iTunes for you.

**Windows only**, and only with classic **iTunes for Windows** (not the newer Apple
Devices app from the Microsoft Store). On macOS/Linux, files still get copied to your
chosen folder, they don't get added to iTunes automatically.

Setup (one-time):

1. Open `backend/.env` (copy it from `backend/.env.example` if it doesn't exist yet).
2. Set `LIBRARY_DIR` to wherever you keep your music, e.g.
   `LIBRARY_DIR=C:\Users\you\Music\Tunes`.
3. Restart the backend (or just use `dev.bat`, which always picks up
   `.env`).

Then, before each download, check **"Add to iTunes automatically"** in the app. (Or set
`AUTO_IMPORT_ITUNES=true` in `.env` to make it the default every time, without checking
the box.)

When it runs, Tunes copies the download into `LIBRARY_DIR` and adds it to your iTunes
library, including creating a matching playlist for a playlist download, in the right
track order. To sync a connected iPhone afterward, click Sync in iTunes yourself.

---

## Legal and intended use

Tunes is intended for personal library management: downloading audio you already have the right to listen to, for offline personal use, in the same spirit as tools like yt-dlp. It is not intended for redistribution, resale, or circumventing paid streaming services. You're responsible for complying with the terms of service of whatever platform you're downloading from, and with your local copyright law. Tunes doesn't host, cache, or redistribute any content itself. Everything is ephemeral, kept only for the current session, and deleted once you start a new lookup or leave the page.

---

## Project layout

```
backend/    FastAPI app: routes, source abstraction, download jobs
frontend/   Vite + React + TypeScript SPA
scripts/    Optional Windows-only helper: sync_to_itunes.py (see scripts/README.md)
```

See `backend/app/sources/` for how new platforms get added. Each source implements a small interface (`matches`, `fetch_info`, `download_track`) and gets registered once in `backend/app/sources/registry.py`.

---

## Dependencies

| Package                                                 | Purpose                                        |
| -------------------------------------------------------- | ----------------------------------------------- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp)              | YouTube extraction and audio download           |
| [FastAPI](https://fastapi.tiangolo.com/)                | Backend web framework                           |
| [sse-starlette](https://github.com/sysid/sse-starlette) | Server-sent events for live download progress   |
| [pywin32](https://github.com/mhammond/pywin32)          | Windows-only: drives iTunes for automatic import |
| [React](https://react.dev/)                             | Frontend UI                                     |
| [Vite](https://vite.dev/)                               | Frontend build tool and dev server              |

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started.

---

## License

This project is licensed under the [MIT License](LICENSE).
