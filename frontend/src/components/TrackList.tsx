import type { InfoResponse, TrackProgress } from "../types";
import { TrackRow } from "./TrackRow";

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
    <div className="track-list">
      <div className="track-list-header">
        <h2>{info.title}</h2>
        {info.type === "playlist" && (
          <span className="track-count">{info.count} tracks</span>
        )}
        {selectable && info.type === "playlist" && (
          <button type="button" className="link-button" onClick={onToggleAll}>
            {selected.size === info.tracks.length ? "Deselect all" : "Select all"}
          </button>
        )}
      </div>
      <ul>
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
