# Tunes

### A self-hosted music downloader built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), FastAPI, and React

[About](#about) • [Features](#features) • [How it works](#how-it-works) • [Installation](#installation) • [Usage](#usage) • [Legal & intended use](#legal--intended-use) • [Project layout](#project-layout) • [Dependencies](#dependencies) • [Contributing](#contributing) • [License](#license)

---

## About

Paste a link to a YouTube video, playlist, or album — or a Spotify track, album, or playlist — and get back MP3s with title, artist, and cover art already embedded.

This exists because manually renaming files, hunting down cover art, and fixing tags for every downloaded track is tedious. `tunes` does that part automatically.

If you find this useful, feel free to leave a ⭐ to help others find it!

---



## Features

- 🎵 **Paste-a-link downloading:** any YouTube video or playlist URL works through the same flow.
- 🔗 **Spotify links, with real tags:** paste a Spotify track/album/playlist link — `tunes` finds the matching audio on YouTube Music automatically, but tags the file with the *real* metadata from Spotify (title, artist, album, cover art), not YouTube's own limited metadata. See [How it works](#how-it-works) for details and caveats.
- 🎯 **Bad-match protection:** YouTube Music search sometimes ranks a wrong song, an instrumental/karaoke upload, or a non-video "browse" result above the actual track. `tunes` checks several results per track, rejects titles that don't plausibly match, deprioritizes instrumental/karaoke/lyrics-video variants, and prefers whichever has real album metadata — instead of blindly trusting the first result.
- 🏷️ **Automatic tagging:** every track comes out as an MP3 with title, artist, album, album artist, and embedded cover art, which means no manual editing (and correct album grouping in players like iTunes/Music.app, even when individual tracks have different featured artists).
- ⚡ **Live progress:** per-track download/convert progress streamed to the page in real time over SSE.
- 📦 **Playlists & albums:** select exactly which tracks you want, download the rest as a single zip with cover art included. Files stay downloadable — re-clicking Save works — until you start a new lookup, click "Start over," or leave the page.
- 🚀 **Concurrent, quality-matched downloads:** up to 8 tracks download at once, each re-encoded at its actual source bitrate (capped at 320kbps) instead of a fixed rate, so playlists finish faster with no wasted file size.
- 🧹 **Ephemeral by design:** nothing is stored server-side beyond the current session — files are cleaned up once you're done with them (new lookup, "Start over," or leaving the page), not on every single download.
- 🧩 **Pluggable source architecture:** the download logic is written behind a small interface so other platforms can be added later without touching routes (see [Project layout](#project-layout)).

---



## How it works

1. Paste a URL → the backend fetches metadata (title, thumbnail, duration) without downloading anything.
2. Pick which tracks you want (for playlists/albums) → hit download.
3. The backend downloads up to 8 tracks at once, converts each to an MP3 matching its source bitrate (capped at 320kbps), embeds ID3 tags (title/artist/album/album artist) and the cover art, and reports live progress back to the page.
4. Single tracks download directly as an `.mp3` [playlists download as a `.zip` (unzip it, then drag the folder into your music library)]. Both stay downloadable for repeat clicks until you start a new lookup, click "Start over," or leave the page.

### Spotify links

Pasting a Spotify link doesn't download from Spotify directly — Spotify doesn't expose downloadable audio the way YouTube does. Instead, `tunes` resolves the track's real metadata from Spotify, searches YouTube Music for the matching audio, downloads it, then **tags the file with the real metadata** (title, artist, album artist, album where available, cover art) instead of YouTube's own.

Metadata comes from Spotify's public embed pages (`open.spotify.com/embed/...`) — the same page Spotify serves for embedded players (e.g. iframes on blogs). No developer account, no API key, no login, no bearer tokens: just a plain HTTP GET. Full playlists and albums are supported.

**Finding the right YouTube Music match:** a plain "take the first search result" approach fails more often than you'd expect — the top result can be an age/region-restricted upload, an unrelated song by the same artist, a non-video "browse" page mixed into search results, or an instrumental/karaoke/lyrics-video upload ranked above the real track. `tunes` instead checks several results per track and:
- filters out anything that isn't actually a video (e.g. YouTube Music album/artist browse pages),
- rejects titles that don't plausibly match the real track title (tolerating differently-worded feature credits, "(Official Video)" suffixes, etc.),
- deprioritizes instrumental/karaoke/lyrics-video/sped-up/slowed variants,
- and among what's left, prefers whichever result carries real album metadata.

This meaningfully cuts down wrong-song downloads and "Output file not found" failures, but YouTube Music's search ranking isn't perfectly stable — an occasional imperfect match (e.g. a fan upload instead of the cleanest official one) is still possible for less common tracks.

**Other caveats:**
- This relies on Spotify continuing to server-render track/album/playlist data into the embed page's HTML. If Spotify changes the page format, Spotify links will stop resolving until this is updated (plain YouTube links are unaffected either way).
- Spotify's embed pages don't expose per-track genre, so Spotify-sourced downloads don't get a genre tag (and YouTube's own generic `Music` genre fallback is explicitly suppressed rather than used as a stand-in).
- Album name is only available when the link itself is an album or when Spotify's own data for that track's containing collection includes it (e.g. an album link) — a standalone track or playlist link doesn't always carry the album name from Spotify, so it may fall back to whatever (if anything) YouTube's matched video provides.
- Album artist is always set from the track's primary artist (not the full featured-artist list), so tracks from the same album group correctly in players like iTunes/Music.app even when individual tracks credit different guest features.

Cover art for Spotify-sourced tracks is the real album/track art from Spotify, not YouTube's video thumbnail.

---



## Installation



### Prerequisites

- Python 3.11+
- Node.js 18+
- **ffmpeg** on your PATH (used for audio extraction, tagging, and embedding cover art):
  - macOS: `brew install ffmpeg`
  - Debian/Ubuntu/WSL: `sudo apt install ffmpeg`
  - Windows: `winget install ffmpeg` 



### Setup

1. **Clone the repository**
  ```bash
   git clone https://github.com/ckagias/tunes.git
   cd tunes
  ```
2. **Install and start the backend**
  ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate      # .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
  ```
3. **Install and start the frontend** (in a second terminal)
  ```bash
   cd frontend
   npm install
   npm run dev
  ```
4. Open `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend on port 8000, so no CORS configuration is needed for local dev.

Once both are installed once, `make dev` (or `./dev.sh`) starts both together.

### Advanced setup (YouTube bot-detection)

YouTube periodically tightens anti-bot measures against tools like yt-dlp. The backend already tries several YouTube "player clients" as fallbacks, but if you hit persistent extraction errors, you can run the optional [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) plugin to supply proof-of-origin tokens:

1. Install and run the provider's Node server (see its README).
2. Set `BGU_POT_SERVER_HOST` in `backend/.env` (copy from `.env.example`) to point at it, e.g. `localhost:4416`.
3. Uncomment `bgutil-ytdlp-pot-provider` in `backend/requirements.txt` and reinstall.

This is not required for normal/occasional personal use.

---



## Usage

Open the app, paste a YouTube or Spotify link, and hit fetch. For a single track you'll get one MP3; for a playlist you can pick which tracks to include before downloading. See `[scripts/README.md](scripts/README.md)` for an optional Windows helper that pushes downloaded songs into iTunes and syncs a connected iPhone.

---



## Legal & intended use

`tunes` is intended for **personal library management**. Downloading audio you already have the right to listen to, for offline personal use, in the same spirit as tools like `yt-dlp`. It is not intended for redistribution, resale, or circumventing paid streaming services. You're responsible for complying with the terms of service of whatever platform you're downloading from, and with your local copyright law. `tunes` doesn't host, cache, or redistribute any content itself — everything is ephemeral, kept only for the current session, and deleted once you start a new lookup, click "Start over," or leave the page.

---



## Project layout

```
backend/    FastAPI app — routes, source abstraction, download jobs
frontend/   Vite + React + TypeScript SPA
scripts/    Optional Windows-only helper: sync_to_itunes.py (see scripts/README.md)
```

See `backend/app/sources/` for how new platforms get added — each source implements a small interface (`matches`, `fetch_info`, `download_track`) and gets registered once in `backend/app/sources/registry.py`.

---



## Dependencies


| Package                                                 | Purpose                                       |
| ------------------------------------------------------- | --------------------------------------------- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp)              | YouTube extraction and audio download         |
| [FastAPI](https://fastapi.tiangolo.com/)                | Backend web framework                         |
| [sse-starlette](https://github.com/sysid/sse-starlette) | Server-sent events for live download progress |
| [React](https://react.dev/)                             | Frontend UI                                   |
| [Vite](https://vite.dev/)                               | Frontend build tool & dev server              |


---



## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started.

---



## License

This project is licensed under the [MIT License](LICENSE).