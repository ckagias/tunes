import type { TrackInfo, TrackProgress } from "../types";
import { StatusBadge } from "./StatusBadge";

const STYLES = {
  row: "flex items-center gap-3 px-4 py-2.5 border-b border-border last:border-b-0",
  checkbox: "accent-accent",
  thumb: "w-12 h-12 object-cover rounded-md flex-shrink-0",
  meta: "flex-1 min-w-0",
  title: "text-sm overflow-hidden text-ellipsis whitespace-nowrap",
  sub: "text-xs text-text-muted",
  progressTrack: "h-1 bg-border rounded-full mt-1.5 overflow-hidden",
  progressFill: "h-full bg-accent transition-[width] duration-200 ease-out",
  error: "text-xs text-danger mt-1",
};

interface TrackRowProps {
  track: TrackInfo;
  selected: boolean;
  onToggle: (url: string) => void;
  progress?: TrackProgress;
  selectable: boolean;
}

export function TrackRow({ track, selected, onToggle, progress, selectable }: TrackRowProps) {
  return (
    <li className={STYLES.row}>
      {selectable && (
        <input
          type="checkbox"
          className={STYLES.checkbox}
          checked={selected}
          onChange={() => onToggle(track.url)}
        />
      )}
      {track.thumbnail && (
        <img className={STYLES.thumb} src={track.thumbnail} alt="" loading="lazy" />
      )}
      <div className={STYLES.meta}>
        <div className={STYLES.title}>{track.title}</div>
        <div className={STYLES.sub}>
          {track.uploader}
          {track.duration && ` · ${track.duration}`}
        </div>
        {progress && progress.status === "downloading" && (
          <div className={STYLES.progressTrack}>
            <div
              className={STYLES.progressFill}
              style={{ width: `${progress.percent}%` }}
            />
          </div>
        )}
        {progress?.status === "error" && (
          <div className={STYLES.error}>{progress.errorMessage}</div>
        )}
      </div>
      {progress && <StatusBadge status={progress.status} />}
    </li>
  );
}
