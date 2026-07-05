import { useEffect, useRef, useState } from "react";
import { endSession, getInfo, startDownload } from "./api/client";
import { DownloadPanel } from "./components/DownloadPanel";
import { TrackList } from "./components/TrackList";
import { UrlInput } from "./components/UrlInput";
import { useDownloadProgress } from "./hooks/useDownloadProgress";
import type { InfoResponse } from "./types";

const STYLES = {
  page: "min-h-screen flex justify-center",
  app: "w-full max-w-2xl px-6 pt-10 pb-16",
  header: "mb-6",
  title: "text-2xl font-semibold tracking-tight",
  errorBanner: "bg-danger/10 text-danger text-sm rounded-lg px-4 py-3 mb-4",
  autoImportRow: "flex items-center gap-2 mb-4",
  autoImportLabel: "text-sm text-text-muted select-none",
};

type Phase = "idle" | "fetching-info" | "info-ready" | "downloading";

export default function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [info, setInfo] = useState<InfoResponse | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [autoImport, setAutoImport] = useState(false);

  const progressState = useDownloadProgress(sessionId);

  // Keeps the beforeunload handler reading the latest sessionId, avoiding a stale closure.
  const sessionIdRef = useRef<string | null>(null);
  sessionIdRef.current = sessionId;

  useEffect(() => {
    const handleUnload = () => {
      if (sessionIdRef.current) endSession(sessionIdRef.current);
    };
    window.addEventListener("beforeunload", handleUnload);
    return () => window.removeEventListener("beforeunload", handleUnload);
  }, []);

  const handleFetchInfo = async (url: string) => {
    if (sessionId) endSession(sessionId);
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
        is_true_playlist: info.is_true_playlist,
        auto_import: autoImport,
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

  const handleReset = () => {
    if (sessionIdRef.current) endSession(sessionIdRef.current);
    setPhase("idle");
    setInfo(null);
    setSessionId(null);
    setSelected(new Set());
    setError(null);
  };

  return (
    <div className={STYLES.page}>
      <main className={STYLES.app}>
        <header className={STYLES.header}>
          <h1 className={STYLES.title}>Tunes</h1>
        </header>

        <UrlInput onSubmit={handleFetchInfo} disabled={phase === "fetching-info"} />

        {error && <p className={STYLES.errorBanner}>{error}</p>}

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
            {!sessionId && (
              <label className={STYLES.autoImportRow}>
                <input
                  type="checkbox"
                  checked={autoImport}
                  onChange={(e) => setAutoImport(e.target.checked)}
                />
                <span className={STYLES.autoImportLabel}>
                  Add to iTunes automatically (Windows only)
                </span>
              </label>
            )}
            <DownloadPanel
              onStart={handleStartDownload}
              starting={starting}
              selectedCount={selected.size}
              sessionId={sessionId}
              isPlaylist={info.type === "playlist"}
              zipFilename={progressState.zipFilename}
              isComplete={progressState.isComplete}
              tracks={progressState.tracks}
              importStatus={progressState.importStatus}
              onReset={handleReset}
            />
          </>
        )}
      </main>
    </div>
  );
}
