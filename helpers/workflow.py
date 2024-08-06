from server import PromptServer
from aiohttp import web
import os
import inspect
import json
import importlib
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import utils

root_directory = os.path.dirname(inspect.getfile(PromptServer))
workflows_directory = utils.get_config_value(
    "workflows.directory", "runcomfy/workflows")
workflows_directory = os.path.join(root_directory, workflows_directory)

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

@PromptServer.instance.routes.get("/runcomfy/workflows")
async def get_workflow(request):
    # Get the file name from the query parameter 'name'
    name = request.query.get("name")
    if not name:
        return web.Response(status=400, text="Missing 'name' query parameter")

    file = os.path.abspath(os.path.join(workflows_directory, name))
    if os.path.commonpath([file, workflows_directory]) != workflows_directory:
        return web.Response(status=403)
    
    if not os.path.exists(file):
        return web.Response(status=404, text="Workflow not found")

    return web.FileResponse(file)