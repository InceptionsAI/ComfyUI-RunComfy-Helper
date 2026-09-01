from server import PromptServer
from aiohttp import web
from datetime import datetime
import json
import logging

# The beacon payload is ~2KB; anything much larger is not ours
MAX_PAYLOAD_BYTES = 64 * 1024

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


@PromptServer.instance.routes.post("/runcomfy/perf")
async def log_perf(request):
    if request.content_length and request.content_length > MAX_PAYLOAD_BYTES:
        return web.Response(status=413)
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400)
    if not isinstance(data, dict):
        return web.Response(status=400)

    # Server-owned fields go after the expansion so a crafted payload cannot
    # override them.
    record = {
        **data,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "client": request.remote,
    }
    logging.info("[RunComfy perf] frontend load: " + json.dumps(record))
    return web.json_response({"ok": True})
