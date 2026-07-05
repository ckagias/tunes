import { singleFileUrl, zipFileUrl } from "../api/client";
import type { InfoResponse, TrackProgress } from "../types";

const STYLES = {
  card: "bg-surface border border-border rounded-xl mb-6 p-4 flex items-center gap-4",
  thumb: "w-20 h-20 object-cover rounded-lg flex-shrink-0 bg-surface-raised",
  meta: "flex-1 min-w-0",
  title: "text-lg font-semibold overflow-hidden text-ellipsis whitespace-nowrap",
  stats: "text-sm text-text-muted mt-1",
  startBtn: "bg-accent text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0",
  saveBtn: "inline-block bg-success text-white text-sm font-medium px-4 py-2.5 rounded-lg no-underline transition-colors hover:brightness-110 flex-shrink-0",
  statusLine: "text-sm text-text-muted flex-shrink-0",
  errorLine: "text-sm text-danger flex-shrink-0",
};

function parseDuration(duration: string): number {
  const parts = duration.split(":").map(Number);
  if (parts.some(Number.isNaN)) return 0;
  return parts.reduce((total, part) => total * 60 + part, 0);
}

function formatTotal(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.round((totalSeconds % 3600) / 60);
  if (h) return `${h}h ${m}m`;
  return `${m}m`;
}

interface PlaylistSummaryProps {
  info: InfoResponse;
  selectedCount: number;
  starting: boolean;
  sessionId: string | null;
  isComplete: boolean;
  zipFilename: string | null;
  tracks: Map<string, TrackProgress>;
  onStartDownload: () => void;
}

export function PlaylistSummary({
  info,
  selectedCount,
  starting,
  sessionId,
  isComplete,
  zipFilename,
  tracks,
  onStartDownload,
}: PlaylistSummaryProps) {
  const totalSeconds = info.tracks.reduce((sum, t) => sum + parseDuration(t.duration), 0);
  const isPlaylist = info.type === "playlist";
  const singleDone = !isPlaylist
    ? [...tracks.values()].find((t) => t.status === "done" && t.filename)
    : undefined;

  return (
    <div className={STYLES.card}>
      {info.thumbnail && <img className={STYLES.thumb} src={info.thumbnail} alt="" />}
      <div className={STYLES.meta}>
        <h2 className={STYLES.title}>{info.title}</h2>
        <p className={STYLES.stats}>
          {isPlaylist ? `${info.count} tracks` : "1 track"}
          {totalSeconds > 0 && ` · ${formatTotal(totalSeconds)}`}
        </p>
      </div>

      {!sessionId && (
        <button
          type="button"
          className={STYLES.startBtn}
          onClick={onStartDownload}
          disabled={starting || selectedCount === 0}
        >
          {starting ? "Starting…" : `Download ${selectedCount} track${selectedCount === 1 ? "" : "s"}`}
        </button>
      )}

      {sessionId && !isComplete && <p className={STYLES.statusLine}>Downloading and tagging…</p>}

      {sessionId && isPlaylist && zipFilename && (
        <a className={STYLES.saveBtn} href={zipFileUrl(sessionId)} download>
          Save {zipFilename}
        </a>
      )}

      {sessionId && !isPlaylist && singleDone && (
        <a className={STYLES.saveBtn} href={singleFileUrl(sessionId, singleDone.filename!)} download>
          Save {singleDone.filename}
        </a>
      )}

      {sessionId && isComplete && isPlaylist && !zipFilename && (
        <p className={STYLES.errorLine}>Archive wasn't created.</p>
      )}
    </div>
  );
}
