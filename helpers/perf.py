from server import PromptServer
from aiohttp import web
from datetime import datetime
import os
import inspect
import json
import importlib.util

# Get the path to utils.py
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils.py')

# Load the module from the specified file
spec = importlib.util.spec_from_file_location("my_utils", utils_path)
my_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(my_utils)

root_directory = os.path.dirname(inspect.getfile(PromptServer))
perf_directory = my_utils.get_config_value("perf.directory", "runcomfy/perf")
perf_directory = os.path.join(root_directory, perf_directory)
perf_log_file = os.path.join(perf_directory, "frontend_load.jsonl")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def format_part(name, part):
    if not part:
        return None
    size = "cached" if part.get("cached") else f"{part.get('bytes', 0) / 1024:.0f}KB"
    return f"{name} {part.get('span_ms')}ms ({size})"


@PromptServer.instance.routes.post("/runcomfy/perf")
async def save_perf(request):
    data = await request.json()
    record = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "client": request.remote,
        **data,
    }

    os.makedirs(perf_directory, exist_ok=True)
    with open(perf_log_file, "a") as f:
        f.write(json.dumps(record) + "\n")

    parts = [f"total {data.get('canvas_ready_ms')}ms", f"ttfb {data.get('ttfb_ms')}ms"]
    for key in ("object_info", "bundles", "node_extensions"):
        formatted = format_part(key, data.get(key))
        if formatted:
            parts.append(formatted)
    my_utils.log("frontend load: " + " | ".join(parts), module_name="perf")

    return web.json_response({"ok": True})


@PromptServer.instance.routes.get("/runcomfy/perf")
async def get_perf(request):
    limit = int(request.query.get("limit", 50))
    if not os.path.exists(perf_log_file):
        return web.json_response([])

    with open(perf_log_file, "r") as f:
        lines = f.readlines()
    return web.json_response([json.loads(line) for line in lines[-limit:]])
