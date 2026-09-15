import importlib,os,sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import date,datetime,timezone
from pathlib import Path
from uuid import uuid4
import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import make_url

DATABASE_URL=os.getenv("ERCLAVE_TEST_DATABASE_URL")
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason="ERCLAVE_TEST_DATABASE_URL is required")
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=="app" or name.startswith("app."):del sys.modules[name]
repo_module=importlib.import_module("app.repositories"); schemas=importlib.import_module("app.schemas")

@pytest.fixture
def repository():
    url = make_url(DATABASE_URL)
    assert url.host in {"localhost", "127.0.0.1", "::1"}
    assert url.port == 5434 and url.database == "erclave_local"
    assert os.getenv("ERCLAVE_TEST_ALLOW_TEMP_TENANTS") == "1", (
        "Temporary test tenants require explicit authorization and ERCLAVE_TEST_ALLOW_TEMP_TENANTS=1"
    )
    # Keep both this tenant and its isolation peer within VARCHAR(40).
    tenant = "ten_purchasing_test_" + uuid4().hex[:14]
    owned_tenants = [tenant, tenant + "_other"]
    value = repo_module.PurchasingRepository(DATABASE_URL)
    value.engine.dispose()
    value.engine = create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool)
    try:
        yield value, tenant
    finally:
        try:
            with value.engine.begin() as connection:
                # Exact, per-fixture identities; never clear a shared tenant on setup.
                for table in ["audit_events", "idempotency_records", "purchase_receipt_lines", "purchase_receipts", "purchase_order_lines", "purchase_orders", "requisition_lines", "requisitions", "suppliers"]:
                    connection.execute(text(f"delete from purchasing.{table} where tenant_id=any(:tenants)"), {"tenants": owned_tenants})
        finally:
            value.engine.dispose()

def line(quantity="10",price=None):return schemas.PurchaseLineInput(line_type="inventory_item",inventory_item_id="itm_test",description="Material de prueba",quantity=quantity,unit_code="H87",unit_price=price)
def service_line(quantity="1",price=None,description="Servicio especializado",unit="E48"):return schemas.PurchaseLineInput(line_type="service",description=description,quantity=quantity,unit_code=unit,unit_price=price)

def supplier_payload(code,commercial_name,tax_id):
    return schemas.SupplierWrite(code=code,commercial_name=commercial_name,legal_name=f"{commercial_name} SA DE CV",tax_id=tax_id,tax_regime="601",billing_email=f"{code.lower()}@example.com",fiscal_postal_code="01234",currency="MXN",payment_terms="cash")

def test_supplier_to_partial_receipt_cycle_and_over_receipt(repository):
    repo,tenant=repository;actor="usr_test"
    supplier=repo.create_supplier(tenant,supplier_payload("PRV-1","Proveedor Test","PTE010101AA1"),"supplier-key-001","a",actor)
    requisition=repo.create_requisition(tenant,schemas.RequisitionWrite(code="REQ-1",required_date=date.today(),lines=[line()]),"requisition-key-001","b",actor)
    requisition=repo.transition_requisition(tenant,requisition["id"],"submitted",None,"submit-key-001","c",actor)
    requisition=repo.transition_requisition(tenant,requisition["id"],"approved",None,"approve-key-001","d",actor)
    order=repo.create_order(tenant,schemas.PurchaseOrderWrite(code="OC-1",requisition_id=requisition["id"],supplier_id=supplier["id"],currency="MXN",payment_terms="cash",lines=[line(price="25")]),"order-key-001","e",actor)
    order=repo.issue_order(tenant,order["id"],"issue-key-001","f",actor)
    payload=schemas.ReceiptWrite(code="REC-1",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order["lines"][0]["id"],quantity="4",warehouse_id="wh_test")])
    receipt,plan=repo.prepare_receipt(tenant,payload,"receipt-key-001","g",actor)
    result=repo.complete_receipt(tenant,receipt,plan,[{"id":"mov_test"}],"receipt-key-001",actor)
    assert result["status"]=="completed"
    assert repo.get_order(tenant,order["id"])["status"]=="partially_received"
    excessive=schemas.ReceiptWrite(code="REC-2",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order["lines"][0]["id"],quantity="7",warehouse_id="wh_test")])
    with pytest.raises(ValueError,match="over_receipt"):repo.prepare_receipt(tenant,excessive,"receipt-key-002","h",actor)

def test_idempotency_replays_and_rejects_changed_request(repository):
    repo,tenant=repository;payload=supplier_payload("PRV-2","Proveedor Idempotente","PID010101AA2")
    first=repo.create_supplier(tenant,payload,"supplier-key-002","same","usr_test")
    second=repo.create_supplier(tenant,payload,"supplier-key-002","same","usr_test")
    assert first["id"]==second["id"]
    with pytest.raises(ValueError,match="idempotency_key_reused"):repo.create_supplier(tenant,payload,"supplier-key-002","different","usr_test")

def test_requisition_persists_and_replaces_multiple_lines_only_while_draft(repository):
    repo,tenant=repository;actor="usr_test"
    first=schemas.PurchaseLineInput(line_type="inventory_item",inventory_item_id="itm_one",description="Articulo uno",quantity="2",unit_code="H87")
    second=schemas.PurchaseLineInput(line_type="inventory_item",inventory_item_id="itm_two",description="Articulo dos",quantity="3.5",unit_code="KGM")
    payload=schemas.RequisitionWrite(code="REQ-MULTI",required_date=date.today(),priority="urgent",lines=[first,second])
    created=repo.create_requisition(tenant,payload,"req-multi-create","multi-create",actor)
    assert [line["line_number"] for line in created["lines"]]==[1,2]
    assert [line["inventory_item_ref_id"] for line in created["lines"]]==["itm_one","itm_two"]
    third=schemas.PurchaseLineInput(line_type="inventory_item",inventory_item_id="itm_three",description="Articulo tres",quantity="1",unit_code="LTR")
    updated=repo.update_requisition(tenant,created["id"],schemas.RequisitionWrite(code="REQ-MULTI",required_date=date.today(),lines=[second,third,first]),"req-multi-update","multi-update",actor)
    assert [line["inventory_item_ref_id"] for line in updated["lines"]]==["itm_two","itm_three","itm_one"]
    submitted=repo.transition_requisition(tenant,created["id"],"submitted",None,"req-multi-submit","multi-submit",actor)
    assert len(submitted["lines"])==3
    with pytest.raises(ValueError,match="requisition_not_editable"):repo.update_requisition(tenant,created["id"],payload,"req-multi-update-locked","locked",actor)

def test_requisition_rejects_duplicate_inventory_item():
    duplicate=line();duplicate.inventory_item_id="itm_same"
    with pytest.raises(ValidationError,match="duplicate_requisition_item"):
        schemas.RequisitionWrite(code="REQ-DUP",required_date=date.today(),lines=[duplicate,duplicate.model_copy()])

def test_service_line_forbids_inventory_reference_and_normalizes_snapshot_fields():
    with pytest.raises(ValidationError,match="service_inventory_item_forbidden"):
        schemas.PurchaseLineInput(line_type="service",inventory_item_id="itm_forbidden",description="Servicio",quantity="1",unit_code="E48")
    value=schemas.PurchaseLineInput(line_type="service",description="  Servicio de campo  ",quantity="1",unit_code=" e48 ")
    assert value.inventory_item_id is None
    assert value.description=="Servicio de campo"
    assert value.unit_code=="E48"

def test_supplier_fiscal_profile_is_editable_unique_per_tenant_and_normalized(repository):
    repo,tenant=repository
    payload=schemas.SupplierWrite(code="PRV-FISCAL",commercial_name="Proveedor Fiscal",legal_name="PROVEEDOR FISCAL SA DE CV",tax_id="abc-010101-aa1",tax_regime="601",billing_email="FACTURAS@EXAMPLE.COM",fiscal_postal_code="01234",fiscal_country="MX",currency="MXN",payment_terms="credit_30",contact_name="Ana Compras",email="ANA@EXAMPLE.COM")
    created=repo.create_supplier(tenant,payload,"supplier-fiscal-001","fiscal-create","usr_test")
    assert created["tax_id"]=="ABC010101AA1"
    assert created["billing_email"]=="facturas@example.com"
    updated=repo.update_supplier(tenant,created["id"],schemas.SupplierUpdate(commercial_name="Proveedor Fiscal Editado",phone="5512345678",fiscal_state="Ciudad de Mexico"),"supplier-fiscal-002","fiscal-update","usr_test")
    assert updated["commercial_name"]=="Proveedor Fiscal Editado"
    assert updated["phone"]=="5512345678"
    duplicate=schemas.SupplierWrite(code="PRV-FISCAL-2",commercial_name="Duplicado",legal_name="DUPLICADO SA DE CV",tax_id="ABC010101AA1",tax_regime="601",billing_email="dup@example.com",fiscal_postal_code="01234",currency="MXN",payment_terms="cash")
    with pytest.raises(ValueError,match="supplier_identity_conflict"):repo.create_supplier(tenant,duplicate,"supplier-fiscal-003","duplicate","usr_test")
    other_tenant=f"{tenant}_other"
    try:
        cross_tenant=repo.create_supplier(other_tenant,duplicate,"supplier-fiscal-004","cross-tenant","usr_test")
        assert cross_tenant["tax_id"]==created["tax_id"]
    finally:
        with repo.engine.begin() as connection:
            for table in ["audit_events","idempotency_records","suppliers"]:
                connection.execute(text(f"delete from purchasing.{table} where tenant_id=:tenant"),{"tenant":other_tenant})

def test_supplier_rejects_invalid_or_incomplete_fiscal_profile():
    with pytest.raises(ValidationError):schemas.SupplierWrite(code="BAD-0",commercial_name="Sin fiscal",currency="MXN",payment_terms="cash")
    with pytest.raises(ValidationError):schemas.SupplierWrite(code="BAD-1",commercial_name="Incompleto",tax_id="ABC010101AA1",currency="MXN",payment_terms="cash")
    with pytest.raises(ValidationError):schemas.SupplierWrite(code="BAD-2",commercial_name="RFC invalido",legal_name="RFC INVALIDO",tax_id="RFC-MALO",tax_regime="601",billing_email="facturas@example.com",fiscal_postal_code="01234",currency="MXN",payment_terms="cash")

def ready_order(repo,tenant,code="FLOW",lines=None):
    actor="usr_test";lines=lines or [line()]
    supplier=repo.create_supplier(tenant,supplier_payload(f"PRV-{code}",f"Proveedor {code}","PFL010101AA1"),f"supplier-{code}-key",f"supplier-{code}",actor)
    req_lines=[item.model_copy(update={"unit_price":None}) for item in lines]
    req=repo.create_requisition(tenant,schemas.RequisitionWrite(code=f"REQ-{code}",required_date=date.today(),lines=req_lines),f"req-{code}-key",f"req-{code}",actor)
    repo.transition_requisition(tenant,req["id"],"submitted",None,f"submit-{code}-key",f"submit-{code}",actor)
    req=repo.transition_requisition(tenant,req["id"],"approved",None,f"approve-{code}-key",f"approve-{code}",actor)
    order=repo.create_order(tenant,schemas.PurchaseOrderWrite(code=f"OC-{code}",requisition_id=req["id"],supplier_id=supplier["id"],currency="MXN",payment_terms="cash",lines=lines),f"order-{code}-key",f"order-{code}",actor)
    return req,repo.issue_order(tenant,order["id"],f"issue-{code}-key",f"issue-{code}",actor)

def test_order_requires_exact_approved_requisition_lines_and_cancel_restores_origin(repository):
    repo,tenant=repository;actor="usr_test"
    supplier=repo.create_supplier(tenant,supplier_payload("PRV-MATCH","Proveedor Match","PMT010101AA1"),"supplier-match-key","supplier-match",actor)
    req=repo.create_requisition(tenant,schemas.RequisitionWrite(code="REQ-MATCH",required_date=date.today(),lines=[line("5")]),"req-match-key","req-match",actor)
    repo.transition_requisition(tenant,req["id"],"submitted",None,"submit-match-key","submit-match",actor)
    req=repo.transition_requisition(tenant,req["id"],"approved",None,"approve-match-key","approve-match",actor)
    bad=schemas.PurchaseOrderWrite(code="OC-BAD",requisition_id=req["id"],supplier_id=supplier["id"],currency="MXN",payment_terms="cash",lines=[line("4",price="10")])
    with pytest.raises(ValueError,match="order_requisition_lines_mismatch"):repo.create_order(tenant,bad,"order-bad-key","order-bad",actor)
    assert repo.get_requisition(tenant,req["id"])["status"]=="approved"
    good=bad.model_copy(update={"code":"OC-GOOD","lines":[line("5",price="10")]})
    order=repo.create_order(tenant,good,"order-good-key","order-good",actor)
    edited=repo.update_order(tenant,order["id"],good.model_copy(update={"lines":[line("5",price="12")]}),"order-edit-key","order-edit",actor)
    assert edited["subtotal"]==60
    cancelled=repo.cancel_order(tenant,order["id"],"Proveedor no disponible","order-cancel-key","order-cancel",actor)
    assert cancelled["status"]=="cancelled"
    assert repo.get_requisition(tenant,req["id"])["status"]=="approved"

def test_partial_dependency_failure_is_reconciled_without_duplicate_quantities(repository):
    repo,tenant=repository
    lines=[line("2",price="10"),schemas.PurchaseLineInput(line_type="inventory_item",inventory_item_id="itm_two",description="Segundo material",quantity="3",unit_code="H87",unit_price="20")]
    _,order=ready_order(repo,tenant,"RECON",lines)
    payload=schemas.ReceiptWrite(code="REC-RECON",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=item["id"],quantity=item["quantity"],warehouse_id="wh_test") for item in order["lines"]])
    receipt,plan=repo.prepare_receipt(tenant,payload,"receipt-recon-key","receipt-recon","usr_test")
    failed=repo.complete_receipt(tenant,receipt,plan,[{"id":"mov_first"}],"receipt-recon-key","usr_test","inventory_unavailable")
    assert failed["status"]=="needs_reconciliation"
    assert [item["reconciliation_status"] for item in failed["lines"]]==["completed","failed"]
    pending,retry_plan=repo.prepare_reconciliation(tenant,receipt["id"],"reconcile-key","reconcile","usr_test")
    assert len(retry_plan)==1 and retry_plan[0]["order_line_id"]==order["lines"][1]["id"]
    completed=repo.complete_receipt(tenant,pending,retry_plan,[{"id":"mov_second"}],"reconcile-key","usr_test",operation="receipt.reconcile")
    assert completed["status"]=="completed"
    final=repo.get_order(tenant,order["id"])
    assert [item["received_quantity"] for item in final["lines"]]==[2,3]

def test_pending_receipt_claim_prevents_concurrent_over_receipt(repository):
    repo,tenant=repository
    _,order=ready_order(repo,tenant,"RACE",[line("5",price="10")])
    barrier=Barrier(2)
    def claim(suffix):
        competing=repo_module.PurchasingRepository(DATABASE_URL)
        competing.engine.dispose();competing.engine=create_engine(DATABASE_URL,pool_pre_ping=True,poolclass=NullPool)
        payload=schemas.ReceiptWrite(code=f"REC-{suffix}",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order["lines"][0]["id"],quantity="5",warehouse_id="wh_test")])
        barrier.wait()
        try:return competing.prepare_receipt(tenant,payload,f"race-{suffix}-key",f"race-{suffix}","usr_test")[0]["id"]
        except ValueError as exc:return str(exc)
        finally:competing.engine.dispose()
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,["A","B"]))
    assert sum(str(value).startswith("rcp_") for value in results)==1
    assert results.count("over_receipt")==1

def test_requisition_can_be_cancelled_with_auditable_reason(repository):
    repo,tenant=repository
    req=repo.create_requisition(tenant,schemas.RequisitionWrite(code="REQ-CANCEL",required_date=date.today(),lines=[line()]),"req-cancel-create","req-cancel-create","usr_test")
    cancelled=repo.cancel_requisition(tenant,req["id"],"Solicitud duplicada","req-cancel-key","req-cancel","usr_test")
    assert cancelled["status"]=="cancelled"
    assert cancelled["cancellation_reason"]=="Solicitud duplicada"

def test_service_requisition_order_and_partial_total_commercial_receipts(repository):
    repo,tenant=repository;actor="usr_test"
    supplier=repo.create_supplier(tenant,supplier_payload("PRV-SRV","Proveedor Servicios","PSR010101AA1"),"supplier-service-key","supplier-service",actor)
    requested=service_line("3",description="Servicio de calibracion")
    requisition=repo.create_requisition(tenant,schemas.RequisitionWrite(code="REQ-SRV",required_date=date.today(),lines=[requested]),"req-service-key","req-service",actor)
    repo.transition_requisition(tenant,requisition["id"],"submitted",None,"submit-service-key","submit-service",actor)
    requisition=repo.transition_requisition(tenant,requisition["id"],"approved",None,"approve-service-key","approve-service",actor)
    ordered=service_line("3",price="850",description="Servicio de calibracion")
    order=repo.create_order(tenant,schemas.PurchaseOrderWrite(code="OC-SRV",requisition_id=requisition["id"],supplier_id=supplier["id"],currency="MXN",payment_terms="cash",lines=[ordered]),"order-service-key","order-service",actor)
    assert order["lines"][0]["line_type"]=="service"
    assert order["lines"][0]["inventory_item_ref_id"] is None
    assert order["lines"][0]["item_code_snapshot"] is None
    assert order["lines"][0]["description"]=="Servicio de calibracion"
    order=repo.issue_order(tenant,order["id"],"issue-service-key","issue-service",actor)

    first_payload=schemas.ReceiptWrite(code="REC-SRV-1",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order["lines"][0]["id"],quantity="1")])
    first_receipt,first_plan=repo.prepare_receipt(tenant,first_payload,"receipt-service-1","receipt-service-1",actor)
    assert first_plan[0]["warehouse_id"] is None
    first=repo.complete_receipt(tenant,first_receipt,first_plan,[{"id":None}],"receipt-service-1",actor)
    assert first["status"]=="completed"
    assert first["lines"][0]["inventory_movement_ref_id"] is None
    assert repo.get_order(tenant,order["id"])["status"]=="partially_received"
    replay,replay_plan=repo.prepare_receipt(tenant,first_payload,"receipt-service-1","receipt-service-1",actor)
    assert replay["id"]==first["id"] and replay_plan is None

    second_payload=schemas.ReceiptWrite(code="REC-SRV-2",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order["lines"][0]["id"],quantity="2")])
    second_receipt,second_plan=repo.prepare_receipt(tenant,second_payload,"receipt-service-2","receipt-service-2",actor)
    second=repo.complete_receipt(tenant,second_receipt,second_plan,[{"id":None}],"receipt-service-2",actor)
    assert second["status"]=="completed"
    final=repo.get_order(tenant,order["id"])
    assert final["status"]=="received"
    assert final["lines"][0]["received_quantity"]==3
    assert repo.get_order(f"{tenant}_other",order["id"]) is None

def test_service_receipt_rejects_warehouse_and_exact_order_drift(repository):
    repo,tenant=repository;actor="usr_test"
    supplier=repo.create_supplier(tenant,supplier_payload("PRV-SRV2","Proveedor Servicios Dos","PSD010101AA1"),"supplier-service2-key","supplier-service2",actor)
    requested=service_line("2",description="Inspeccion")
    requisition=repo.create_requisition(tenant,schemas.RequisitionWrite(code="REQ-SRV2",required_date=date.today(),lines=[requested]),"req-service2-key","req-service2",actor)
    repo.transition_requisition(tenant,requisition["id"],"submitted",None,"submit-service2-key","submit-service2",actor)
    requisition=repo.transition_requisition(tenant,requisition["id"],"approved",None,"approve-service2-key","approve-service2",actor)
    drift=service_line("2",price="100",description="Inspeccion alterada")
    with pytest.raises(ValueError,match="order_requisition_lines_mismatch"):
        repo.create_order(tenant,schemas.PurchaseOrderWrite(code="OC-SRV2-BAD",requisition_id=requisition["id"],supplier_id=supplier["id"],currency="MXN",payment_terms="cash",lines=[drift]),"order-service2-bad","order-service2-bad",actor)
    order=repo.create_order(tenant,schemas.PurchaseOrderWrite(code="OC-SRV2",requisition_id=requisition["id"],supplier_id=supplier["id"],currency="MXN",payment_terms="cash",lines=[service_line("2",price="100",description="Inspeccion")]),"order-service2","order-service2",actor)
    order=repo.issue_order(tenant,order["id"],"issue-service2","issue-service2",actor)
    invalid=schemas.ReceiptWrite(code="REC-SRV2",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order["lines"][0]["id"],quantity="1",warehouse_id="wh_forbidden")])
    with pytest.raises(ValueError,match="service_warehouse_not_allowed"):
        repo.prepare_receipt(tenant,invalid,"receipt-service2","receipt-service2",actor)

def test_mixed_receipt_completes_service_even_when_inventory_fails_first(repository):
    repo,tenant=repository
    lines=[line("1",price="10"),service_line("1",price="200")]
    _,order=ready_order(repo,tenant,"MIXED",lines)
    payload=schemas.ReceiptWrite(code="REC-MIXED",purchase_order_id=order["id"],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order["lines"][0]["id"],quantity="1",warehouse_id="wh_test"),schemas.ReceiptLineInput(order_line_id=order["lines"][1]["id"],quantity="1")])
    receipt,plan=repo.prepare_receipt(tenant,payload,"receipt-mixed","receipt-mixed","usr_test")
    failed=repo.complete_receipt(tenant,receipt,plan,[None,{"id":None}],"receipt-mixed","usr_test","inventory_unavailable")
    assert failed["status"]=="needs_reconciliation"
    assert [item["reconciliation_status"] for item in failed["lines"]]==["failed","completed"]
    current=repo.get_order(tenant,order["id"])
    assert [item["received_quantity"] for item in current["lines"]]==[0,1]
    pending,retry_plan=repo.prepare_reconciliation(tenant,receipt["id"],"reconcile-mixed","reconcile-mixed","usr_test")
    assert [item["line_type"] for item in retry_plan]==["inventory_item"]
    completed=repo.complete_receipt(tenant,pending,retry_plan,[{"id":"mov_mixed"}],"reconcile-mixed","usr_test",operation="receipt.reconcile")
    assert completed["status"]=="completed"
    assert repo.get_order(tenant,order["id"])["status"]=="received"
