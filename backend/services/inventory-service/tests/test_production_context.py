import importlib
import json
import sys
from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest
from fastapi.testclient import TestClient
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError
from erclave_common.operational_context import OperationalContext
from erclave_common.organization_client import OrganizationAccess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]
context_module = importlib.import_module("app.reservation_context")
schemas = importlib.import_module("app.schemas")
scoped = importlib.import_module("app.scoped_availability")
main = importlib.import_module("app.main")
repos = importlib.import_module("app.repositories")
auth = importlib.import_module("app.authorization")
TENANT = "ten_739ee59d765d5e14818674800d"
CTX = OperationalContext(division_ref_id="division-a", society_ref_id="society-a", division_code="A", division_name="A", cost_currency="MXN")
SCOPE = OrganizationAccess(TENANT, "actor", ("production.order.release",), ({"id":"division-a","code":"A","name":"A","society_id":"society-a"},), False, False, societies=({"id":"society-a","base_currency":"MXN"},))


def payload():
    return schemas.ReservationCreateRequest(inventory_item_id="item", warehouse_id="warehouse", quantity=Decimal("2.125"), unit="PZA", source={"type":"production_order", "id":"order", "line_id":"item:0"})


def proof():
    return {"order_id":"order", "organization_context":CTX.model_dump(), "allocation":{"line_id":"item:0","inventory_item_id":"item","warehouse_id":"warehouse","quantity":"2.125","unit":"PZA"}}


def test_proof_accepts_exact_allocation_and_explicit_legacy_null():
    assert context_module.validate_production_proof(proof(), payload()) == CTX
    assert context_module.validate_production_proof(None, payload()) is None


@pytest.mark.parametrize("field,value", [("line_id","other"),("inventory_item_id","other"),("warehouse_id","other"),("quantity","2.124999"),("quantity","NaN"),("quantity","0"),("unit","KGM")])
def test_proof_rejects_changed_allocation(field, value):
    value_proof=proof(); value_proof["allocation"][field]=value
    with pytest.raises(ErclaveError) as exc:
        context_module.validate_production_proof(value_proof,payload())
    assert exc.value.code == "operational_context_mismatch"


@pytest.mark.parametrize("value", [{}, [], {"allocation":{}}, {**proof(),"organization_context":None}, {**proof(),"allocation":{**proof()["allocation"],"quantity":"bad"}}])
def test_malformed_proof_never_becomes_legacy(value):
    with pytest.raises(ErclaveError) as exc:
        context_module.validate_production_proof(value,payload())
    assert exc.value.code == "assignment_authority_unavailable"


def test_proof_requires_matching_order_and_currency():
    value=proof(); value["order_id"]="foreign"
    with pytest.raises(ErclaveError):context_module.validate_production_proof(value,payload())
    value=proof();value["organization_context"]["cost_currency"]=None
    with pytest.raises(ErclaveError) as exc:context_module.validate_production_proof(value,payload())
    assert exc.value.code == "operational_cost_currency_unavailable"


def test_http_proof_forwards_identity_and_preserves_null(monkeypatch):
    client=context_module.ReservationContextClient(Settings(environment="local"))
    values=[proof(),None];seen=[]
    @contextmanager
    def response(req, **options):
        seen.append(req)
        yield SimpleNamespace(read=lambda:json.dumps({"data":values.pop(0)}).encode())
    monkeypatch.setattr(context_module,"open_dependency",response)
    assert client.production_context(TENANT,payload(),"Bearer synthetic","actor") == CTX
    assert client.production_context(TENANT,payload(),"Bearer synthetic","actor") is None
    assert seen[0].headers["X-tenant-id"]==TENANT
    assert seen[0].headers["X-actor-id"]=="actor"
    assert seen[0].full_url.endswith("/orders/order/reservation-context?line_id=item%3A0")


@pytest.mark.parametrize("status,code",[(403,"assignment_authority_denied"),(409,"production_creation_attempt_failed"),(500,"assignment_authority_unavailable")])
def test_http_proof_dependency_failure_is_not_legacy(monkeypatch,status,code):
    def fail(*args,**kwargs):raise HTTPError("http://synthetic",status,"denied",{},None)
    monkeypatch.setattr(context_module,"open_dependency",fail)
    with pytest.raises(ErclaveError) as exc:context_module.ReservationContextClient(Settings(environment="local")).production_context(TENANT,payload(),None,"actor")
    assert exc.value.code==code


def test_api_rechecks_scope_before_repository_or_replay():
    calls=[];scope=replace(SCOPE,divisions=())
    class Client:
        def production_context(self,*args):return CTX
        def access(self,*args):return scope
    class Repository:
        def create_reservation(self,*args,**kwargs):calls.append(1);raise AssertionError("denied command reached storage")
    app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode="demo")
    app.dependency_overrides[context_module.get_reservation_context_client]=lambda:Client()
    app.dependency_overrides[repos.get_inventory_repository]=lambda:Repository()
    try:
        http=TestClient(app);headers={"X-Tenant-Id":TENANT,"Idempotency-Key":"same-capture"}
        for _ in range(2):
            response=http.post("/v1/inventory/reservation-requests",headers=headers,json=payload().model_dump(mode="json"))
            assert response.status_code==403,response.text
        assert calls==[]
    finally:app.dependency_overrides.clear()


def test_scoped_availability_uses_exact_cost_and_never_legacy_fallback(monkeypatch):
    class Connection:
        def execute(self,*args):return SimpleNamespace(scalar=lambda:"active")
    class Engine:
        @contextmanager
        def begin(self):yield Connection()
    class Repository:
        engine=Engine()
        def _item(self,*args):return SimpleNamespace(id="item",code="IT",name="Item",status="active",use_in_recipe=True,base_unit="PZA",default_unit_cost=999)
        def _availability_rows(self,connection,tenant,item,unit,division):
            assert tenant==TENANT and division=="division-a"
            return [{"warehouse_id":"warehouse","warehouse_name":"A","available":Decimal("2"),"on_hand":Decimal("2"),"reserved":0,"unit_cost":Decimal("12.123456")}]
    monkeypatch.setattr(scoped,"validate_local_context",lambda *args:None)
    monkeypatch.setattr(scoped,"validate_cost_currency",lambda *args:None)
    requested=schemas.AvailabilityCheckRequest(division_ref_id="division-a",source={"type":"production_validation","id":"recipe"},items=[{"inventory_item_id":"item","quantity":3,"unit":"PZA"}])
    value=scoped.check_scoped_availability(Repository(),TENANT,requested,CTX)
    assert not value.available
    assert value.items[0].original_total_cost==Decimal("24.246912")
    assert value.items[0].allocations[0].original_unit_cost==Decimal("12.123456")
    assert value.items[0].cost_currency=="MXN"
    assert value.items[0].blocker_code=="insufficient_material"
    def incompatible(*args):raise ErclaveError("operational_cost_history_review_required","history",409)
    monkeypatch.setattr(scoped,"validate_cost_currency",incompatible)
    with pytest.raises(ErclaveError):scoped.check_scoped_availability(Repository(),TENANT,requested,CTX)


finished_context=importlib.import_module("app.finished_goods_context")


def finished_projection():
    return {"id":"order","code":"OP","product_service_id":"product","status":"completed","quantity":10,"unit":"PZA","unit_cost":12.123456,"original_unit_cost":"12.123456","organization_context":CTX.model_dump()}


@pytest.mark.parametrize("cost",[None,"NaN","Infinity","-1","bad"])
def test_finished_goods_rejects_missing_invalid_or_negative_exact_cost(cost):
    order=finished_projection();order["original_unit_cost"]=cost
    with pytest.raises(ErclaveError) as exc:finished_context.finished_goods_context(order,{"id":"product"},"order")
    assert exc.value.code=="operational_cost_currency_unavailable"


def test_finished_goods_preserves_exact_original_cost_and_origin():
    context,cost=finished_context.finished_goods_context(finished_projection(),{"id":"product"},"order")
    assert context==CTX and cost==Decimal("12.123456")
    with pytest.raises(ErclaveError):finished_context.finished_goods_context(finished_projection(),{"id":"foreign"},"order")
    legacy=finished_projection();legacy["organization_context"]=None
    assert finished_context.finished_goods_context(legacy,{"id":"product"},"order")== (None,None)


def test_finished_goods_scope_is_rechecked_before_receipt_replay():
    class Production:
        def get_finished_goods_candidate(self,*args):return {"order":finished_projection(),"product":{"id":"product","type":"product","status":"active","inventory_item_id":"item"}}
    class Context:
        def access(self,*args):return replace(SCOPE,divisions=())
    class Repository:
        def create_finished_goods_receipt(self,*args):raise AssertionError("unauthorized receipt reached storage")
    app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode="demo")
    app.dependency_overrides[auth.get_production_order_client]=lambda:Production()
    app.dependency_overrides[context_module.get_reservation_context_client]=lambda:Context()
    app.dependency_overrides[repos.get_inventory_repository]=lambda:Repository()
    try:
        client=TestClient(app)
        for _ in range(2):
            response=client.post("/v1/inventory/finished-goods-receipts",headers={"X-Tenant-Id":TENANT,"Idempotency-Key":"same-receipt"},json={"production_order_id":"order","warehouse_id":"warehouse","quantity":1,"received_at":"2026-10-08T12:00:00Z"})
            assert response.status_code==403,response.text
    finally:app.dependency_overrides.clear()


def test_finished_goods_payload_does_not_accept_caller_cost_or_context():
    from pydantic import ValidationError
    value={"production_order_id":"order","warehouse_id":"warehouse","quantity":1,"received_at":"2026-10-08T12:00:00Z"}
    for field,extra in (("unit_cost",1),("original_unit_cost","1"),("organization_context",CTX.model_dump())):
        with pytest.raises(ValidationError):schemas.FinishedGoodsReceiptCreate(**value,**{field:extra})


@pytest.mark.parametrize('field,value',[('inventory_item_id','other'),('warehouse_id','other'),('unit','KGM'),('quantity','2.124999'),('line_id','other')])
def test_sales_receipt_reconciliation_proof_binds_allocation(field,value):
    requested=payload().model_copy(update={'source':schemas.SourceRef(type='sales_order',id='order',line_id='item:0')})
    projected={'order_id':'order','order_line_id':'item:0','organization_context':CTX.model_dump(),'allocation':proof()['allocation']}
    client=context_module.ReservationContextClient(Settings(environment='local'))
    client.client=SimpleNamespace(get=lambda *args:projected)
    assert client.sales_context(TENANT,requested.source,'Bearer synthetic','actor',requested)==CTX
    projected['allocation'][field]=value
    with pytest.raises(ErclaveError) as exc:client.sales_context(TENANT,requested.source,'Bearer synthetic','actor',requested)
    assert exc.value.code=='operational_context_mismatch'


def test_sales_reconciliation_legacy_proof_preserves_explicit_null():
    requested=payload().model_copy(update={'source':schemas.SourceRef(type='sales_order',id='order',line_id='item:0')})
    projection={'order_id':'order','order_line_id':'item:0','organization_context':None,'allocation':proof()['allocation']}
    client=context_module.ReservationContextClient(Settings(environment='local'))
    client.client=SimpleNamespace(get=lambda *args:projection)
    assert client.sales_context(TENANT,requested.source,'Bearer synthetic','actor',requested) is None
    del projection['organization_context']
    with pytest.raises(ErclaveError) as exc:client.sales_context(TENANT,requested.source,'Bearer synthetic','actor',requested)
    assert exc.value.code=='assignment_authority_unavailable'
