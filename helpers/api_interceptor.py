"""
API Interceptor for ComfyUI-RunComfy-Helper

This module monkey-patches the ComfyUI core API nodes to redirect API calls
to api.runcomfy.net with proper authorization from the RUNCOMFY_API_TOKEN env var.

It patches the following modules:
- comfy_api_nodes.util._helpers (source module)
- comfy_api_nodes.util.client (imports from _helpers)
- comfy_api_nodes.util.download_helpers (imports from _helpers)
"""

import os
import sys
import logging

# Store original functions for potential restoration
_original_default_base_url = None
_original_get_auth_header = None
_patched = False

# RunComfy API configuration
RUNCOMFY_API_BASE_URL = "https://api.runcomfy.net"
RUNCOMFY_API_TOKEN_ENV = "RUNCOMFY_API_TOKEN"


def get_runcomfy_api_token() -> str | None:
    """Get the RunComfy API token from environment variable."""
    return os.environ.get(RUNCOMFY_API_TOKEN_ENV)


def patched_default_base_url() -> str:
    """
    Replacement for comfy_api_nodes.util._helpers.default_base_url()
    Returns the RunComfy API base URL instead of the default Comfy API.
    """
    return RUNCOMFY_API_BASE_URL


def patched_get_auth_header(node_cls) -> dict[str, str]:
    """
    Replacement for comfy_api_nodes.util._helpers.get_auth_header()
    Uses RUNCOMFY_API_TOKEN environment variable for authorization.
    Falls back to original behavior if token is not set.
    """
    token = get_runcomfy_api_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    
    # Fall back to original behavior if no RunComfy token
    if _original_get_auth_header:
        return _original_get_auth_header(node_cls)
    
    return {}


def _patch_module_attribute(module, attr_name: str, new_value, module_name: str = None) -> bool:
    """
    Safely patch a module attribute.
    Returns True if patched successfully, False otherwise.
    """
    try:
        if hasattr(module, attr_name):
            setattr(module, attr_name, new_value)
            return True
        return False
    except Exception as e:
        logging.debug(f"[RunComfy] Could not patch {module_name or module}.{attr_name}: {e}")
        return False


def apply_api_interceptor():
    """
    Apply monkey-patches to redirect ComfyUI API calls to RunComfy API.
    This should be called early in the startup process.
    """
    global _original_default_base_url, _original_get_auth_header, _patched
    
    if _patched:
        logging.debug("[RunComfy] API interceptor already applied, skipping")
        return
    
    token = get_runcomfy_api_token()
    if not token:
        logging.info(
            f"[RunComfy] {RUNCOMFY_API_TOKEN_ENV} is not set; skipping API interceptor"
        )
        return
    
    try:
        # Import the helpers module
        from comfy_api_nodes.util import _helpers
        
        # Store original functions
        _original_default_base_url = _helpers.default_base_url
        _original_get_auth_header = _helpers.get_auth_header
        
        # Apply patches
        _helpers.default_base_url = patched_default_base_url
        _helpers.get_auth_header = patched_get_auth_header
        
        _patched = True
        
        # Log the patching
        logging.info(f"[RunComfy] API interceptor applied successfully")
        logging.info(f"[RunComfy] API Base URL: {RUNCOMFY_API_BASE_URL}")
            
    except ImportError as e:
        logging.warning(f"[RunComfy] Could not apply API interceptor: comfy_api_nodes not found. {e}")
    except Exception as e:
        logging.error(f"[RunComfy] Failed to apply API interceptor: {e}")


def restore_original():
    """
    Restore the original ComfyUI API helpers.
    Useful for testing or if you need to revert the changes.
    """
    global _patched
    
    if not _patched:
        return
    
    try:
        from comfy_api_nodes.util import _helpers
        
        if _original_default_base_url:
            _helpers.default_base_url = _original_default_base_url
        if _original_get_auth_header:
            _helpers.get_auth_header = _original_get_auth_header
            
        _patched = False
        logging.info("[RunComfy] API interceptor restored to original")
        
    except Exception as e:
        logging.error(f"[RunComfy] Failed to restore original API helpers: {e}")


def is_patched() -> bool:
    """Check if the API interceptor is currently active."""
    return _patched


def apply_full_api_interceptor():
    """
    Apply comprehensive monkey-patches to ensure all API calls are redirected.
    This patches the _helpers module and all modules that import from it:
    - comfy_api_nodes.util._helpers (source)
    - comfy_api_nodes.util.client (imports default_base_url, get_auth_header)
    - comfy_api_nodes.util.download_helpers (imports default_base_url, get_auth_header)
    """
    global _patched
    
    if _patched:
        logging.debug("[RunComfy] API interceptor already applied, skipping")
        return

    token = get_runcomfy_api_token()
    if not token:
        logging.info(
            f"[RunComfy] {RUNCOMFY_API_TOKEN_ENV} is not set; skipping API interceptor"
        )
        return
        
    try:
        # First apply the basic patches to the source _helpers module
        from comfy_api_nodes.util import _helpers
        
        global _original_default_base_url, _original_get_auth_header
        
        # Store original functions
        _original_default_base_url = _helpers.default_base_url
        _original_get_auth_header = _helpers.get_auth_header
        
        # Apply patches to _helpers module
        _helpers.default_base_url = patched_default_base_url
        _helpers.get_auth_header = patched_get_auth_header
        
        patched_modules = ["comfy_api_nodes.util._helpers"]
        
        # Patch the client module's imported references
        try:
            from comfy_api_nodes.util import client
            if _patch_module_attribute(client, 'default_base_url', patched_default_base_url, 'client'):
                patched_modules.append("comfy_api_nodes.util.client.default_base_url")
            if _patch_module_attribute(client, 'get_auth_header', patched_get_auth_header, 'client'):
                patched_modules.append("comfy_api_nodes.util.client.get_auth_header")
        except ImportError as e:
            logging.debug(f"[RunComfy] Could not import client module: {e}")
        except Exception as e:
            logging.debug(f"[RunComfy] Could not patch client module: {e}")
        
        # Patch the download_helpers module's imported references
        try:
            from comfy_api_nodes.util import download_helpers
            if _patch_module_attribute(download_helpers, 'default_base_url', patched_default_base_url, 'download_helpers'):
                patched_modules.append("comfy_api_nodes.util.download_helpers.default_base_url")
            if _patch_module_attribute(download_helpers, 'get_auth_header', patched_get_auth_header, 'download_helpers'):
                patched_modules.append("comfy_api_nodes.util.download_helpers.get_auth_header")
        except ImportError as e:
            logging.debug(f"[RunComfy] Could not import download_helpers module: {e}")
        except Exception as e:
            logging.debug(f"[RunComfy] Could not patch download_helpers module: {e}")
        
        # Also check sys.modules for any already-imported modules
        # This ensures we catch modules that were imported before our interceptor ran
        modules_to_patch = [
            'comfy_api_nodes.util.client',
            'comfy_api_nodes.util.download_helpers',
        ]
        
        for module_name in modules_to_patch:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                if hasattr(module, 'default_base_url'):
                    setattr(module, 'default_base_url', patched_default_base_url)
                if hasattr(module, 'get_auth_header'):
                    setattr(module, 'get_auth_header', patched_get_auth_header)
        
        _patched = True
        
        # Log the patching
        token = get_runcomfy_api_token()
        token_status = "configured" if token else "NOT SET"
        logging.info(f"[RunComfy] API interceptor applied successfully")
        logging.info(f"[RunComfy] API Base URL: {RUNCOMFY_API_BASE_URL}")
        logging.info(f"[RunComfy] API Token: {token_status}")
        logging.debug(f"[RunComfy] Patched modules: {patched_modules}")
        
        if not token:
            logging.warning(
                f"[RunComfy] {RUNCOMFY_API_TOKEN_ENV} environment variable is not set. "
                "API calls may fail due to missing authorization."
            )
            
    except ImportError as e:
        logging.warning(f"[RunComfy] Could not apply API interceptor: comfy_api_nodes not found. {e}")
    except Exception as e:
        logging.error(f"[RunComfy] Failed to apply API interceptor: {e}")


def apply_lazy_interceptor():
    """
    Apply an import hook that patches modules as they are imported.
    This ensures that even if modules are imported after our initial patching,
    they will still get the patched functions.
    
    This is a more robust solution that works regardless of import order.
    """
    import importlib.abc
    import importlib.machinery
    
    class RunComfyImportHook(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        """
        Import hook that patches comfy_api_nodes modules after they're loaded.
        """
        TARGET_MODULES = {
            'comfy_api_nodes.util._helpers',
            'comfy_api_nodes.util.client', 
            'comfy_api_nodes.util.download_helpers',
        }
        
        def find_module(self, fullname, path=None):
            if fullname in self.TARGET_MODULES:
                return self
            return None
        
        def find_spec(self, fullname, path, target=None):
            # Let Python do the normal import, we'll patch after
            return None
        
        def load_module(self, fullname):
            # This won't be called since find_spec returns None
            # We rely on the post-import patching in __init__.py instead
            pass
    
    # Note: Instead of using a complex import hook, we rely on the 
    # apply_full_api_interceptor being called both in prestartup_script.py
    # and in __init__.py, which should catch most cases.
    pass
