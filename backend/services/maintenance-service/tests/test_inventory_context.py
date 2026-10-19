"""No network/DB: producer snapshots and revoked-scope boundaries."""
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
import pytest
from erclave_common.errors import ErclaveError
from erclave_common.organization_client import OrganizationAccess

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
context=importlib.import_module('app.inventory_context')
authorities=importlib.import_module('app.authorities')
CTX={'division_ref_id':'d1','society_ref_id':'s1','division_code':'D1','division_name':'Division','cost_currency':'MXN'}

def access(divisions=True):
    return OrganizationAccess('tenant','actor',('maintenance.material_request.create',),({'id':'d1','society_id':'s1','code':'D1','name':'Division'},) if divisions else (),False,False,societies=({'id':'s1','base_currency':'MXN'},))

def test_material_context_comes_from_authoritative_warehouse_and_admin(monkeypatch):
    monkeypatch.setattr(context,'organization_access',lambda *args:access())
    assert context.material_context({'division_ref_id':'d1'},{},None,'tenant','token','actor')==CTX

def test_source_machine_cannot_cross_warehouse_division():
    authority=SimpleNamespace(machine=lambda *args:{'division_ref_id':'d2'})
    with pytest.raises(ErclaveError) as error:
        context.material_context({'division_ref_id':'d1'},{'production_machine_id':'machine'},authority,'tenant','token','actor')
    assert error.value.code=='operational_context_mismatch'

def test_replay_preserved_snapshot_still_requires_current_scope(monkeypatch):
    monkeypatch.setattr(context,'organization_access',lambda *args:access(False))
    with pytest.raises(ErclaveError) as error:
        context.guard_material({'organization_context':CTX},'tenant','token','maintenance.material_request.reconcile','actor')
    assert error.value.code=='assignment_division_denied'

def test_legacy_context_is_not_backfilled_from_current_configuration(monkeypatch):
    monkeypatch.setattr(context,'organization_access',lambda *args:replace(access(),all_divisions=True))
    assert context.guard_material({'organization_context':None},'tenant','token','permission') is None
    assert context.material_context({}, {}, None,'tenant','token','actor') is None


def test_legacy_material_requires_full_scope_even_without_scoped_history(monkeypatch):
    monkeypatch.setattr(context,'organization_access',lambda *args:access())
    with pytest.raises(ErclaveError) as error:
        context.guard_material({'organization_context':None},'tenant','token','maintenance.material_request.reconcile')
    assert error.value.code=='assignment_division_denied'
    assert context.material_divisions(SimpleNamespace(has_scoped_material_requests=lambda tenant:False),'tenant','token','maintenance.material_request.read')==['d1']

def test_reserve_retries_preserve_source_key_and_original_context():
    client=authorities.MaintenanceAuthorityClient(SimpleNamespace(hr_service_url='http://127.0.0.1',inventory_service_url='http://127.0.0.1',production_service_url='http://127.0.0.1',admin_service_url='http://127.0.0.1',authorization_timeout_seconds=1))
    calls=[]
    client._call=lambda *args:calls.append(args) or {'id':'reservation'}
    line={'item_id':'item','line_id':'line','quantity':'2.123456','unit_code':'PZA','organization_context':CTX}
    for _ in range(2):client.reserve('tenant','order','request',line,'warehouse','token','stable-key')
    assert calls[0]==calls[1]
    assert calls[0][4]['organization_context']==CTX
    assert calls[0][4]['source']=={'type':'maintenance_order','id':'order','line_id':'line'}
