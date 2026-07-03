import { singleFileUrl, zipFileUrl } from "../api/client";
import type { TrackProgress } from "../types";

interface DownloadPanelProps {
  onStart: () => void;
  starting: boolean;
  selectedCount: number;
  sessionId: string | null;
  isPlaylist: boolean;
  zipFilename: string | null;
  isComplete: boolean;
  tracks: Map<string, TrackProgress>;
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
}: DownloadPanelProps) {
  const singleDone = !isPlaylist
    ? [...tracks.values()].find((t) => t.status === "done" && t.filename)
    : undefined;

  return (
    <div className="download-panel">
      {!sessionId && (
        <button type="button" onClick={onStart} disabled={starting || selectedCount === 0}>
          {starting ? "Starting…" : `Download ${selectedCount} track${selectedCount === 1 ? "" : "s"}`}
        </button>
      )}

      {sessionId && !isComplete && <p className="status-line">Downloading and tagging…</p>}

      {sessionId && isPlaylist && zipFilename && (
        <a className="save-button" href={zipFileUrl(sessionId)} download>
          Save {zipFilename}
        </a>
      )}

      {sessionId && !isPlaylist && singleDone && (
        <a
          className="save-button"
          href={singleFileUrl(sessionId, singleDone.filename!)}
          download
        >
          Save {singleDone.filename}
        </a>
      )}

      {sessionId && isComplete && isPlaylist && !zipFilename && (
        <p className="status-line error">
          All tracks processed, but the archive wasn't created. Check the backend logs.
        </p>
      )}
    </div>
  );
}
