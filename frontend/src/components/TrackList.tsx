import type { InfoResponse, TrackProgress } from "../types";
import { TrackRow } from "./TrackRow";

const STYLES = {
  card: "bg-surface border border-border rounded-xl mb-6 overflow-hidden",
  header: "flex items-baseline gap-3 px-4 py-3.5 border-b border-border",
  title: "text-base font-semibold flex-1 overflow-hidden text-ellipsis whitespace-nowrap",
  count: "text-sm text-text-muted",
  toggleAllBtn: "bg-transparent p-0 text-sm text-accent hover:text-accent-hover underline transition-colors",
  list: "list-none max-h-105 overflow-y-auto",
};

interface TrackListProps {
  info: InfoResponse;
  selected: Set<string>;
  onToggle: (url: string) => void;
  onToggleAll: () => void;
  progress: Map<string, TrackProgress>;
  selectable: boolean;
}

export function TrackList({
  info,
  selected,
  onToggle,
  onToggleAll,
  progress,
  selectable,
}: TrackListProps) {
  return (
    <div className={STYLES.card}>
      <div className={STYLES.header}>
        <h2 className={STYLES.title}>{info.title}</h2>
        {info.type === "playlist" && (
          <span className={STYLES.count}>{info.count} tracks</span>
        )}
        {selectable && info.type === "playlist" && (
          <button type="button" className={STYLES.toggleAllBtn} onClick={onToggleAll}>
            {selected.size === info.tracks.length ? "Deselect all" : "Select all"}
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
