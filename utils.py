import json
import os

config = None

def is_logging_enabled():
    config = get_extension_config()
    if "logging" not in config:
        return False
    return config["logging"]

def log(message, type=None, module_name=None):
    if not is_logging_enabled():
        return

    if type is not None:
        message = f"[{type}] {message}"
    
    if module_name is None:
        module_name = "common"

    print(f"(runcomfy:{module_name}) {message}")
    
def get_ext_dir(subpath=None, mkdir=False):
    dir = os.path.dirname(__file__)
    if subpath is not None:
        dir = os.path.join(dir, subpath)

    dir = os.path.abspath(dir)

    if mkdir and not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def get_extension_config(reload=False):
    global config
    if reload == False and config is not None:
        return config

    config_path = get_ext_dir("runcomfy.config.json")
    if not os.path.exists(config_path):
        log(f"Failed to load config at {config_path}", type="ERROR")
        raise FileNotFoundError(f"Failed to load config at {config_path}")

    with open(config_path, "r") as f:
        config = json.loads(f.read())
    return config


def get_config_value(key, default=None, throw=False):
    split = key.split(".")
    obj = get_extension_config()
    for s in split:
        if s in obj:
            obj = obj[s]
        else:
            if throw:
                raise KeyError("Configuration key missing: " + key)
            else:
                return default
    return obj
