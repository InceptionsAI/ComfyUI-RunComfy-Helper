from server import PromptServer
from aiohttp import web
from datetime import datetime
import inspect
import json
import logging
import os

root_directory = os.path.dirname(inspect.getfile(PromptServer))
perf_directory = os.path.join(root_directory, "runcomfy", "perf")
perf_log_file = os.path.join(perf_directory, "frontend_load.jsonl")

# Rotate once the current file reaches this size, keeping one previous
# generation, so the telemetry never grows past ~2x this on disk.
MAX_LOG_BYTES = 5 * 1024 * 1024
# How much of the file tail GET reads; plenty for MAX_LIMIT records.
TAIL_READ_BYTES = 512 * 1024
MAX_LIMIT = 500

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def format_part(name, part):
    if not isinstance(part, dict):
        return None
    size = "cached" if part.get("cached") else f"{part.get('bytes', 0) / 1024:.0f}KB"
    return f"{name} {part.get('span_ms')}ms ({size})"


@PromptServer.instance.routes.post("/runcomfy/perf")
async def save_perf(request):
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

    os.makedirs(perf_directory, exist_ok=True)
    if os.path.exists(perf_log_file) and os.path.getsize(perf_log_file) >= MAX_LOG_BYTES:
        os.replace(perf_log_file, perf_log_file + ".1")
    with open(perf_log_file, "a") as f:
        f.write(json.dumps(record) + "\n")

    try:
        parts = [f"total {data.get('canvas_ready_ms')}ms", f"ttfb {data.get('ttfb_ms')}ms"]
        for key in ("object_info", "bundles", "node_extensions"):
            formatted = format_part(key, data.get(key))
            if formatted:
                parts.append(formatted)
        logging.info("[RunComfy perf] frontend load: " + " | ".join(parts))
    except Exception:
        pass

    return web.json_response({"ok": True})


@PromptServer.instance.routes.get("/runcomfy/perf")
async def get_perf(request):
    try:
        limit = min(int(request.query.get("limit", 50)), MAX_LIMIT)
    except ValueError:
        return web.Response(status=400)
    if not os.path.exists(perf_log_file):
        return web.json_response([])

    # Read only a bounded tail of the file instead of the whole log
    with open(perf_log_file, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - TAIL_READ_BYTES))
        chunk = f.read().decode("utf-8", errors="replace")

    lines = chunk.splitlines()
    if size > TAIL_READ_BYTES and lines:
        # The first line is likely partial after seeking into the middle
        lines = lines[1:]

    records = []
    for line in lines[-limit:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return web.json_response(records)
