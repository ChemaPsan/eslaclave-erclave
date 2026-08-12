"""Import adapter for hr-service."""
import importlib, os, sys
from pathlib import Path
os.environ["ERCLAVE_SERVICE_NAME"]="hr-service"
sys.path.insert(0,str(Path(__file__).parent/"hr-service"))
app=importlib.import_module("app.main").app
