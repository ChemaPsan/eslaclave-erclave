import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]
DEFAULT_UNITS = importlib.import_module("app.seeds.units_of_measure").DEFAULT_UNITS


def test_default_unit_catalog_contains_standard_service_unit_once():
    matches = [unit for unit in DEFAULT_UNITS if unit[0] == "E48"]

    assert matches == [("E48", "Unidad de servicio", "Service unit", "serv", "service", 3)]
    assert len({unit[0] for unit in DEFAULT_UNITS}) == len(DEFAULT_UNITS)
