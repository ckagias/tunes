import type { ImportStatus } from "../hooks/useDownloadProgress";
import type { InfoResponse, TrackProgress } from "../types";
import { TrackRow } from "./TrackRow";

const STYLES = {
  card: "bg-surface border border-border rounded-xl mb-6 overflow-hidden",
  header: "flex items-center gap-3 px-4 py-3.5 border-b border-border",
  toggleAllBtn: "bg-transparent p-0 text-sm text-accent hover:text-accent-hover underline transition-colors ml-auto",
  newDownloadBtn: "bg-transparent p-0 text-sm text-accent hover:text-accent-hover underline transition-colors ml-auto",
  autoImportRow: "flex items-center gap-1.5 shrink-0",
  autoImportLabel: "text-sm text-text-muted select-none",
  autoImportToggle: (checked: boolean) =>
    [
      "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors",
      checked ? "bg-accent" : "bg-white/10",
    ].join(" "),
  autoImportToggleKnob: (checked: boolean) =>
    [
      "inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform",
      checked ? "translate-x-[18px]" : "translate-x-1",
    ].join(" "),
  importLine: "text-sm text-text-muted",
  importErrorLine: "text-sm text-danger",
  list: "list-none max-h-105 overflow-y-auto",
};

interface TrackListProps {
  info: InfoResponse;
  selected: Set<string>;
  onToggle: (url: string) => void;
  onToggleAll: () => void;
  progress: Map<string, TrackProgress>;
  selectable: boolean;
  autoImport: boolean;
  onAutoImportChange: (value: boolean) => void;
  sessionId: string | null;
  isComplete: boolean;
  importStatus: ImportStatus | null;
  onReset: () => void;
}

function ImportStatusLine({ importStatus }: { importStatus: ImportStatus | null }) {
  if (!importStatus) return null;

  if (importStatus.state === "importing") {
    return <span className={STYLES.importLine}>Adding to iTunes…</span>;
  }
  if (importStatus.state === "error") {
    return <span className={STYLES.importErrorLine}>iTunes import failed: {importStatus.message}</span>;
  }
  if (importStatus.message) {
    return <span className={STYLES.importLine}>{importStatus.message}</span>;
  }
  return (
    <span className={STYLES.importLine}>
      Added {importStatus.added}/{importStatus.total} to iTunes
    </span>
  );
}

export function TrackList({
  info,
  selected,
  onToggle,
  onToggleAll,
  progress,
  selectable,
  autoImport,
  onAutoImportChange,
  sessionId,
  isComplete,
  importStatus,
  onReset,
}: TrackListProps) {
  return (
    <div className={STYLES.card}>
      <div className={STYLES.header}>
        {!sessionId && (
          <div className={STYLES.autoImportRow}>
            <span className={STYLES.autoImportLabel}>Add to iTunes</span>
            <button
              type="button"
              role="switch"
              aria-checked={autoImport}
              aria-label="Add to iTunes automatically"
              className={STYLES.autoImportToggle(autoImport)}
              onClick={() => onAutoImportChange(!autoImport)}
            >
              <span className={STYLES.autoImportToggleKnob(autoImport)} />
            </button>
          </div>
        )}

        {sessionId && <ImportStatusLine importStatus={importStatus} />}

        {!sessionId && selectable && info.type === "playlist" && (
          <button type="button" className={STYLES.toggleAllBtn} onClick={onToggleAll}>
            {selected.size === info.tracks.length ? "Deselect all" : "Select all"}
          </button>
        )}

        {sessionId && isComplete && (
          <button type="button" className={STYLES.newDownloadBtn} onClick={onReset}>
            New Download
          </button>
        )}
      </div>
      <ul className={STYLES.list}>
        {info.tracks.map((track) => (
          <TrackRow
            key={track.url}
            track={track}
            selected={selected.has(track.url)}
            onToggle={onToggle}
            progress={progress.get(track.url)}
            selectable={selectable}
          />
        ))}
      </ul>
    </div>
  );
}
