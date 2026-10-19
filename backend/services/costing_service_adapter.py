"""Isolated runtime for the basic cost-center catalog; analytical Costing stays planned."""
import os,sys
from pathlib import Path
os.environ['ERCLAVE_SERVICE_NAME']='costing-service'
sys.path.insert(0,str(Path(__file__).parent/'costing-service'))
from costing_app.main import app
