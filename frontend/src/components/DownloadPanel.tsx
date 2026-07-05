import { singleFileUrl, zipFileUrl } from "../api/client";
import type { ImportStatus } from "../hooks/useDownloadProgress";
import type { TrackProgress } from "../types";

const STYLES = {
  wrapper: "flex flex-col gap-2",
  panel: "flex items-center gap-4",
  startBtn: "bg-accent text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed",
  statusLine: "text-sm text-text-muted",
  errorLine: "text-sm text-danger",
  saveBtn: "inline-block bg-success text-white text-sm font-medium px-4 py-2.5 rounded-lg no-underline transition-colors hover:brightness-110",
  newDownloadBtn: "bg-transparent border border-border text-sm font-medium px-4 py-2.5 rounded-lg transition-colors hover:border-accent hover:text-accent",
  importLine: "text-sm text-text-muted",
  importErrorLine: "text-sm text-danger",
};

interface DownloadPanelProps {
  onStart: () => void;
  starting: boolean;
  selectedCount: number;
  sessionId: string | null;
  isPlaylist: boolean;
  zipFilename: string | null;
  isComplete: boolean;
  tracks: Map<string, TrackProgress>;
  importStatus: ImportStatus | null;
  onReset: () => void;
}

function ImportStatusLine({ importStatus }: { importStatus: ImportStatus | null }) {
  if (!importStatus) return null;

  if (importStatus.state === "importing") {
    return <p className={STYLES.importLine}>Adding to iTunes…</p>;
  }
  if (importStatus.state === "error") {
    return <p className={STYLES.importErrorLine}>iTunes import failed: {importStatus.message}</p>;
  }
  if (importStatus.message) {
    return <p className={STYLES.importLine}>{importStatus.message}</p>;
  }
  return (
    <p className={STYLES.importLine}>
      Added {importStatus.added}/{importStatus.total} to iTunes
    </p>
  );
}

export function DownloadPanel({
  onStart,
  starting,
  selectedCount,
  sessionId,
  isPlaylist,
  zipFilename,
  isComplete,
  tracks,
  importStatus,
  onReset,
}: DownloadPanelProps) {
  const singleDone = !isPlaylist
    ? [...tracks.values()].find((t) => t.status === "done" && t.filename)
    : undefined;

  return (
    <div className={STYLES.wrapper}>
      <div className={STYLES.panel}>
        {!sessionId && (
          <button
            type="button"
            className={STYLES.startBtn}
            onClick={onStart}
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
          <a
            className={STYLES.saveBtn}
            href={singleFileUrl(sessionId, singleDone.filename!)}
            download
          >
            Save {singleDone.filename}
          </a>
        )}

        {sessionId && isComplete && isPlaylist && !zipFilename && (
          <p className={STYLES.errorLine}>
            All tracks processed, but the archive wasn't created. Check the backend logs.
          </p>
        )}

        {sessionId && isComplete && (
          <button type="button" className={STYLES.newDownloadBtn} onClick={onReset}>
            New Download
          </button>
        )}
      </div>

      {sessionId && <ImportStatusLine importStatus={importStatus} />}
    </div>
  );
}
