"""Import adapter for running maintenance-service from the backend directory."""
import importlib,os,sys
from pathlib import Path
os.environ["ERCLAVE_SERVICE_NAME"]="maintenance-service"
service_root=Path(__file__).parent / "maintenance-service"
sys.path.insert(0,str(service_root))
app=importlib.import_module("app.main").app
