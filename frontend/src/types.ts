// Mirrors backend/app/models.py — keep these in sync if the API changes.

export interface TrackInfo {
  id: string;
  title: string;
  url: string;
  duration: string;
  thumbnail: string;
  uploader: string;
}

export interface InfoResponse {
  type: "single" | "playlist";
  title: string;
  uploader: string;
  thumbnail: string;
  count: number;
  tracks: TrackInfo[];
}

export interface DownloadRequestPayload {
  urls: string[];
  titles: Record<string, string>;
  playlist_title: string;
  playlist_thumbnail: string;
  session_id?: string;
}

export interface DownloadResponse {
  session_id: string;
  is_playlist: boolean;
}

// Progress events streamed over SSE from /api/progress/{session_id}.
// The `type` discriminant matches the backend's event contract exactly.
export type ProgressEvent =
  | { type: "started"; url: string; title: string }
  | {
      type: "progress";
      url: string;
      title: string;
      percent: number;
      speed: string;
      eta: string;
    }
  | { type: "converting"; url: string; title: string }
  | {
      type: "track_done";
      url: string;
      title: string;
      filename?: string;
      session_id?: string;
    }
  | { type: "track_error"; url: string; title: string; message: string }
  | { type: "zipping"; message: string }
  | { type: "zip_ready"; session_id: string; filename: string }
  | { type: "all_done"; session_id: string }
  | { type: "keepalive" }
  | { type: "error"; message: string };

export type TrackStatus =
  | "pending"
  | "downloading"
  | "converting"
  | "done"
  | "error";

export interface TrackProgress {
  url: string;
  title: string;
  status: TrackStatus;
  percent: number;
  speed?: string;
  eta?: string;
  filename?: string;
  errorMessage?: string;
}
