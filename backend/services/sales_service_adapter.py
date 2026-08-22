"""Import adapter for running sales-service from the backend directory."""

import importlib
import os
from pathlib import Path
import sys

os.environ["ERCLAVE_SERVICE_NAME"] = "sales-service"
service_root = Path(__file__).parent / "sales-service"
sys.path.insert(0, str(service_root))
module = importlib.import_module("app.main")
app = module.app
