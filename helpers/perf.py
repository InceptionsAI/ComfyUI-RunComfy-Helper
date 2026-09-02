from server import PromptServer
from aiohttp import web
from datetime import datetime
import json
import logging
import math
import time

# The beacon payload is ~2KB; anything much larger is not ours
MAX_PAYLOAD_BYTES = 64 * 1024

# Global rate limit so repeated requests cannot flood the server log
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_RECORDS = 60
rate_window_start = 0.0
rate_window_count = 0

NUMBER_KEYS = (
    "canvas_ready_ms", "setup_ms", "graph_configured_ms",
    "ttfb_ms", "html_ms", "dom_content_loaded_ms",
)
BOOL_KEYS = ("incomplete", "painted")
STRING_KEYS = ("visibility", "page")
GROUP_KEYS = (
    "object_info", "bundles", "node_extensions",
    "api_misc", "templates", "resources_total",
)

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def rate_limited():
    global rate_window_start, rate_window_count
    now = time.monotonic()
    if now - rate_window_start >= RATE_LIMIT_WINDOW_SECONDS:
        rate_window_start = now
        rate_window_count = 0
    if rate_window_count >= RATE_LIMIT_MAX_RECORDS:
        return True
    rate_window_count += 1
    return False


def sanitize_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def sanitize_group(value):
    if not isinstance(value, dict):
        return None
    return {
        "count": sanitize_number(value.get("count")),
        "span_ms": sanitize_number(value.get("span_ms")),
        "bytes": sanitize_number(value.get("bytes")),
        "cached": bool(value.get("cached")),
    }


def sanitize_record(data):
    # Only known fields with expected types reach the log, so a crafted
    # payload cannot inject arbitrary content and the line size is bounded
    record = {}
    for key in NUMBER_KEYS:
        record[key] = sanitize_number(data.get(key))
    for key in BOOL_KEYS:
        record[key] = bool(data.get(key))
    for key in STRING_KEYS:
        value = data.get(key)
        record[key] = value[:128] if isinstance(value, str) else None
    for key in GROUP_KEYS:
        record[key] = sanitize_group(data.get(key))
    return record


@PromptServer.instance.routes.post("/runcomfy/perf")
async def log_perf(request):
    # Requiring the JSON content type also means cross-origin pages cannot
    # post here without a CORS preflight (text/plain would skip it)
    if request.content_type != "application/json":
        return web.Response(status=415)
    if rate_limited():
        return web.Response(status=429)
    if request.content_length and request.content_length > MAX_PAYLOAD_BYTES:
        return web.Response(status=413)
    # content_length is None for chunked requests, so also enforce the cap
    # while reading the body instead of buffering it whole. read(n) can
    # return fewer than n bytes before EOF, so loop until EOF or over-cap.
    body = b""
    while len(body) <= MAX_PAYLOAD_BYTES:
        chunk = await request.content.read(MAX_PAYLOAD_BYTES + 1 - len(body))
        if not chunk:
            break
        body += chunk
    if len(body) > MAX_PAYLOAD_BYTES:
        return web.Response(status=413)
    try:
        data = json.loads(body)
    except Exception:
        return web.Response(status=400)
    if not isinstance(data, dict):
        return web.Response(status=400)

    # Server-owned fields; the sanitized client fields cannot collide
    record = sanitize_record(data)
    record["timestamp"] = datetime.now().astimezone().isoformat(timespec="seconds")
    record["client"] = request.remote
    logging.info("[RunComfy perf] frontend load: " + json.dumps(record))
    return web.json_response({"ok": True})
