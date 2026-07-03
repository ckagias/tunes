import type { TrackInfo, TrackProgress } from "../types";
import { StatusBadge } from "./StatusBadge";

interface TrackRowProps {
  track: TrackInfo;
  selected: boolean;
  onToggle: (url: string) => void;
  progress?: TrackProgress;
  selectable: boolean;
}

export function TrackRow({ track, selected, onToggle, progress, selectable }: TrackRowProps) {
  return (
    <li className="track-row">
      {selectable && (
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onToggle(track.url)}
        />
      )}
      {track.thumbnail && (
        <img className="track-thumb" src={track.thumbnail} alt="" loading="lazy" />
      )}
      <div className="track-meta">
        <div className="track-title">{track.title}</div>
        <div className="track-sub">
          {track.uploader}
          {track.duration && ` · ${track.duration}`}
        </div>
        {progress && progress.status === "downloading" && (
          <div className="track-progress-bar">
            <div
              className="track-progress-fill"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
        )}
        {progress?.status === "error" && (
          <div className="track-error">{progress.errorMessage}</div>
        )}
      </div>
      {progress && <StatusBadge status={progress.status} />}
    </li>
  );
}
