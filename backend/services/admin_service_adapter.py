"""Import adapter for running admin-service from the backend directory.

The service folder keeps its hyphenated name to match service ownership docs.
This adapter lets uvicorn load the FastAPI app from a Python-friendly module.
"""

import importlib
from pathlib import Path
import sys

service_root = Path(__file__).parent / "admin-service"
sys.path.insert(0, str(service_root))
module = importlib.import_module("app.main")

app = module.app
