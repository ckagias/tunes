import type { ProgressEvent } from "../types";

/**
 * Opens an SSE connection to /api/progress/{sessionId} and calls onEvent for
 * each parsed event. Closes the connection automatically once an "all_done"
 * or "error" event arrives, so EventSource's built-in auto-reconnect doesn't
 * re-process a finished session.
 *
 * Returns a cleanup function the caller should invoke on unmount.
 */
export function openProgressStream(
  sessionId: string,
  onEvent: (event: ProgressEvent) => void,
): () => void {
  const source = new EventSource(`/api/progress/${encodeURIComponent(sessionId)}`);

  source.onmessage = (message) => {
    try {
      const parsed = JSON.parse(message.data) as ProgressEvent;
      onEvent(parsed);
      if (parsed.type === "all_done" || parsed.type === "error") {
        source.close();
      }
    } catch {
      // Ignore malformed frames rather than crashing the stream handler.
    }
  };

  source.onerror = () => {
    // The browser will attempt to reconnect on transient errors; if the
    // session is already gone server-side we just let it retry a couple of
    // times and give up quietly (close is safe to call multiple times).
  };

  return () => source.close();
}
