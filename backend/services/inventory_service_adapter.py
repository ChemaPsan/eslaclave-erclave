"""Import adapter for inventory-service."""
import importlib, os, sys
from pathlib import Path
os.environ["ERCLAVE_SERVICE_NAME"] = "inventory-service"
sys.path.insert(0, str(Path(__file__).parent / "inventory-service"))
app = importlib.import_module("app.main").app
