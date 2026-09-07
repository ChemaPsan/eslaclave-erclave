import importlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text


DATABASE_URL=os.getenv("ERCLAVE_TEST_DATABASE_URL","")
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason="ERCLAVE_TEST_DATABASE_URL is required for PostgreSQL integration")
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=="app" or name.startswith("app."):del sys.modules[name]
repositories=importlib.import_module("app.repositories");schemas=importlib.import_module("app.schemas")


@pytest.fixture
def context():
    engine=create_engine(DATABASE_URL,pool_pre_ping=True);tenant=f"ten_sales_test_{uuid4().hex[:12]}";repo=repositories.SalesRepository(engine)
    try:yield repo,tenant
    finally:
        with engine.begin() as connection:
            for table in ("service_evidence","service_cost_entries","service_time_entries","service_orders","delivery_lines","deliveries","order_line_reservations","order_lines","orders","audit_events","idempotency_records","quote_lines","quotes","customer_contacts","customers"):
                connection.execute(text(f"delete from sales.{table} where tenant_id=:tenant"),{"tenant":tenant})
        engine.dispose()


def worker():return schemas.WorkerReference(id="hrw_test",employee_number="E-TEST",full_name="Persona Ventas",position_name="Ejecutiva",labor_area_name="Comercial",status="active")
def customer_payload():return schemas.CustomerCreateRequest(code="CLI-TEST",commercial_name="Cliente Integracion",customer_type="company",status="active",responsible_worker_id="hrw_test",primary_contact={"name":"Contacto","email":"contacto@example.com","phone":"5512345678"},payment_terms="credit_30",currency="MXN")
def quote_payload(customer_id):return schemas.QuoteCreateRequest(code="COT-TEST",customer_id=customer_id,valid_until=date.today()+timedelta(days=15),lines=[{"product_service_id":"prs_test","quantity":Decimal("2"),"unit":"HUR","unit_price":Decimal("100"),"discount_percentage":Decimal("10")}])


def test_sales_repository_persists_calculates_isolates_and_replays(context):
    repo,tenant=context;payload=customer_payload();created=repo.create_customer(tenant,payload,worker(),"customer-key","customer-hash","usr_test")
    replay=repo.create_customer(tenant,payload,worker(),"customer-key","customer-hash","usr_test")
    assert replay.id==created.id and repo.list_customers("ten_other")==[]
    assert repo.list_customers(tenant,q="contacto@example.com")[0].id==created.id
    product=schemas.ProductReference(id="prs_test",code="SERV-TEST",name="Servicio Integracion",type="service",base_unit="HUR",status="active",target_price=100,standard_cost=50)
    quote_input=quote_payload(created.id);lines=[schemas.ResolvedQuoteLine(product=product,quantity=Decimal("2"),unit="HUR",unit_price=Decimal("100"),discount_percentage=Decimal("10"))]
    quote=repo.create_quote(tenant,quote_input,created,worker(),lines,"quote-key","quote-hash","usr_test")
    assert quote.total==Decimal("180.00") and quote.estimated_cost==Decimal("100.00") and quote.estimated_margin==Decimal("44.4444")
    submitted=repo.transition_quote(tenant,quote.id,"quoted","submit-key","submit-hash","usr_test")
    approved=repo.transition_quote(tenant,quote.id,"approved","approve-key","approve-hash","usr_test")
    assert submitted.status=="quoted" and approved.status=="approved"
    order=repo.create_order(tenant,schemas.SalesOrderCreateRequest(code="PED-TEST",quote_id=approved.id),approved,"order-key","order-hash","usr_test")
    configured=order
    assert configured.lines[0].fulfillment_status=="pending"
    service=repo.list_service_orders(tenant,order_id=order.id)[0]
    assert service.code.startswith("OS-PED-TEST-1-") and repo.list_service_orders("ten_other")==[]
    with pytest.raises(ValueError,match="service_line_requires_service_order"):
        repo.create_delivery(tenant,schemas.DeliveryCreateRequest(code="ENT-SERVICE",order_id=order.id,scheduled_date=date.today(),lines=[{"order_line_id":order.lines[0].id,"quantity":Decimal("1")}]),"delivery-service-key","delivery-service-hash","usr_test")
    planned=repo.plan_service_order(tenant,service.id,schemas.ServiceOrderPlanRequest(planned_start_date=date.today(),planned_end_date=date.today()),"service-plan-key","service-plan-hash","usr_test")
    replay=repo.plan_service_order(tenant,service.id,schemas.ServiceOrderPlanRequest(planned_start_date=date.today(),planned_end_date=date.today()),"service-plan-key","service-plan-hash","usr_test")
    assert replay.id==planned.id and replay.status=="planned"
    assigned=repo.assign_service_order(tenant,service.id,worker(),"service-assign-key","service-assign-hash","usr_test")
    started=repo.transition_service_order(tenant,service.id,"start",None,"service-start-key","service-start-hash","usr_test")
    assert assigned.status=="assigned" and started.status=="in_progress"
    with pytest.raises(ValueError,match="service_order_reason_required"):
        repo.transition_service_order(tenant,service.id,"wait",None,"service-wait-no-reason-key","service-wait-no-reason-hash","usr_test")
    waiting=repo.transition_service_order(tenant,service.id,"wait","Esperando autorizacion del cliente","service-wait-key","service-wait-hash","usr_test")
    resumed=repo.transition_service_order(tenant,service.id,"resume",None,"service-resume-key","service-resume-hash","usr_test")
    assert waiting.status=="on_hold" and resumed.status=="in_progress"
    evidenced=repo.add_service_evidence(tenant,service.id,schemas.ServiceEvidenceCreateRequest(evidence_reference="evidence://service/test"),"service-evidence-key","service-evidence-hash","usr_test")
    assert len(evidenced.evidence)==1
    repo.transition_service_order(tenant,service.id,"submit_acceptance",None,"service-submit-key","service-submit-hash","usr_test")
    with pytest.raises(ValueError,match="service_order_cost_required"):
        repo.transition_service_order(tenant,service.id,"accept",None,"service-accept-without-cost-key","service-accept-without-cost-hash","usr_test")
    timed=repo.add_service_time_entry(tenant,service.id,schemas.ServiceTimeEntryCreateRequest(worker_id="hrw_test",worked_on=date.today(),minutes=60,hourly_cost=Decimal("45")),worker(),"service-time-key","service-time-hash","usr_test")
    assert timed.time_entries[0].total_cost==Decimal("45.00")
    accepted=repo.transition_service_order(tenant,service.id,"accept",None,"service-accept-key","service-accept-hash","usr_test")
    refreshed=repo.get_order(tenant,order.id)
    assert accepted.status=="accepted" and accepted.actual_cost==Decimal("45.00")
    assert refreshed.status=="delivered" and refreshed.lines[0].delivered_quantity==Decimal("2") and refreshed.actual_cost==Decimal("45.00")
    with pytest.raises(ValueError,match="quote_not_editable"):
        repo.update_quote(tenant,quote.id,schemas.QuoteUpdateRequest(notes="late"),None,None,None,"update-key","update-hash","usr_test")


def test_sales_repository_replays_concurrent_idempotent_create(context):
    repo,tenant=context;payload=customer_payload()
    def create():
        return repo.create_customer(tenant,payload,worker(),"concurrent-customer-key","concurrent-customer-hash","usr_test")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(lambda _:create(),range(2)))
    assert results[0].id==results[1].id
    assert len(repo.list_customers(tenant))==1


def test_fulfillment_claim_is_exclusive_and_uses_postgres_line_locks(context):
    repo,tenant=context
    created=repo.create_customer(tenant,customer_payload(),worker(),"customer-product-key","customer-product-hash","usr_test")
    product=schemas.ProductReference(id="prd_test",code="PROD-TEST",name="Producto Integracion",type="product",base_unit="H87",status="active",target_price=100,standard_cost=50,inventory_item_id="itm_test")
    quote_input=schemas.QuoteCreateRequest(code="COT-PRODUCT",customer_id=created.id,valid_until=date.today()+timedelta(days=15),lines=[{"product_service_id":"prd_test","quantity":Decimal("2"),"unit":"H87","unit_price":Decimal("100")}])
    lines=[schemas.ResolvedQuoteLine(product=product,quantity=Decimal("2"),unit="H87",unit_price=Decimal("100"),discount_percentage=Decimal("0"))]
    quote=repo.create_quote(tenant,quote_input,created,worker(),lines,"quote-product-key","quote-product-hash","usr_test")
    repo.transition_quote(tenant,quote.id,"quoted","submit-product-key","submit-product-hash","usr_test")
    approved=repo.transition_quote(tenant,quote.id,"approved","approve-product-key","approve-product-hash","usr_test")
    order=repo.create_order(tenant,schemas.SalesOrderCreateRequest(code="PED-PRODUCT",quote_id=approved.id),approved,"order-product-key","order-product-hash","usr_test")
    payload=schemas.SalesOrderFulfillmentRequest(lines=[{"order_line_id":order.lines[0].id,"mode":"production"}])

    def claim(index):
        try:
            prepared=repo.prepare_order_fulfillment(tenant,order.id,payload,f"fulfillment-key-{index}",f"fulfillment-hash-{index}")
            return prepared[1]
        except ValueError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(claim,range(2)))
    assert sum(value.startswith("fulfillment-key-") for value in results)==1
    assert "sales_order_fulfillment_in_progress" in results
    winner_key=next(value for value in results if value.startswith("fulfillment-key-"))
    winner_index=winner_key.rsplit("-",1)[1]
    configured=repo.configure_order_fulfillment(tenant,order.id,[{"order_line_id":order.lines[0].id,"mode":"production","production_request_id":"psr_test"}],winner_key,f"fulfillment-hash-{winner_index}","usr_test")
    replay=repo.prepare_order_fulfillment(tenant,order.id,payload,winner_key,f"fulfillment-hash-{winner_index}")
    assert configured.fulfillment_state=="completed" and replay[0].fulfillment_state=="completed"


def test_mixed_order_creates_only_service_orders_and_acceptance_keeps_product_pending(context):
    repo,tenant=context
    created=repo.create_customer(tenant,customer_payload(),worker(),"customer-mixed-key","customer-mixed-hash","usr_test")
    service=schemas.ProductReference(id="srv_mixed",code="SERV-MIX",name="Servicio Mixto",type="service",base_unit="HUR",status="active",target_price=100,standard_cost=50)
    product=schemas.ProductReference(id="prd_mixed",code="PROD-MIX",name="Producto Mixto",type="product",base_unit="H87",status="active",target_price=200,standard_cost=80,inventory_item_id="itm_mixed")
    payload=schemas.QuoteCreateRequest(code="COT-MIX",customer_id=created.id,valid_until=date.today()+timedelta(days=15),lines=[
        {"product_service_id":"srv_mixed","quantity":Decimal("1"),"unit":"HUR","unit_price":Decimal("100")},
        {"product_service_id":"prd_mixed","quantity":Decimal("1"),"unit":"H87","unit_price":Decimal("200")},
    ])
    lines=[schemas.ResolvedQuoteLine(product=service,quantity=Decimal("1"),unit="HUR",unit_price=Decimal("100"),discount_percentage=Decimal("0")),
        schemas.ResolvedQuoteLine(product=product,quantity=Decimal("1"),unit="H87",unit_price=Decimal("200"),discount_percentage=Decimal("0"))]
    quote=repo.create_quote(tenant,payload,created,worker(),lines,"quote-mixed-key","quote-mixed-hash","usr_test")
    repo.transition_quote(tenant,quote.id,"quoted","submit-mixed-key","submit-mixed-hash","usr_test")
    approved=repo.transition_quote(tenant,quote.id,"approved","approve-mixed-key","approve-mixed-hash","usr_test")
    order=repo.create_order(tenant,schemas.SalesOrderCreateRequest(code="PED-MIX",quote_id=approved.id),approved,"order-mixed-key","order-mixed-hash","usr_test",{approved.lines[0].id:"OS-000777"})
    service_orders=repo.list_service_orders(tenant,order_id=order.id)
    assert len(service_orders)==1 and service_orders[0].order_line_id==order.lines[0].id and service_orders[0].code=="OS-000777"
    value=service_orders[0]
    repo.plan_service_order(tenant,value.id,schemas.ServiceOrderPlanRequest(planned_start_date=date.today(),planned_end_date=date.today()),"plan-mixed-key","plan-mixed-hash","usr_test")
    repo.assign_service_order(tenant,value.id,worker(),"assign-mixed-key","assign-mixed-hash","usr_test")
    repo.transition_service_order(tenant,value.id,"start",None,"start-mixed-key","start-mixed-hash","usr_test")
    repo.add_service_cost_entry(tenant,value.id,schemas.ServiceCostEntryCreateRequest(cost_type="external",description="Servicio externo",quantity=1,unit_cost=40),"cost-mixed-key","cost-mixed-hash","usr_test")
    repo.add_service_evidence(tenant,value.id,schemas.ServiceEvidenceCreateRequest(evidence_reference="evidence://mixed/1"),"evidence-mixed-key","evidence-mixed-hash","usr_test")
    repo.transition_service_order(tenant,value.id,"submit_acceptance",None,"submit-acceptance-mixed-key","submit-acceptance-mixed-hash","usr_test")
    repo.transition_service_order(tenant,value.id,"accept",None,"accept-mixed-key","accept-mixed-hash","usr_test")
    refreshed=repo.get_order(tenant,order.id)
    assert refreshed.status=="partially_delivered"
    assert refreshed.lines[0].fulfillment_status=="delivered" and refreshed.lines[1].fulfillment_status=="pending"
    assert refreshed.actual_cost==Decimal("40.00") and refreshed.actual_margin==Decimal("86.6667")


def test_cancel_and_delivery_confirmation_cannot_claim_same_order(context):
    repo,tenant=context
    created=repo.create_customer(tenant,customer_payload(),worker(),"customer-race-key","customer-race-hash","usr_test")
    product=schemas.ProductReference(id="prd_race",code="PROD-RACE",name="Producto Carrera",type="product",base_unit="H87",status="active",target_price=100,standard_cost=50,inventory_item_id="itm_race")
    quote_input=schemas.QuoteCreateRequest(code="COT-RACE",customer_id=created.id,valid_until=date.today()+timedelta(days=15),lines=[{"product_service_id":"prd_race","quantity":Decimal("1"),"unit":"H87","unit_price":Decimal("100")}])
    lines=[schemas.ResolvedQuoteLine(product=product,quantity=Decimal("1"),unit="H87",unit_price=Decimal("100"),discount_percentage=Decimal("0"))]
    quote=repo.create_quote(tenant,quote_input,created,worker(),lines,"quote-race-key","quote-race-hash","usr_test")
    repo.transition_quote(tenant,quote.id,"quoted","submit-race-key","submit-race-hash","usr_test")
    approved=repo.transition_quote(tenant,quote.id,"approved","approve-race-key","approve-race-hash","usr_test")
    order=repo.create_order(tenant,schemas.SalesOrderCreateRequest(code="PED-RACE",quote_id=approved.id),approved,"order-race-key","order-race-hash","usr_test")
    fulfillment=schemas.SalesOrderFulfillmentRequest(lines=[{"order_line_id":order.lines[0].id,"mode":"stock","allocations":[{"inventory_item_id":"itm_race","warehouse_id":"wh_race","quantity":Decimal("1")}]}])
    repo.prepare_order_fulfillment(tenant,order.id,fulfillment,"fulfill-race-key","fulfill-race-hash")
    order=repo.configure_order_fulfillment(tenant,order.id,[{"order_line_id":order.lines[0].id,"mode":"stock","inventory_item_id":"itm_race","inventory_item_code":"ART-RACE","inventory_item_name":"Articulo Carrera","reservations":[{"id":"rsv_race","warehouse_id":"wh_race","quantity":Decimal("1"),"unit_cost_snapshot":Decimal("40") }]}],"fulfill-race-key","fulfill-race-hash","usr_test")
    delivery=repo.create_delivery(tenant,schemas.DeliveryCreateRequest(code="ENT-RACE",order_id=order.id,scheduled_date=date.today(),lines=[{"order_line_id":order.lines[0].id,"quantity":Decimal("1")}]),"delivery-race-key","delivery-race-hash","usr_test")
    with pytest.raises(ValueError,match="delivery_quantity_exceeds_uncommitted"):
        repo.create_delivery(tenant,schemas.DeliveryCreateRequest(code="ENT-RACE-2",order_id=order.id,scheduled_date=date.today(),lines=[{"order_line_id":order.lines[0].id,"quantity":Decimal("1")}]),"delivery-over-key","delivery-over-hash","usr_test")

    def claim_cancel():
        try:
            repo.prepare_cancel_order(tenant,order.id,"cancel-race-key","cancel-race-hash")
            return "cancel"
        except ValueError as exc:
            return str(exc)

    def claim_confirmation():
        try:
            repo.prepare_delivery_confirmation(tenant,delivery.id,"confirm-race-key","confirm-race-hash")
            return "confirm"
        except ValueError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results=[executor.submit(claim_cancel),executor.submit(claim_confirmation)]
        results=[item.result() for item in results]
    assert sum(value in {"cancel","confirm"} for value in results)==1
    assert any(value in {"sales_order_not_deliverable","delivery_confirmation_in_progress"} for value in results)
