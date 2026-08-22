import importlib
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]
main = importlib.import_module("app.main")
sales_api = importlib.import_module("app.api")
repos = importlib.import_module("app.repositories")
authorities = importlib.import_module("app.authorities")
authorization = importlib.import_module("app.authorization")
schemas = importlib.import_module("app.schemas")
from erclave_common.config import Settings

app = main.app
TENANT = "ten_demo"
NOW = datetime.now(timezone.utc)


def customer(status="active"):
    return schemas.CustomerRead(id="cus_1", code="CLI-001", commercial_name="Cliente Demo", customer_type="company", status=status, responsible_worker_id="hrw_1", responsible_worker_name="María Ventas", payment_terms="credit_30", currency="MXN", credit_limit=10000, contacts=[schemas.ContactRead(id="sco_1", name="Ana Compras", email="ana@example.com", phone="5512345678", is_primary=True, status="active")], created_at=NOW, updated_at=NOW)


def quote(status="draft"):
    return schemas.QuoteRead(id="quo_1", code="COT-001", customer_id="cus_1", customer_code="CLI-001", customer_name="Cliente Demo", responsible_worker_id="hrw_1", responsible_worker_name="María Ventas", status=status, currency="MXN", payment_terms="credit_30", valid_until=date.today() + timedelta(days=15), subtotal=200, discount_total=20, total=180, estimated_cost=100, estimated_margin=Decimal("44.4444"), lines=[schemas.QuoteLineRead(id="sql_1", line_number=1, product_service_id="prd_1", product_service_code="SERV-1", product_service_name="Servicio", product_service_type="service", unit="HUR", quantity=2, unit_price=100, discount_percentage=10, subtotal=200, discount_amount=20, total=180, standard_unit_cost_snapshot=50, estimated_cost=100)], created_at=NOW, updated_at=NOW)


def order(status="ready"):
    line=schemas.SalesOrderLineRead(id="sol_1",quote_line_id="sql_1",line_number=1,product_service_id="prd_1",product_service_code="SERV-1",product_service_name="Servicio",product_service_type="service",unit="HUR",ordered_quantity=2,delivered_quantity=0,unit_price=100,discount_percentage=10,total=180,standard_unit_cost_snapshot=50,estimated_cost=100,fulfillment_mode="service",fulfillment_status="ready")
    return schemas.SalesOrderRead(id="sor_1",code="PED-001",quote_id="quo_1",quote_code="COT-001",customer_id="cus_1",customer_code="CLI-001",customer_name="Cliente Demo",responsible_worker_id="hrw_1",responsible_worker_name="Maria Ventas",status=status,currency="MXN",payment_terms="credit_30",subtotal=200,discount_total=20,total=180,estimated_cost=100,estimated_margin=Decimal("44.4444"),lines=[line],created_at=NOW,updated_at=NOW)


def delivery(status="draft"):
    line=schemas.DeliveryLineRead(id="sdl_1",order_line_id="sol_1",line_number=1,product_service_id="prd_1",product_service_code="SERV-1",product_service_name="Servicio",unit="HUR",quantity=2)
    return schemas.DeliveryRead(id="del_1",code="ENT-001",order_id="sor_1",order_code="PED-001",customer_id="cus_1",customer_name="Cliente Demo",status=status,scheduled_date=date.today(),lines=[line],created_at=NOW,updated_at=NOW)


class FakeRepository:
    def list_customers(self, tenant_id, status=None, q=None): return [customer()] if tenant_id == TENANT else []
    def get_customer(self, tenant_id, customer_id): return customer() if tenant_id == TENANT and customer_id == "cus_1" else None
    def create_customer(self, tenant_id, payload, worker, key, fingerprint, actor): return customer(payload.status)
    def update_customer(self, tenant_id, customer_id, payload, worker, key, fingerprint, actor): return customer(payload.status or "active")
    def list_quotes(self, tenant_id, status=None, customer_id=None): return [quote(status or "draft")] if tenant_id == TENANT else []
    def get_quote(self, tenant_id, quote_id): return quote() if tenant_id == TENANT and quote_id == "quo_1" else None
    def create_quote(self, tenant_id, payload, customer_value, worker, lines, key, fingerprint, actor): return quote()
    def update_quote(self, tenant_id, quote_id, payload, customer_value, worker, lines, key, fingerprint, actor): return quote()
    def transition_quote(self, tenant_id, quote_id, target, key, fingerprint, actor): return quote(target)
    def list_orders(self, tenant_id, status=None, customer_id=None): return [order(status or "ready")]
    def get_order(self, tenant_id, order_id): return order() if order_id == "sor_1" else None
    def create_order(self, tenant_id, payload, quote_value, key, fingerprint, actor): return order("confirmed")
    def configure_order_fulfillment(self, tenant_id, order_id, resolved, key, fingerprint, actor): return order("ready")
    def cancel_order(self, tenant_id, order_id, reason, key, fingerprint, actor): return order("cancelled")
    def list_deliveries(self, tenant_id, status=None, order_id=None): return [delivery(status or "draft")]
    def get_delivery(self, tenant_id, delivery_id): return delivery() if delivery_id == "del_1" else None
    def create_delivery(self, tenant_id, payload, key, fingerprint, actor): return delivery()
    def delivery_consumption_plan(self, tenant_id, delivery_id): return (delivery(), []) if delivery_id == "del_1" else None
    def prepare_delivery_confirmation(self, tenant_id, delivery_id, key, fingerprint): return (delivery(), [], key) if delivery_id == "del_1" else None
    def mark_delivery_reconciliation(self, tenant_id, delivery_id): pass
    def confirm_delivery(self, tenant_id, delivery_id, consumptions, key, fingerprint, actor): return delivery("confirmed")
    def cancel_delivery(self, tenant_id, delivery_id, reason, key, fingerprint, actor): return delivery("cancelled")


class FakeAuthority:
    def list_catalog(self, tenant_id, catalog_code, authorization):
        values = {
            "currencies": [
                {"id": "cat_mxn", "code": "MXN", "name_es": "Peso mexicano", "name_en": "Mexican peso", "status": "active"},
                {"id": "cat_usd", "code": "USD", "name_es": "Dólar estadounidense", "name_en": "US dollar", "status": "active"},
            ],
            "payment_terms": [
                {"id": "cat_c30", "code": "credit_30", "name_es": "Crédito 30 días", "name_en": "Net 30", "status": "active"},
            ],
        }
        return values[catalog_code]

    def require_catalog_item(self, tenant_id, catalog_code, code, authorization):
        matching = [item for item in self.list_catalog(tenant_id, catalog_code, authorization) if item["code"] == code]
        if not matching:
            raise ValueError("catalog_item_not_found")
        return matching[0]

    def get_worker(self, tenant_id, worker_id, authorization):
        if worker_id != "hrw_1": raise Exception("unexpected worker")
        return schemas.WorkerReference(id="hrw_1", employee_number="E-001", full_name="María Ventas", position_name="Ejecutiva", labor_area_name="Comercial", status="active")
    def get_product(self, tenant_id, product_id, authorization):
        return schemas.ProductReference(id=product_id, code="SERV-1", name="Servicio", type="service", base_unit="HUR", status="active", target_price=100, standard_cost=50)
    def require_unit(self, tenant_id, code, authorization): return code.upper()
    def request_production(self, *args): return {"id":"psr_1"}
    def reserve_stock(self, *args): return {"id":"rsv_1","unit_cost_snapshot":12}
    def release_reservation(self, *args): return {"id":"rsv_1"}
    def consume_reservation(self, *args): return {"id":"mov_1","unit_cost":12}


class FakeAdminSessionClient:
    def __init__(self, active_modules, permissions):
        self.context = {"tenant": {"id": TENANT, "status": "active"}, "user": {"id": "usr_sales"}, "active_modules": active_modules, "permissions": permissions}

    def get_context(self, tenant_id, token):
        return self.context


def client():
    app.dependency_overrides[repos.get_sales_repository] = lambda: FakeRepository()
    app.dependency_overrides[authorities.get_sales_authority_client] = lambda: FakeAuthority()
    return TestClient(app)


def teardown_function(): app.dependency_overrides.clear()


def headers(command=False):
    result = {"X-Tenant-Id": TENANT, "X-Actor-Id": "usr_demo"}
    if command: result["Idempotency-Key"] = "sales-test-001"
    return result


def customer_payload(status="active"):
    return {"code":"CLI-001","commercial_name":"Cliente Demo","customer_type":"company","status":status,"responsible_worker_id":"hrw_1","primary_contact":{"name":"Ana Compras","email":"ANA@example.com","phone":"5512345678"},"payment_terms":"credit_30","currency":"MXN"}


def quote_payload(unit="HUR"):
    return {"code":"COT-001","customer_id":"cus_1","valid_until":(date.today()+timedelta(days=15)).isoformat(),"lines":[{"product_service_id":"prd_1","quantity":2,"unit":unit,"unit_price":100,"discount_percentage":10}]}


def test_quote_and_order_business_codes_are_normalized_for_authoritative_use():
    quote_request=schemas.QuoteCreateRequest.model_validate(quote_payload() | {"code":"  cot.central-0001  "})
    order_request=schemas.SalesOrderCreateRequest.model_validate({"code":"  ped.central_0001  ","quote_id":"quo_1"})
    assert quote_request.code=="COT.CENTRAL-0001"
    assert order_request.code=="PED.CENTRAL_0001"
    assert sales_api.fingerprint(quote_request)==sales_api.fingerprint(schemas.QuoteCreateRequest.model_validate(quote_payload() | {"code":"COT.CENTRAL-0001"}))


def test_quote_and_order_reject_codes_outside_business_code_contract():
    c=client()
    invalid_quote=quote_payload() | {"code":"COT 001"}
    assert c.post("/v1/sales/quotes",headers=headers(True),json=invalid_quote).status_code==422
    assert c.post("/v1/sales/orders",headers=headers(True),json={"code":"PED/001","quote_id":"quo_1"}).status_code==422


def test_health_reference_data_and_tenant_scope():
    c=client(); assert c.get("/health").status_code==200
    assert c.get("/v1/sales/reference-data",headers=headers()).json()["data"]["currencies"][0]["code"]=="MXN"
    assert c.get("/v1/sales/customers",headers=headers()).status_code==200
    assert c.get("/v1/sales/customers").status_code==400


def test_customer_requires_idempotency_responsible_and_valid_contact():
    c=client(); assert c.post("/v1/sales/customers",headers=headers(),json=customer_payload()).status_code==400
    response=c.post("/v1/sales/customers",headers=headers(True),json=customer_payload())
    assert response.status_code==201 and response.json()["data"]["responsible_worker_id"]=="hrw_1"
    invalid=customer_payload(); invalid["primary_contact"]["email"]="not-an-email"
    assert c.post("/v1/sales/customers",headers=headers(True),json=invalid).status_code==422


def test_customer_rejects_blank_required_text_and_accepts_rfc_with_enye():
    c=client()
    blank_name=customer_payload(); blank_name["commercial_name"]="   "
    assert c.post("/v1/sales/customers",headers=headers(True),json=blank_name).status_code==422
    blank_contact=customer_payload(); blank_contact["primary_contact"]["name"]="\t "
    assert c.post("/v1/sales/customers",headers=headers(True),json=blank_contact).status_code==422
    valid=customer_payload(); valid.update({"legal_name":"Empresa Ñandú SA de CV","tax_id":"\u00d1AAA010101AAA","billing_email":"facturas@example.com"})
    assert c.post("/v1/sales/customers",headers=headers(True),json=valid).status_code==201


def test_quote_uses_authoritative_unit_and_server_totals():
    c=client(); response=c.post("/v1/sales/quotes",headers=headers(True),json=quote_payload())
    assert response.status_code==201 and response.json()["data"]["total"]=="180"
    mismatch=c.post("/v1/sales/quotes",headers=headers(True),json=quote_payload("PZ"))
    assert mismatch.status_code==422 and mismatch.json()["error"]["code"]=="quote_unit_mismatch"


def test_quote_transitions_are_explicit_and_revalidated():
    response=client().post("/v1/sales/quotes/quo_1/submit",headers=headers(True))
    assert response.status_code==200 and response.json()["data"]["status"]=="quoted"


def test_billing_profile_is_optional_but_complete_when_started():
    payload=customer_payload(); payload["tax_id"]="ABC010101ABC"
    response=client().post("/v1/sales/customers",headers=headers(True),json=payload)
    assert response.status_code==422


def test_firebase_authorization_rejects_disabled_sales_module():
    c=client()
    app.dependency_overrides[authorization.get_settings]=lambda:Settings(auth_mode="firebase")
    app.dependency_overrides[authorization.get_admin_session_client]=lambda:FakeAdminSessionClient([], ["sales.customer.read"])
    response=c.get("/v1/sales/customers",headers={"X-Tenant-Id":TENANT,"Authorization":"Bearer local-test"})
    assert response.status_code==403 and response.json()["error"]["code"]=="module_not_enabled"


def test_firebase_read_only_sales_user_can_read_without_mutation_permissions():
    c=client()
    app.dependency_overrides[authorization.get_settings]=lambda:Settings(auth_mode="firebase")
    app.dependency_overrides[authorization.get_admin_session_client]=lambda:FakeAdminSessionClient(["sales"], ["sales.customer.read"])
    auth_headers={"X-Tenant-Id":TENANT,"Authorization":"Bearer local-test"}
    assert c.get("/v1/sales/customers",headers=auth_headers).status_code==200
    assert c.get("/v1/sales/reference-data",headers=auth_headers).status_code==200
    denied=c.get("/v1/sales/quotes",headers=auth_headers)
    assert denied.status_code==403 and denied.json()["error"]["code"]=="permission_denied"


def test_quote_update_rejects_past_delivery_promise():
    payload={"promised_delivery_date":(date.today()-timedelta(days=1)).isoformat()}
    response=client().patch("/v1/sales/quotes/quo_1",headers=headers(True),json=payload)
    assert response.status_code==422


def test_fulfillment_rejects_an_inventory_item_other_than_product_mapping(monkeypatch):
    product_line=order().lines[0].model_copy(update={"product_service_type":"product","fulfillment_mode":"pending","fulfillment_status":"pending"})
    product_order=order("confirmed").model_copy(update={"lines":[product_line]})
    monkeypatch.setattr(FakeRepository,"get_order",lambda self,tenant_id,order_id: product_order)
    monkeypatch.setattr(FakeAuthority,"get_product",lambda self,tenant_id,product_id,authorization: schemas.ProductReference(id=product_id,code="PROD-1",name="Producto",type="product",base_unit="HUR",status="active",target_price=100,standard_cost=50,inventory_item_id="itm_authoritative"))
    response=client().post("/v1/sales/orders/sor_1/fulfillment",headers=headers(True),json={"lines":[{"order_line_id":"sol_1","mode":"stock","allocations":[{"inventory_item_id":"itm_other","warehouse_id":"wh_1","quantity":2}]}]})
    assert response.status_code==422
    assert response.json()["error"]["code"]=="product_inventory_mapping_mismatch"


def test_action_reason_rejects_whitespace():
    response=client().post("/v1/sales/orders/sor_1/cancel",headers=headers(True),json={"reason":"   "})
    assert response.status_code==422


def test_order_and_delivery_are_authoritative_lifecycle_endpoints(monkeypatch):
    monkeypatch.setattr(FakeRepository,"get_quote",lambda self,tenant_id,quote_id: quote("approved"))
    c=client()
    created=c.post("/v1/sales/orders",headers=headers(True),json={"code":"PED-001","quote_id":"quo_1"})
    assert created.status_code==201 and created.json()["data"]["status"]=="confirmed"
    draft=c.post("/v1/sales/deliveries",headers=headers(True),json={"code":"ENT-001","order_id":"sor_1","scheduled_date":date.today().isoformat(),"lines":[{"order_line_id":"sol_1","quantity":2,"actual_unit_cost":45}]})
    assert draft.status_code==201 and draft.json()["data"]["status"]=="draft"
    confirmed=c.post("/v1/sales/deliveries/del_1/confirm",headers=headers(True),json={"reason":"Entrega completa"})
    assert confirmed.status_code==200 and confirmed.json()["data"]["status"]=="confirmed"
