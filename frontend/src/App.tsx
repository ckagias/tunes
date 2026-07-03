import { useMemo, useState } from "react";
import { getInfo, startDownload } from "./api/client";
import { DownloadPanel } from "./components/DownloadPanel";
import { TrackList } from "./components/TrackList";
import { UrlInput } from "./components/UrlInput";
import { useDownloadProgress } from "./hooks/useDownloadProgress";
import type { InfoResponse } from "./types";

type Phase = "idle" | "fetching-info" | "info-ready" | "downloading";

export default function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [info, setInfo] = useState<InfoResponse | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const progressState = useDownloadProgress(sessionId);

  const handleFetchInfo = async (url: string) => {
    setError(null);
    setPhase("fetching-info");
    setInfo(null);
    setSessionId(null);
    try {
      const result = await getInfo(url);
      setInfo(result);
      setSelected(new Set(result.tracks.map((t) => t.url)));
      setPhase("info-ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch info");
      setPhase("idle");
    }
  };

  const handleToggle = (url: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(url)) next.delete(url);
      else next.add(url);
      return next;
    });
  };

  const handleToggleAll = () => {
    if (!info) return;
    setSelected((prev) =>
      prev.size === info.tracks.length ? new Set() : new Set(info.tracks.map((t) => t.url)),
    );
  };

  const handleStartDownload = async () => {
    if (!info) return;
    setStarting(true);
    setError(null);
    try {
      const urls = info.tracks.filter((t) => selected.has(t.url)).map((t) => t.url);
      const titles = Object.fromEntries(info.tracks.map((t) => [t.url, t.title]));
      const isPlaylist = info.type === "playlist";

      const response = await startDownload({
        urls,
        titles,
        playlist_title: isPlaylist ? info.title : "",
        playlist_thumbnail: isPlaylist ? info.thumbnail : "",
      });

      setSessionId(response.session_id);
      setPhase("downloading");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start download");
    } finally {
      setStarting(false);
    }
  };

  const selectable = phase === "info-ready";

  const resetLink = useMemo(
    () => (
      <button
        type="button"
        className="link-button"
        onClick={() => {
          setPhase("idle");
          setInfo(null);
          setSessionId(null);
          setSelected(new Set());
          setError(null);
        }}
      >
        Start over
      </button>
    ),
    [],
  );

  return (
    <main className="app">
      <header className="app-header">
        <h1>tunes</h1>
        <p className="tagline">
          Paste a link. Get a fully tagged MP3 with cover art — ready for Apple Music.
        </p>
      </header>

      <UrlInput onSubmit={handleFetchInfo} disabled={phase === "fetching-info"} />

      {error && <p className="error-banner">{error}</p>}

      {info && (
        <>
          <TrackList
            info={info}
            selected={selected}
            onToggle={handleToggle}
            onToggleAll={handleToggleAll}
            progress={progressState.tracks}
            selectable={selectable}
          />
          <DownloadPanel
            onStart={handleStartDownload}
            starting={starting}
            selectedCount={selected.size}
            sessionId={sessionId}
            isPlaylist={info.type === "playlist"}
            zipFilename={progressState.zipFilename}
            isComplete={progressState.isComplete}
            tracks={progressState.tracks}
          />
        </>
      )}

      {(info || sessionId) && <footer className="app-footer">{resetLink}</footer>}
    </main>
  );
}
