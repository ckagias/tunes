# Contributing to Tunes

### Help improve a self-hosted music downloader built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), FastAPI, and React

[Getting Started](#getting-started) • [Project Structure](#project-structure) • [Adding a Source](#adding-a-source) • [Adding a Route](#adding-a-route) • [Adding a Frontend Component](#adding-a-frontend-component) • [Guidelines](#guidelines) • [Submitting a PR](#submitting-a-pr)

---

## Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/ckagias/tunes.git
   cd tunes
   ```
2. **Install and run the backend** (see [Installation](README.md#installation) in the README for the full prerequisites, including ffmpeg)
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate      # .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
3. **Install and run the frontend** (in a second terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. **Create a branch** off `main` for your change:
   ```bash
   git checkout -b feat/my-feature
   ```

---

## Project Structure

```
tunes/
├── backend/
│   └── app/
│       ├── main.py              FastAPI app instance, CORS, router wiring
│       ├── config.py            Environment-based settings (pydantic-settings)
│       ├── models.py            Pydantic request/response schemas
│       ├── routes/              One file per API route group: info, download, progress, serve
│       ├── sources/
│       │   ├── base.py              The Source interface every platform implements
│       │   ├── registry.py          Resolves a URL to its Source
│       │   ├── youtube.py           YouTube and YouTube Music source, also used for Spotify downloads
│       │   └── spotify.py           Spotify source: metadata from Spotify, audio via youtube.py
│       └── services/
│           ├── jobs.py              Download job orchestration and progress bridging
│           ├── sessions.py          Ephemeral in-memory session store
│           ├── media.py             URL/text helpers, cover-art fetching, zip and playlist building
│           ├── ydl_opts.py          yt-dlp option builders, the tagging pipeline
│           └── spotify_client.py    Spotify metadata via public embed pages
├── frontend/
│   └── src/
│       ├── App.tsx              Top-level page state machine
│       ├── api/                 Fetch client and SSE progress stream wrapper
│       ├── components/          UrlInput, TrackList, TrackRow, DownloadPanel, StatusBadge
│       ├── hooks/                   useDownloadProgress: reduces SSE events into UI state
│       └── types.ts             TS types mirroring the backend's Pydantic schemas
└── scripts/                     Optional Windows-only helpers (see scripts/README.md)
```

---

## Adding a Source

Every platform implements the `Source` interface in `backend/app/sources/base.py`, and gets registered once in `backend/app/sources/registry.py`. Routes never import a concrete source directly; they always go through `registry.resolve(url)`, so adding a platform never touches route code.

### Minimal template

```python
from app.models import InfoResponse
from app.sources.base import Source


class MySource(Source):
    name = "myplatform"

    def matches(self, url: str) -> bool:
        return "myplatform.com" in url

    def fetch_info(self, url: str) -> InfoResponse:
        # Return metadata only, no downloading here.
        ...

    def download_track(self, url, title, music_dir, progress_hook, pp_hook) -> str | None:
        # Download and tag the track into music_dir, calling progress_hook/pp_hook
        # as work progresses. Return the final file path, or None on failure.
        ...
```

Then register it:

```python
# backend/app/sources/registry.py
_SOURCES: list[Source] = [
    YouTubeSource(),
    SpotifySource(),
    MySource(),
]
```

### Rules for sources

- **`matches()` must be cheap and side-effect-free.** It's called on every incoming URL to find the right source.
- **`fetch_info()` must not download any media,** only resolve metadata: title, thumbnail, duration, uploader, and, for playlists and albums, the full track list.
- **Reuse the existing tagging pipeline** (`services/ydl_opts.py`) wherever the platform's audio can be fetched via yt-dlp, instead of writing a new postprocessor chain. If your source has no downloadable audio of its own, see `sources/spotify.py` for the pattern of resolving real metadata, then delegating the actual download to `youtube.py`'s `download_with_overrides()`.
- **Fail with a clear, user-facing message.** Raise `ValueError` for anything the user can act on, such as missing credentials, an unsupported URL shape, or region-locked content. Routes already catch `ValueError` and return it as a clean 400.

---

## Adding a Route

Routes live in `backend/app/routes/`, one file per group, and are wired up in `backend/app/main.py` via `app.include_router(...)`. Keep route handlers thin. They should validate input, call into `services/` or `sources/`, and shape the response; put actual logic in a service module instead.

---

## Adding a Frontend Component

Components live in `frontend/src/components/`. The app is intentionally simple: a single state machine in `App.tsx` (`idle → fetching-info → info-ready → downloading`) drives which components render. New UI should fit into that flow rather than introduce a parallel state source. SSE progress events are consumed centrally in `hooks/useDownloadProgress.ts`; read from that hook's output rather than opening a second `EventSource`.

---

## Guidelines

### General

- Keep each module focused on one thing. A route file handles one group of endpoints, a source handles one platform.
- Prefer `async`/`await` in the frontend and FastAPI routes; keep blocking work, such as yt-dlp calls, off the event loop via `run_in_executor`, matching the existing pattern in `routes/info.py` and `services/jobs.py`.
- Match the existing code style. Python follows the formatting already in the codebase (no enforced linter yet); TypeScript avoids `any` and keeps types in `types.ts` in sync with the backend's Pydantic models.
- Keep comments short and purposeful. Explain the non-obvious "why," not the "what" the code already shows.

### Commits

- Use short, imperative commit messages: `add Bandcamp source`, `fix zip cleanup on serve error`.
- One logical change per commit.

### What not to add

- A database or persisted library. The app is intentionally ephemeral for now, see the README's Legal section for the reasoning.
- Dependencies that aren't genuinely needed, especially ones with awkward version pins that could conflict with FastAPI or yt-dlp.
- Config files or secrets (`.env`, API keys, tokens).

---

## Submitting a PR

1. Make sure the backend still imports cleanly (`python -c "from app.main import app"`) and the frontend still typechecks (`npx tsc --noEmit`).
2. Test the happy path and at least one error or edge case, such as an unsupported URL, private or unavailable content, or an empty selection.
3. If you touched tagging or download logic, verify the resulting MP3 actually has embedded tags and cover art, for example with `ffprobe`, or by importing it into a music player.
4. Open a pull request against `main` with a clear title and a short description of what changed and why.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
