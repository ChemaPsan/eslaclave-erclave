"""Import adapter for running purchasing-service from the backend directory."""
import importlib,os,sys
from pathlib import Path
os.environ["ERCLAVE_SERVICE_NAME"]="purchasing-service"
service_root=Path(__file__).parent / "purchasing-service"
sys.path.insert(0,str(service_root))
app=importlib.import_module("app.main").app
