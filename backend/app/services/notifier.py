"""Fire-and-forget webhook telemetry. Off by default; enable by setting WEBHOOK_URL (or TELEMETRY_ENABLED=true)."""

import json
import os
import threading
import urllib.request

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()

_env_enabled = os.getenv("TELEMETRY_ENABLED", "").strip().lower()
if _env_enabled:
    TELEMETRY_ENABLED = _env_enabled in ("true", "1", "yes", "on")
else:
    TELEMETRY_ENABLED = bool(WEBHOOK_URL)


def _send_payload(payload: dict) -> None:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2.0):
            pass
    except Exception as e:
        print(f"[Telemetry] Webhook event dispatch failed: {e}")


def notify_event(
    event: str,
    client_ip: str = "",
    title: str = "",
    item_type: str = "",
    tracks_count: int = 0,
    size_bytes: int = 0,
    duration_seconds: float = 0.0,
    error: str = "",
    details: str = "",
    session_id: str = "",
) -> None:
    """Dispatch a telemetry event to WEBHOOK_URL on a background thread. No-op if telemetry is disabled."""
    if not TELEMETRY_ENABLED or not WEBHOOK_URL:
        return

    payload = {
        "event": event,
        "client_ip": client_ip,
        "title": title,
        "type": item_type,
        "tracks_count": tracks_count,
        "size_bytes": size_bytes,
        "duration_seconds": duration_seconds,
        "error": error,
        "details": details,
        "session_id": session_id,
    }
    threading.Thread(target=_send_payload, args=(payload,), daemon=True).start()
