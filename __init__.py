import importlib.util
import glob
import os
import sys
from .utils import get_ext_dir

# Apply API interceptor as early as possible during node loading
# This ensures that even if prestartup_script didn't run, the interceptor is applied
try:
    from .helpers.api_interceptor import apply_full_api_interceptor
    apply_full_api_interceptor()
except Exception as e:
    import logging
    logging.debug(f"[RunComfy] Could not apply API interceptor during __init__: {e}")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

py = get_ext_dir("helpers")
files = glob.glob(os.path.join(py, "*.py"), recursive=False)
for file in files:
    name = os.path.splitext(file)[0]
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if hasattr(module, "NODE_CLASS_MAPPINGS") and getattr(module, "NODE_CLASS_MAPPINGS") is not None:
        NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
        if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS") and getattr(module, "NODE_DISPLAY_NAME_MAPPINGS") is not None:
            NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)

WEB_DIRECTORY="./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]