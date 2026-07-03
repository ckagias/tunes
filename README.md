# Tunes

### A self-hosted YouTube music downloader built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), FastAPI, and React

[About](#about) • [Features](#features) • [How it works](#how-it-works) • [Installation](#installation) • [Usage](#usage) • [Legal & intended use](#legal--intended-use) • [Project layout](#project-layout) • [Dependencies](#dependencies) • [Contributing](#contributing) • [License](#license)

---

## About

Paste a link to a YouTube video, playlist, or album. Get back MP3s with the artist, album, title, and cover art already embedded.

This exists because manually renaming files, hunting down cover art, and fixing tags for every downloaded track is tedious. `tunes` does that part automatically.

If you find this useful, feel free to leave a ⭐ to help others find it!

---



## Features

- 🎵 **Paste-a-link downloading:** any YouTube video or playlist URL works through the same flow.
- 🏷️ **Automatic tagging:** every track comes out as a 320kbps MP3 with title, artist, album, and embedded cover art which means no manual editing.
- ⚡ **Live progress:** per-track download/convert progress streamed to the page in real time over SSE.
- 📦 **Playlists & albums:** select exactly which tracks you want, download the rest as a single zip with cover art included.
- 🧹 **Ephemeral by design:** nothing is stored server-side beyond the time it takes to hand a file to your browser.
- 🧩 **Pluggable source architecture:** the download logic is written behind a small interface so other platforms can be added later without touching routes (see [Project layout](#project-layout)).

---



## How it works

1. Paste a URL → the backend fetches metadata (title, thumbnail, duration) without downloading anything.
2. Pick which tracks you want (for playlists/albums) → hit download.
3. The backend downloads each track, converts it to a 320kbps MP3, embeds ID3 tags (title/artist/album) and the cover art, and reports live progress back to the page.
4. Single tracks download directly as an `.mp3` [playlists download as a `.zip` (unzip it, then drag the folder into your music library)].

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

Open the app, paste a YouTube video or playlist link, and hit fetch. For a single track you'll get one MP3; for a playlist you can pick which tracks to include before downloading. See `[scripts/README.md](scripts/README.md)` for an optional Windows helper that pushes downloaded songs into iTunes and syncs a connected iPhone.

---



## Legal & intended use

`tunes` is intended for **personal library management**. Downloading audio you already have the right to listen to, for offline personal use, in the same spirit as tools like `yt-dlp`. It is not intended for redistribution, resale, or circumventing paid streaming services. You're responsible for complying with the terms of service of whatever platform you're downloading from, and with your local copyright law. `tunes` doesn't host, cache, or redistribute any content itself — everything is ephemeral and deleted immediately after being handed to your browser.

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