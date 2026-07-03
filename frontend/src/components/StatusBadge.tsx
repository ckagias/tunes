import type { TrackStatus } from "../types";

const LABELS: Record<TrackStatus, string> = {
  pending: "Waiting",
  downloading: "Downloading",
  converting: "Tagging",
  done: "Done",
  error: "Failed",
};

export function StatusBadge({ status }: { status: TrackStatus }) {
  return <span className={`status-badge status-${status}`}>{LABELS[status]}</span>;
}
