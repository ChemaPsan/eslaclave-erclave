"""Import adapter for running admin-service from the backend directory.

The service folder keeps its hyphenated name to match service ownership docs.
This adapter lets uvicorn load the FastAPI app from a Python-friendly module.
"""

import importlib.util
from pathlib import Path

service_main = Path(__file__).parent / "admin-service" / "app" / "main.py"
spec = importlib.util.spec_from_file_location("admin_service_app", service_main)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

app = module.app

