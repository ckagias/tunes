# tunes

Paste a link to a song or playlist. Get back MP3s with the artist, album,
title, and cover art already embedded — ready to drag straight into Apple
Music (or any other player) with zero manual tagging.

This exists because manually renaming files, hunting down cover art, and
fixing tags for every downloaded track is tedious. `tunes` does that part
automatically using [yt-dlp](https://github.com/yt-dlp/yt-dlp) + `ffmpeg`
under the hood.

## Status

**Phase 1 — YouTube only.** Paste a YouTube video or playlist link, pick which
tracks you want, download them as 320kbps MP3s with embedded metadata and
cover art. Spotify and SoundCloud support are planned (see [Roadmap](#roadmap)).

The app is intentionally **ephemeral** — nothing is stored server-side beyond
the time it takes to download and hand a file to your browser. There's no
account system, no database, no persisted library (yet).

## How it works

1. Paste a URL → the backend fetches metadata (title, thumbnail, duration)
   without downloading anything.
2. Pick which tracks you want (for playlists) → hit download.
3. The backend downloads each track, converts it to a 320kbps MP3, embeds
   ID3 tags (title/artist/album) and the cover art, and reports live
   progress back to the page.
4. Single tracks download directly as an `.mp3`; playlists download as a
   `.zip` (unzip it, then drag the folder into your music library).

## Running locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- **ffmpeg** on your PATH — yt-dlp shells out to it for audio extraction,
  tagging, and embedding cover art. Install it with:
  - macOS: `brew install ffmpeg`
  - Debian/Ubuntu/WSL: `sudo apt install ffmpeg`
  - Windows: `winget install ffmpeg` (or `choco install ffmpeg`)

### Setup

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate      # .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`. The Vite dev server proxies `/api`
requests to the backend on port 8000, so no CORS configuration is needed for
local dev.

Alternatively, once both are installed once, `make dev` (or `./dev.sh`) runs
both together.

### Advanced setup — YouTube bot-detection

YouTube periodically tightens anti-bot measures against tools like yt-dlp.
The backend already tries several YouTube "player clients" as fallbacks, but
if you hit persistent extraction errors, you can run the optional
[bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider)
plugin to supply proof-of-origin tokens:

1. Install and run the provider's Node server (see its README).
2. Set `BGU_POT_SERVER_HOST` in `backend/.env` (copy from `.env.example`) to
   point at it, e.g. `localhost:4416`.
3. Uncomment `bgutil-ytdlp-pot-provider` in `backend/requirements.txt` and
   reinstall.

This is not required for normal/occasional personal use.

## Legal & intended use

`tunes` is intended for **personal library management** — downloading audio
you already have the right to listen to, for offline personal use, in the
same spirit as tools like `yt-dlp` and `spotdl`. It is not intended for
redistribution, resale, or circumventing paid streaming services. You're
responsible for complying with the terms of service of whatever platform
you're downloading from, and with your local copyright law. `tunes` doesn't
host, cache, or redistribute any content itself — everything is ephemeral and
deleted immediately after being handed to your browser.

## Roadmap

- **Phase 2 — Spotify**: Spotify doesn't expose downloadable audio streams,
  so this will follow the same approach as `spotdl` — resolve accurate
  metadata via the Spotify Web API, then source the actual audio from
  YouTube, tagged with Spotify's (usually cleaner) metadata.
- **Phase 3 — SoundCloud**: yt-dlp already has a SoundCloud extractor, so
  this is mostly plumbing work once phase 1 is stable.
- **Persisted library**: an optional local database to track what you've
  already downloaded, instead of the current fully-ephemeral model.
- **Hosting**: a proper deploy target (the ephemeral, potentially slow
  download step doesn't fit Vercel's serverless model — a host with
  persistent disk and longer execution limits, e.g. Render/Fly/Railway,
  would be needed for a live demo).
- Design polish — the current UI is intentionally plain.

## Project layout

```
backend/    FastAPI app — routes, source abstraction (YouTube/Spotify/SoundCloud), download jobs
frontend/   Vite + React + TypeScript SPA
scripts/    Optional Windows-only helper: sync_to_itunes.py (see scripts/README.md)
```

See `backend/app/sources/` for how new platforms get added — each source
implements a small interface (`matches`, `fetch_info`, `download_track`) and
gets registered once in `backend/app/sources/registry.py`.

## Contributing

Issues and PRs welcome, especially for Spotify/SoundCloud source
implementations (see the stubs in `backend/app/sources/` for the intended
shape) and frontend design polish.
