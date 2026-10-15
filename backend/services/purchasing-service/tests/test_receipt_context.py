import importlib
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
from contextlib import contextmanager
from types import SimpleNamespace
from dataclasses import replace
import pytest
from erclave_common.errors import ErclaveError
from erclave_common.operational_context import OperationalContext
from erclave_common.organization_client import OrganizationAccess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]
module = importlib.import_module("app.receipt_context")
schemas = importlib.import_module("app.schemas")
Authority = importlib.import_module("app.authorities").PurchasingAuthorityClient
TENANT = "ten_739ee59d765d5e14818674800d"
CONTEXT = OperationalContext(division_ref_id="division-a", society_ref_id="society-a", division_code="A", division_name="A", cost_currency="MXN")


def access(divisions=True):
    return OrganizationAccess(TENANT, "actor", ("inventory.movement.create",), ({"id":"division-a", "society_id":"society-a", "code":"A", "name":"A"},) if divisions else (), False, False)


def test_cost_preserves_original_precision_and_converts_six_decimals():
    snapshot = module.cost_snapshot(CONTEXT, "USD", Decimal("4.123456"), Decimal("20"))
    assert snapshot["original_unit_cost"] == "4.123456"
    assert snapshot["unit_cost"] == "82.469120"
    assert snapshot["original_currency"] == "USD"
    assert snapshot["organization_context"]["cost_currency"] == "MXN"


@pytest.mark.parametrize("currency,rate,code", [("USD", None,"purchasing_receipt_exchange_rate_required"), ("MXN", Decimal("20"),"purchasing_receipt_exchange_rate_invalid"), ("USD", Decimal("0"),"purchasing_receipt_exchange_rate_invalid"), ("USD", Decimal("NaN"),"purchasing_receipt_exchange_rate_invalid"), ("USD", Decimal("999999999999999999"),"purchasing_receipt_exchange_rate_invalid")])
def test_missing_or_invalid_rates_fail_closed(currency, rate,code):
    with pytest.raises(ErclaveError) as exc:
        module.cost_snapshot(CONTEXT, currency, Decimal("4"), rate)
    assert exc.value.code==code and exc.value.details['field']=='cost_exchange_rate'


def test_same_currency_identity_and_rounding():
    assert module.cost_snapshot(CONTEXT, "MXN", Decimal("4.123456"), None)["unit_cost"] == "4.123456"
    assert module.cost_snapshot(CONTEXT, "USD", Decimal("1.000001"), Decimal("1.5"))["unit_cost"] == "1.500002"


@pytest.mark.parametrize("rate", ["0", "-1", "1.1234567", "NaN", "Infinity"])
def test_schema_rejects_invalid_rate(rate):
    with pytest.raises(ValueError):
        schemas.ReceiptWrite(code="R", purchase_order_id="o", received_at="2026-10-12T00:00:00Z", cost_exchange_rate=rate, lines=[{"order_line_id":"l","quantity":"1"}])


class Connection:
    def __init__(self, row): self.row=row
    def execute(self, query, parameters):
        assert parameters == {"t":TENANT,"r":"receipt-a","l":"line-a"}
        return self
    def mappings(self): return self
    def first(self): return self.row
    @contextmanager
    def connect(self): yield self


def row():
    return {"receipt_id":"receipt-a","purchase_order_id":"order-a","receipt_line_id":"line-a","order_line_id":"order-line-a",
            "inventory_item_id":"item-a","warehouse_id":"warehouse-a","unit":"PZA","quantity":Decimal("2.5"),
            "inventory_idempotency_key":"purchase-receipt-line-a","received_at":datetime(2026,10,12,tzinfo=timezone.utc),
            "inventory_context_snapshot":module.cost_snapshot(CONTEXT,"USD",Decimal("4.123456"),Decimal("20")),
            "line_type":"inventory_item","receipt_status":"needs_reconciliation","order_status":"partially_received"}


def proof(value, granted=True):
    authority=SimpleNamespace(organization_access=lambda *args: access(granted))
    return module.receipt_proof(SimpleNamespace(engine=Connection(value)),authority,TENANT,"receipt-a","line-a","Bearer test","actor")


def test_proof_uses_durable_snapshot_during_recovery():
    value = proof(row())
    assert value["receipt_line_id"] == "line-a"
    assert value["unit_cost"] == "82.469120"
    assert value["quantity"] == "2.5"
    assert value["occurred_at"] == "2026-10-12T00:00:00+00:00"


@pytest.mark.parametrize("change,code", [({"inventory_context_snapshot":None}, "operational_cost_history_review_required"), ({"order_status":"cancelled"}, "receipt_not_reconcilable"), ({"line_type":"service"}, "receipt_not_reconcilable"), ({"receipt_status":"draft"}, "receipt_not_reconcilable")])
def test_proof_rejects_unready_or_legacy_source(change, code):
    with pytest.raises(ErclaveError) as exc: proof({**row(), **change})
    assert exc.value.code == code


def test_proof_requires_current_scope_and_tenant_match():
    with pytest.raises(ErclaveError) as exc: proof(row(), False)
    assert exc.value.code == "assignment_division_denied"
    with pytest.raises(ErclaveError) as exc: proof(None)
    assert exc.value.code == "receipt_not_found"


def test_receive_sends_converted_cost_unique_receipt_source_and_stable_key():
    authority = Authority.__new__(Authority)
    authority.inventory="http://127.0.0.1:8002"
    calls=[]
    authority._inventory_call=lambda *args: calls.append(args) or {"id":"movement-a"}
    line={"inventory_item_id":"item-a","warehouse_id":"warehouse-a","quantity":Decimal("2.5"),"unit_code":"PZA", "received_at":"2026-10-12T00:00:00Z", "receipt_line_id":"line-a", "inventory_context_snapshot":row()["inventory_context_snapshot"]}
    authority.receive(TENANT,line,"receipt-a","order-a","Bearer test","stable-key")
    payload=calls[0][4]
    assert payload["source"] == {"type":"purchase_receipt","id":"receipt-a","line_id":"line-a"}
    assert payload["unit_cost"] == "82.469120"
    assert calls[0][-1] == "stable-key"
    with pytest.raises(ErclaveError): authority.receive(TENANT,{**line,"inventory_context_snapshot":None},"receipt-a","order-a",None,"stable-key")
    assert len(calls) == 1


def test_preparation_inherits_order_context_and_document_currency():
    order={"organization_context":CONTEXT.model_dump(),"currency":"USD","lines":[{"id":"l","line_type":"inventory_item","unit_price":Decimal("4.123456")}]}
    repository=SimpleNamespace(get_order=lambda *args:order)
    organization=replace(access(), societies=({"id":"society-a","base_currency":"MXN"},))
    authority=SimpleNamespace(warehouse=lambda *args:{"id":"w","status":"active","division_ref_id":"division-a"}, organization_access=lambda *args:organization)
    payload=schemas.ReceiptWrite(code="R",purchase_order_id="o",received_at="2026-10-12T00:00:00Z",cost_exchange_rate="20",lines=[{"order_line_id":"l","quantity":"1","warehouse_id":"w"}])
    result=module.ReceiptContext(repository,authority).prepare(TENANT,payload,"Bearer test","actor")
    assert result["l"]["organization_context"] == CONTEXT.model_dump()
    assert result["l"]["unit_cost"] == "82.469120"
    authority.warehouse=lambda *args:{"status":"active","division_ref_id":"foreign"}
    with pytest.raises(ErclaveError) as exc: module.ReceiptContext(repository,authority).prepare(TENANT,payload,None,"actor")
    assert exc.value.code == "assignment_division_denied"
    authority.warehouse=lambda *args:{"status":"active"}
    with pytest.raises(ErclaveError) as exc: module.ReceiptContext(repository,authority).prepare(TENANT,payload,None,"actor")
    assert exc.value.code == "operational_context_required"


@pytest.mark.parametrize("supplier,assignment", [("inactive",{"status":"active","society_ref_id":"society-a"}), ("active",None), ("active",{"status":"inactive","society_ref_id":"society-a"}), ("active",{"status":"active","society_ref_id":"foreign"})])
def test_supplier_assignment_required_for_physical_receipt(supplier, assignment):
    class SupplierConnection:
        def execute(self, query, parameters):
            assert parameters["t"] == TENANT
            return self
        def scalar(self): return supplier
        def mappings(self): return self
        def first(self): return assignment
    with pytest.raises(ErclaveError) as exc: module.require_supplier(SupplierConnection(),TENANT,"supplier-a",CONTEXT)
    assert exc.value.code == "operational_context_resource_unavailable"


@pytest.mark.parametrize('other_currency',['MXN','EUR'])
def test_receipt_cannot_cross_order_division_even_same_currency(other_currency):
    order={"organization_context":CONTEXT.model_dump(),"currency":"USD","lines":[{"id":i,"line_type":"inventory_item","unit_price":Decimal("4.12")} for i in ('a','b')]}
    divisions=({'id':'division-a','society_id':'society-a','code':'A','name':'A'}, {'id':'division-b','society_id':'society-b','code':'B','name':'B'})
    organization=replace(access(),divisions=divisions,societies=({'id':'society-a','base_currency':'MXN'}, {'id':'society-b','base_currency':other_currency}))
    authority=SimpleNamespace(warehouse=lambda tenant,id_,auth:{'status':'active','division_ref_id':id_},organization_access=lambda *args:organization)
    payload=schemas.ReceiptWrite(code='R',purchase_order_id='o',received_at='2026-10-12T00:00:00Z',cost_exchange_rate='20',lines=[{'order_line_id':i,'warehouse_id':'division-'+i,'quantity':'1'} for i in ('a','b')])
    with pytest.raises(ErclaveError) as exc:module.ReceiptContext(SimpleNamespace(get_order=lambda *args:order),authority).prepare(TENANT,payload,None,'actor')
    assert exc.value.code=='operational_context_mismatch'
    assert exc.value.details['field']=='lines.1.warehouse_id'


def test_document_price_two_decimals_and_fractional_rate_preserve_base_six():
    snapshot=module.cost_snapshot(CONTEXT,'USD',Decimal('4.12'),Decimal('20.123456'))
    assert snapshot['original_unit_cost']=='4.12'
    assert snapshot['unit_cost']=='82.908639'


def test_receipt_rejects_naive_date_before_persistence():
    with pytest.raises(ValueError,match='purchase_receipt_timezone_required'):
        schemas.ReceiptWrite(code='R',purchase_order_id='o',received_at='2026-10-12T12:30:00',lines=[{'order_line_id':'l','quantity':'1'}])


def test_whole_receipt_scope_rejects_one_foreign_or_legacy_physical_line():
    repository=SimpleNamespace(has_scoped_receipts=lambda tenant:True)
    authority=SimpleNamespace(organization_access=lambda *args:access())
    visible={'inventory_context_snapshot':module.cost_snapshot(CONTEXT,'MXN','4.12',None)}
    foreign={'inventory_context_snapshot':module.cost_snapshot(CONTEXT.model_copy(update={'division_ref_id':'foreign'}),'MXN','4.12',None)}
    for hidden in [foreign,{'warehouse_ref_id':'legacy-warehouse'}]:
        with pytest.raises(ErclaveError) as exc:module.authorize_receipt(repository,authority,TENANT,{'lines':[visible,hidden]},'inventory.movement.create',None,'actor')
        assert exc.value.code=='assignment_division_denied'
    # Services now inherit scope too; undimensioned history is fullscope only.
    with pytest.raises(ErclaveError):module.authorize_receipt(repository,authority,TENANT,{'lines':[{'warehouse_ref_id':None}]},'purchasing.receipt.read',None,'actor')
    module.authorize_receipt(repository,SimpleNamespace(organization_access=lambda *args:replace(access(),all_divisions=True)),TENANT,{'lines':[{'warehouse_ref_id':None}]},'purchasing.receipt.read',None,'actor')
