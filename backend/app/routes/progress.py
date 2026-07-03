import asyncio
import json
import queue

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.services.sessions import store

router = APIRouter()


@router.get("/progress/{session_id}")
async def progress_stream(session_id: str) -> EventSourceResponse:
    async def event_generator():
        session = store.get(session_id)
        if not session:
            yield {"data": json.dumps({"type": "error", "message": "Session not found"})}
            return

        loop = asyncio.get_running_loop()
        while True:
            try:
                # queue.Queue.get is blocking; run it off the event loop so other
                # requests (and other SSE streams) aren't stalled while we wait.
                msg = await loop.run_in_executor(None, session.queue.get, True, 25)
                yield {"data": json.dumps(msg)}
                if msg.get("type") == "all_done":
                    break
            except queue.Empty:
                yield {"data": json.dumps({"type": "keepalive"})}

    return EventSourceResponse(event_generator())
