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
default_workflow = utils.get_config_value(
    "workflows.default", "default.json")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

@PromptServer.instance.routes.get("/runcomfy/workflows")
async def get_workflows(request):
    # Get the file name from the query parameter 'name'
    name = request.query.get("name")
    if not name or name == "" or name == "undefined":
        name = default_workflow

    file = os.path.abspath(os.path.join(workflows_directory, name))
    if os.path.commonpath([file, workflows_directory]) != workflows_directory:
        return web.Response(status=403)
    
    if not os.path.exists(file):
        utils.log(f"Workflow {name} not found", type="WARNING")
        # Find the most recent updated file in the workflows_directory
        files = os.listdir(workflows_directory)
        files = [os.path.join(workflows_directory, file) for file in files]
        files = [file for file in files if os.path.isfile(file)]
        files = sorted(files, key=os.path.getmtime, reverse=True)
        if not files:
            return web.Response(status=404)
        file = files[0]

    return web.FileResponse(file)

@PromptServer.instance.routes.post("/runcomfy/workflows")
async def save_workflows(request):
    json_data = await request.json()
    workflows = json_data["workflows"]

    for workflow_data in workflows:
        file_name = workflow_data["file_name"]
        workflow = workflow_data["workflow"]
        is_default = "default" in workflow_data and workflow_data["default"]

        file_path = os.path.abspath(os.path.join(workflows_directory, file_name))
        if os.path.commonpath([file_path, workflows_directory]) != workflows_directory:
            return web.Response(status=403)

        sub_path = os.path.dirname(file_path)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        with open(file_path, "w") as f:
            f.write(json.dumps(workflow))

    return web.Response(status=201)