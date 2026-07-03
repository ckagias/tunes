import type { TrackStatus } from "../types";

const LABELS: Record<TrackStatus, string> = {
  pending: "Waiting",
  downloading: "Downloading",
  converting: "Tagging",
  done: "Done",
  error: "Failed",
};

const STYLES = {
  badge: (status: TrackStatus) =>
    [
      "text-xs px-2 py-0.5 rounded-full flex-shrink-0",
      status === "done"
        ? "bg-success/15 text-success"
        : status === "error"
          ? "bg-danger/15 text-danger"
          : "bg-surface-raised text-text-muted",
    ].join(" "),
};

export function StatusBadge({ status }: { status: TrackStatus }) {
  return <span className={STYLES.badge(status)}>{LABELS[status]}</span>;
}
