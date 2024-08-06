from server import PromptServer
from aiohttp import web
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import utils

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

@PromptServer.instance.routes.get("/runcomfy/ping")
async def ping(request):
    return web.json_response({"message": "pong"})
