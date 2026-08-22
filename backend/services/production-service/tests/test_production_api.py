import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient


SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))
for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        del sys.modules[module_name]

main_module = importlib.import_module("app.main")
repositories_module = importlib.import_module("app.repositories")
schemas_module = importlib.import_module("app.schemas")
authorization_module = importlib.import_module("app.authorization")
api_module = importlib.import_module("app.api")
from erclave_common.config import Settings

app = main_module.app
get_production_repository = repositories_module.get_production_repository
ProductServiceRead = schemas_module.ProductServiceRead
RecipeRead = schemas_module.RecipeRead
RecipeVersionRead = schemas_module.RecipeVersionRead
MachineRead = schemas_module.MachineRead
ProductionOrderRead = schemas_module.ProductionOrderRead
ProductionOrderResourceRead = schemas_module.ProductionOrderResourceRead
ProductionOrderStageRead = schemas_module.ProductionOrderStageRead
ResourceValidationRead = schemas_module.ResourceValidationRead
ORDER_STATUS_TRANSITIONS = schemas_module.ORDER_STATUS_TRANSITIONS


TENANT_ID = "ten_demo"
OTHER_TENANT_ID = "ten_other_tenant"
PRODUCT_SERVICE_ID = "prs_demo"


class FakeProductionRepository:
    def list_product_services(self, tenant_id: str, limit: int = 50, status: str | None = None, q: str | None = None, type_: str | None = None, inventory_mapping: str | None = None):
        if tenant_id != TENANT_ID:
            return []
        return [
            ProductServiceRead(
                id=PRODUCT_SERVICE_ID,
                code="pan-caja",
                name="Pan de caja",
                type="product",
                category="Panificacion",
                base_unit="pza",
                status="active",
                target_price=42.5,
                standard_cost=20.0,
                responsible_area="Produccion",
                inventory_item_id="itm_demo",
            )
        ]

    def get_product_service(self, tenant_id: str, product_service_id: str):
        if tenant_id != TENANT_ID or product_service_id not in (PRODUCT_SERVICE_ID,"prs_unlinked"):
            return None
        return ProductServiceRead(
            id=PRODUCT_SERVICE_ID,
            code="pan-caja",
            name="Pan de caja",
            type="product",
            category="Panificacion",
            base_unit="pza",
            status="active",
            inventory_item_id=None if product_service_id=="prs_unlinked" else "itm_demo",
        )

    def create_product_service(
        self,
        tenant_id: str,
        code: str,
        name: str,
        type_: str,
        category: str | None,
        base_unit: str,
        target_price: float | None,
        responsible_area: str | None,
        cost_center: str | None,
        expected_margin: float | None,
        description: str | None,
        inventory_item_id: str | None,
        idempotency_key: str,
        request_hash: str,
        actor_id: str,
    ):
        if code == "duplicado":
            return None
        return ProductServiceRead(
            id="prs_new",
            code=code.lower(),
            name=name,
            type=type_,
            category=category,
            base_unit=base_unit,
            status="active",
            target_price=target_price,
            responsible_area=responsible_area,
            inventory_item_id=inventory_item_id,
        )

    def update_product_service(
        self,
        tenant_id: str,
        product_service_id: str,
        name: str | None,
        category: str | None,
        base_unit: str | None,
        target_price: float | None,
        responsible_area: str | None,
        cost_center: str | None,
        expected_margin: float | None,
        description: str | None,
        inventory_item_id: str | None,
    ):
        if tenant_id != TENANT_ID or product_service_id != PRODUCT_SERVICE_ID:
            return None
        return ProductServiceRead(
            id=PRODUCT_SERVICE_ID,
            code="pan-caja",
            name=name or "Pan de caja",
            type="product",
            category=category or "Panificacion",
            base_unit=base_unit or "pza",
            status="active",
            target_price=target_price,
            responsible_area=responsible_area,
            inventory_item_id=inventory_item_id,
        )

    def update_product_service_status(self, tenant_id: str, product_service_id: str, status: str, idempotency_key: str, request_hash: str, actor_id: str):
        if tenant_id != TENANT_ID or product_service_id != PRODUCT_SERVICE_ID:
            return None
        return ProductServiceRead(
            id=PRODUCT_SERVICE_ID,
            code="pan-caja",
            name="Pan de caja",
            type="product",
            category="Panificacion",
            base_unit="pza",
            status=status,
        )

    def link_product_inventory_item(self,tenant_id,product_service_id,inventory_item_id):
        item=self.get_product_service(tenant_id,product_service_id)
        return item.model_copy(update={"inventory_item_id":inventory_item_id}) if item else None

    def _version(self, status="draft", complete=True):
        resources = [{"id": "rrs_demo", "resource_type": "material", "resource_ref_id":"itm_demo", "resource_code": "component-a", "resource_name": "Componente A", "quantity": 1, "unit": "PZA", "unit_cost": 2, "total_cost": 2, "sort_order": 1}] if complete else []
        stages = [{"id": "rst_demo", "labor_area_ref_id":"hra_mezclado", "labor_area_name":"Mezclado", "name": "Mezclar", "expected_minutes": 10, "sort_order": 1, "weight_percent": 100, "status": "active"}] if complete else []
        return RecipeVersionRead(id="rcv_demo", recipe_id="rec_demo", version_number=1, status=status, base_quantity=1, base_unit="PZA", standard_cost=2, resources=resources, stages=stages)

    def list_recipes(self, tenant_id: str, limit: int = 50):
        return [self.get_recipe(tenant_id, "rec_demo")] if tenant_id == TENANT_ID else []

    def get_recipe(self, tenant_id: str, recipe_id: str):
        if tenant_id != TENANT_ID or recipe_id != "rec_demo":
            return None
        return RecipeRead(id="rec_demo", product_service_id=PRODUCT_SERVICE_ID, code="rec-pan", name="Receta pan", status="draft", versions=[self._version()])

    def get_recipe_version(self,tenant_id,version_id):return self._version(status="approved") if tenant_id==TENANT_ID and version_id=="rcv_demo" else None
    def normalize_recipe_payload(self,tenant_id,payload,product_service_id=None,recipe_id=None):return payload

    def create_recipe(self, tenant_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str):
        if tenant_id != TENANT_ID or payload.product_service_id != PRODUCT_SERVICE_ID:
            return None
        return RecipeRead(id="rec_demo", product_service_id=payload.product_service_id, code=payload.code.lower(), name=payload.name, status="draft", versions=[self._version(complete=bool(payload.resources and payload.stages))])

    def create_recipe_version(self, tenant_id: str, recipe_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str):
        return self._version(complete=bool(payload.resources and payload.stages)) if tenant_id == TENANT_ID and recipe_id == "rec_demo" else None

    def update_recipe_version(self, tenant_id: str, version_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str):
        return self._version(complete=bool(payload.resources and payload.stages)) if tenant_id == TENANT_ID and version_id == "rcv_demo" else None

    def transition_recipe_version(self, tenant_id: str, version_id: str, action: str, approved_by: str, approval_notes: str | None, effective_from: str | None, idempotency_key: str, request_hash: str):
        if tenant_id != TENANT_ID or version_id != "rcv_demo":
            return None
        statuses = {"submit": "pending_approval", "approve": "approved", "obsolete": "obsolete"}
        return self._version(statuses[action])

    def _machine(self):
        return MachineRead(id="maq_demo",code="recta",name="Recta",machine_type="Costura",area_name="Produccion",available_minutes_per_day=480,cost_per_minute=1.5,status="active")

    def list_machines(self, tenant_id, q=None, status=None): return [self._machine()] if tenant_id == TENANT_ID else []
    def create_machine(self, tenant_id, payload, key, request_hash, actor_id): return self._machine() if tenant_id == TENANT_ID else None
    def update_machine(self, tenant_id, machine_id, payload, key, request_hash, actor_id): return self._machine() if tenant_id == TENANT_ID and machine_id == "maq_demo" else None

    def _validation(self):
        return ResourceValidationRead(recipe_version_id="rcv_demo",quantity=2,unit="pza",can_release=True,planned_cost=4,validated_at=datetime.now(timezone.utc),rows=[],blockers=[])
    def validate_resources(self, tenant_id, payload, observations, key, request_hash, actor_id): return self._validation() if tenant_id == TENANT_ID else None
    def preview_resources(self,tenant_id,payload,observations):return self._validation() if tenant_id==TENANT_ID else None

    def _stage(self, status="pending", progress=0):
        return ProductionOrderStageRead(id="ost_demo",recipe_stage_id="rst_demo",name="Mezclar",sort_order=1,weight_percent=100,status=status,planned_minutes=10,responsible_name="Ana",progress_percent=progress)
    def _order(self, status="released"):
        return ProductionOrderRead(id="ord_demo",code="OP-001",product_service_id=PRODUCT_SERVICE_ID,recipe_id="rec_demo",recipe_version_id="rcv_demo",quantity=2,unit="pza",status=status,priority="medium",responsible_name="Ana",source_type="manual",planned_cost=4,recipe_snapshot={},resource_validation_snapshot={},stages=[self._stage()],created_at=datetime.now(timezone.utc))
    def list_orders(self, tenant_id, limit=50, status=None): return [self._order()] if tenant_id == TENANT_ID else []
    def get_order(self, tenant_id, order_id): return self._order() if tenant_id == TENANT_ID and order_id == "ord_demo" else None
    def preflight_order_status(self,tenant_id,order_id,target_status):return self.get_order(tenant_id,order_id)
    def create_order(self, tenant_id, payload, observations, order_id, reservation_refs, key, request_hash, actor_id): return self._order().model_copy(update={"code": payload.code or "OP-001"}) if tenant_id == TENANT_ID else None
    def update_order_status(self, tenant_id, order_id, payload, key, request_hash, actor_id, material_actuals=None): return self._order(payload.status) if tenant_id == TENANT_ID and order_id == "ord_demo" else None
    def update_order_resource_actual(self,tenant_id,order_id,resource_id,payload,key,request_hash,actor_id):
        return ProductionOrderResourceRead(id=resource_id,resource_type="labor",resource_ref_id="role_demo",resource_code="role_demo",resource_name="Operador",unit="MIN",planned_quantity=60,actual_quantity=payload.actual_quantity,unit_cost=2,planned_cost=120,actual_cost=payload.actual_quantity*2) if tenant_id==TENANT_ID and order_id=="ord_demo" else None
    def update_order_stage(self, tenant_id, stage_id, payload, key, request_hash, actor_id): return self._stage(payload.status,payload.progress_percent) if tenant_id == TENANT_ID and stage_id == "ost_demo" else None


def client_with_fake_repo() -> TestClient:
    app.dependency_overrides[get_production_repository] = lambda: FakeProductionRepository()
    app.dependency_overrides[authorization_module.get_settings] = lambda: Settings(auth_mode="demo")
    app.dependency_overrides[api_module.get_hr_worker_client] = lambda: FakeHrWorkerClient()
    app.dependency_overrides[api_module.get_unit_catalog_client] = lambda: FakeUnitCatalogClient()
    app.dependency_overrides[api_module.get_resource_authority_client] = lambda: FakeResourceAuthorityClient()
    return TestClient(app)

class FakeHrWorkerClient:
    def eligible(self,tenant_id,authorization):
        return [{"id":"hrw_demo","full_name":"Ana Ruiz"}] if tenant_id==TENANT_ID else []

class FakeUnitCatalogClient:
    def require_active(self,tenant_id,code,authorization=None): return code.upper()

class FakeResourceAuthorityClient:
    def validate_product_inventory_mapping(self,tenant_id,inventory_item_id,base_unit,authorization):return {"id":inventory_item_id,"status":"active","type":"finishedGood","base_unit":base_unit}
    def create_finished_good_item(self,tenant_id,payload,authorization,idempotency_key):return {"id":"itm_new","status":"active",**payload}
    def normalize_recipe(self,tenant_id,payload,authorization):return payload
    def normalize_machine(self,tenant_id,payload,authorization):return payload.model_copy(update={"area_name":"Produccion"})
    def observations(self,tenant_id,version,payload,authorization,idempotency_key):return []
    def reserve(self,tenant_id,order_id,row,authorization,idempotency_key):return []
    def reservation_action(self,tenant_id,reservation_id,action,authorization,idempotency_key,reason):return {"quantity":1,"unit_cost":2}


def teardown_function():
    app.dependency_overrides.clear()


class FakeAdminSessionClient:
    def __init__(self, context: dict):
        self.context = context

    def get_context(self, tenant_id: str, authorization: str) -> dict:
        return self.context


def firebase_client(permissions: list[str], active_modules: list[str] | None = None, tenant_status: str = "active") -> TestClient:
    context = {
        "tenant": {"id": TENANT_ID, "status": tenant_status},
        "user": {"id": "usr_authenticated"},
        "permissions": permissions,
        "active_modules": active_modules if active_modules is not None else ["production"],
    }
    app.dependency_overrides[get_production_repository] = lambda: FakeProductionRepository()
    app.dependency_overrides[authorization_module.get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[authorization_module.get_admin_session_client] = lambda: FakeAdminSessionClient(context)
    app.dependency_overrides[api_module.get_unit_catalog_client] = lambda: FakeUnitCatalogClient()
    return TestClient(app)


def test_firebase_mode_requires_bearer_token():
    response = firebase_client(["production.product_service.read"]).get(
        "/v1/production/product-services", headers={"X-Tenant-Id": TENANT_ID}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_required"


def test_firebase_mode_denies_missing_permission():
    response = firebase_client([]).get(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Authorization": "Bearer test-token"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_firebase_mode_denies_inactive_module():
    response = firebase_client(["production.product_service.read"], active_modules=[]).get(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Authorization": "Bearer test-token"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "module_not_enabled"


def test_firebase_mode_allows_exact_permission():
    response = firebase_client(["production.product_service.read"]).get(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200


def test_machine_commands_use_contract_and_tenant():
    response=client_with_fake_repo().post("/v1/production/machines",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"machine-create-test"},json={"code":"equipment-a","name":"Equipo A","machine_type":"Proceso","area_ref_id":"hra_mezclado","area_name":"ignorado","available_minutes_per_day":480,"cost_per_minute":1.5})
    assert response.status_code==201 and response.json()["data"]["id"]=="maq_demo"


def test_resource_validation_returns_backend_decision():
    response=client_with_fake_repo().post("/v1/production/resource-validations",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"resource-validation-test"},json={"recipe_version_id":"rcv_demo","quantity":2,"unit":"PZA"})
    assert response.status_code==200 and response.json()["data"]["can_release"] is True


def test_resource_validation_rejects_client_observed_availability():
    response=client_with_fake_repo().post("/v1/production/resource-validations",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"resource-validation-observed"},json={"recipe_version_id":"rcv_demo","quantity":2,"unit":"PZA","observed_resources":[]})
    assert response.status_code==422


def test_order_create_and_state_commands_are_exposed():
    client=client_with_fake_repo(); headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"order-create-test"}
    created=client.post("/v1/production/orders",headers=headers,json={"recipe_version_id":"rcv_demo","quantity":2,"unit":"pza","responsible_worker_id":"hrw_demo","stage_assignments":[{"recipe_stage_id":"rst_demo","responsible_worker_id":"hrw_demo"}]})
    assert created.status_code==201 and created.json()["data"]["status"]=="released"
    changed=client.patch("/v1/production/orders/ord_demo/status",headers={**headers,"Idempotency-Key":"order-status-test"},json={"status":"in_progress","reason":"Inicio autorizado"})
    assert changed.status_code==200 and changed.json()["data"]["status"]=="in_progress"


def test_first_start_consumes_material_reservations_with_stable_key():
    material=ProductionOrderResourceRead(id="por_material",resource_type="material",resource_ref_id="itm_demo",resource_code="MAT-1",resource_name="Material",unit="PZA",planned_quantity=2,unit_cost=3,planned_cost=6,reservation_ref_id="res_demo",reservation_ref_ids=["res_demo"])

    class MaterialOrderRepository(FakeProductionRepository):
        received_actuals=None
        def _order(self,status="released"):
            return super()._order(status).model_copy(update={"resources":[material]})
        def update_order_status(self,tenant_id,order_id,payload,key,request_hash,actor_id,material_actuals=None):
            self.received_actuals=material_actuals
            return self._order(payload.status)

    class ReservationSpy(FakeResourceAuthorityClient):
        def __init__(self):self.actions=[]
        def reservation_action(self,tenant_id,reservation_id,action,authorization,idempotency_key,reason):
            self.actions.append((reservation_id,action,idempotency_key))
            return {"quantity":2,"unit_cost":3}

    repository=MaterialOrderRepository();spy=ReservationSpy();client=client_with_fake_repo()
    app.dependency_overrides[get_production_repository]=lambda:repository
    app.dependency_overrides[api_module.get_resource_authority_client]=lambda:spy
    response=client.patch("/v1/production/orders/ord_demo/status",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"start-materials-test"},json={"status":"in_progress","reason":"Inicio autorizado"})
    assert response.status_code==200
    assert spy.actions==[("res_demo","consume","production-order-ord_demo-material-start")]
    assert repository.received_actuals=={"res_demo":{"quantity":2.0,"cost":6.0}}


def test_resume_completion_and_post_start_cancellation_do_not_issue_materials_again():
    material=ProductionOrderResourceRead(id="por_material",resource_type="material",resource_ref_id="itm_demo",resource_code="MAT-1",resource_name="Material",unit="PZA",planned_quantity=2,actual_quantity=2,unit_cost=3,planned_cost=6,actual_cost=6,reservation_ref_id="res_demo",reservation_ref_ids=["res_demo"])

    class ExistingIssueRepository(FakeProductionRepository):
        def __init__(self,status,target):self.status=status;self.target=target
        def _order(self,status=None):
            return super()._order(status or self.status).model_copy(update={"resources":[material],"stages":[self._stage("completed")]})
        def preflight_order_status(self,tenant_id,order_id,target_status):return self._order()
        def update_order_status(self,tenant_id,order_id,payload,key,request_hash,actor_id,material_actuals=None):return self._order(payload.status)

    class ReservationSpy(FakeResourceAuthorityClient):
        def __init__(self):self.actions=[]
        def reservation_action(self,*args,**kwargs):self.actions.append((args,kwargs));return {"quantity":2,"unit_cost":3}

    for source,target in (("paused","in_progress"),("in_validation","completed"),("in_progress","cancelled")):
        spy=ReservationSpy();client=client_with_fake_repo()
        app.dependency_overrides[get_production_repository]=lambda source=source,target=target:ExistingIssueRepository(source,target)
        app.dependency_overrides[api_module.get_resource_authority_client]=lambda spy=spy:spy
        response=client.patch("/v1/production/orders/ord_demo/status",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":f"no-double-{source}-{target}"},json={"status":target,"reason":"Continuidad operativa"})
        assert response.status_code==200
        assert spy.actions==[]


def test_waiting_resources_order_can_start_but_cannot_skip_to_validation():
    assert "in_progress" in ORDER_STATUS_TRANSITIONS["waiting_resources"]
    assert "in_validation" not in ORDER_STATUS_TRANSITIONS["waiting_resources"]


def test_direct_validation_rejects_incomplete_stages():
    class IncompleteStageRepository(FakeProductionRepository):
        def preflight_order_status(self,tenant_id,order_id,target_status):
            assert target_status=="in_validation"
            raise ValueError("production_stages_incomplete")

    client=client_with_fake_repo()
    app.dependency_overrides[get_production_repository]=lambda:IncompleteStageRepository()
    response=client.patch("/v1/production/orders/ord_demo/status",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"validation-incomplete-test"},json={"status":"in_validation","reason":"Revision operativa"})
    assert response.status_code==409
    assert response.json()["error"]["code"]=="production_stages_incomplete"


def test_failed_status_preflight_does_not_call_inventory_reservations():
    class RejectingPreflightRepository(FakeProductionRepository):
        def preflight_order_status(self,tenant_id,order_id,target_status):
            raise ValueError("production_stages_incomplete")

    class ReservationSpy(FakeResourceAuthorityClient):
        def __init__(self):self.actions=[]
        def reservation_action(self,*args,**kwargs):
            self.actions.append((args,kwargs))
            return super().reservation_action(*args,**kwargs)

    spy=ReservationSpy()
    client=client_with_fake_repo()
    app.dependency_overrides[get_production_repository]=lambda:RejectingPreflightRepository()
    app.dependency_overrides[api_module.get_resource_authority_client]=lambda:spy
    response=client.patch("/v1/production/orders/ord_demo/status",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"failed-preflight-test"},json={"status":"completed","reason":"Intento de cierre"})
    assert response.status_code==409
    assert response.json()["error"]["code"]=="production_stages_incomplete"
    assert spy.actions==[]

def test_order_rejects_unknown_or_ineligible_worker():
    response=client_with_fake_repo().post("/v1/production/orders",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"order-worker-reject"},json={"recipe_version_id":"rcv_demo","quantity":2,"unit":"pza","responsible_worker_id":"hrw_unknown","stage_assignments":[{"recipe_stage_id":"rst_demo","responsible_worker_id":"hrw_demo"}]})
    assert response.status_code==422 and response.json()["error"]["code"]=="responsible_worker_not_eligible"


def test_order_stage_command_is_exposed():
    response=client_with_fake_repo().patch("/v1/production/order-stages/ost_demo",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"stage-update-test"},json={"status":"in_progress","progress_percent":65})
    assert response.status_code==200 and response.json()["data"]["status"]=="in_progress"
    assert response.json()["data"]["progress_percent"]==65


def test_order_stage_progress_and_status_must_agree():
    client=client_with_fake_repo()
    invalid=client.patch("/v1/production/order-stages/ost_demo",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"stage-invalid-progress"},json={"status":"completed","progress_percent":99})
    assert invalid.status_code==422
    completed=client.patch("/v1/production/order-stages/ost_demo",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"stage-complete-progress"},json={"status":"completed","progress_percent":100})
    assert completed.status_code==200 and completed.json()["data"]["progress_percent"]==100


def test_actual_resource_usage_is_valued_by_backend():
    response=client_with_fake_repo().patch("/v1/production/orders/ord_demo/resources/por_demo",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"resource-actual-test"},json={"actual_quantity":55})
    assert response.status_code==200
    assert response.json()["data"]["actual_cost"]==110


def test_new_production_routes_require_exact_permission_in_firebase_mode():
    response=firebase_client([]).get("/v1/production/orders",headers={"X-Tenant-Id":TENANT_ID,"Authorization":"Bearer test-token"})
    assert response.status_code==403 and response.json()["error"]["details"]["permission"]=="production.order.read"


def test_list_product_services_requires_tenant_header():
    client = client_with_fake_repo()

    response = client.get("/v1/production/product-services")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "tenant_required"


def test_list_product_services_returns_catalog():
    client = client_with_fake_repo()

    response = client.get("/v1/production/product-services", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "pan-caja"


def test_list_product_services_does_not_leak_other_tenant_data():
    client = client_with_fake_repo()

    response = client.get("/v1/production/product-services", headers={"X-Tenant-Id": OTHER_TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_create_product_service_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID},
            json={"code": "galleta", "name": "Galleta", "type": "product", "base_unit": "pza", "inventory_item_id": "itm_demo"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_create_product_service_returns_created_item():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-product-create"},
        json={"code": "Galleta", "name": "Galleta", "type": "product", "base_unit": "pza", "inventory_item_id": "itm_demo"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["code"] == "galleta"

def test_guided_finished_good_creation_links_by_id():
    response=client_with_fake_repo().put("/v1/production/product-services/prs_unlinked/finished-good-link",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"guided-finished-good"},json={"inventory_item":{"code":"VELA-PT","name":"Vela terminada","type":"finishedGood","base_unit":"pza","inventory_policy":"standard"}})
    assert response.status_code==200
    assert response.json()["data"]["product_service"]["inventory_item_id"]=="itm_new"
    assert response.json()["data"]["inventory_item"]["name"]=="Vela terminada"

def test_guided_finished_good_rejects_unit_mismatch():
    response=client_with_fake_repo().put("/v1/production/product-services/prs_unlinked/finished-good-link",headers={"X-Tenant-Id":TENANT_ID,"Idempotency-Key":"guided-unit-mismatch"},json={"inventory_item":{"code":"VELA-PT","name":"Vela terminada","type":"finishedGood","base_unit":"kg"}})
    assert response.status_code==422
    assert response.json()["error"]["code"]=="product_inventory_unit_mismatch"


def test_product_requires_non_blank_inventory_mapping_and_service_forbids_it():
    client = client_with_fake_repo()
    headers = {"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-product-mapping"}

    missing = client.post(
        "/v1/production/product-services",
        headers=headers,
        json={"code": "producto-sin-articulo", "name": "Producto", "type": "product", "base_unit": "pza", "inventory_item_id": "   "},
    )
    forbidden = client.post(
        "/v1/production/product-services",
        headers=headers,
        json={"code": "servicio-con-articulo", "name": "Servicio", "type": "service", "base_unit": "hur", "inventory_item_id": "itm_demo"},
    )

    assert missing.status_code == 422
    assert forbidden.status_code == 422


def test_get_product_service_returns_item():
    client = client_with_fake_repo()

    response = client.get(f"/v1/production/product-services/{PRODUCT_SERVICE_ID}", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"]["id"] == PRODUCT_SERVICE_ID


def test_get_product_service_from_other_tenant_returns_404():
    client = client_with_fake_repo()

    response = client.get(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}",
        headers={"X-Tenant-Id": OTHER_TENANT_ID},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_service_not_found"


def test_update_product_service_returns_updated_item():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}",
        headers={"X-Tenant-Id": TENANT_ID},
        json={"name": "Pan de caja actualizado", "target_price": 44.0},
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Pan de caja actualizado"


def test_update_product_service_from_other_tenant_returns_404():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}",
        headers={"X-Tenant-Id": OTHER_TENANT_ID},
        json={"name": "No debe cruzar tenant"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_service_not_found"


def test_update_product_service_status_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}/status",
        headers={"X-Tenant-Id": TENANT_ID},
        json={"status": "inactive", "reason": "QA"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_update_product_service_status_returns_updated_status():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}/status",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-product-status"},
        json={"status": "inactive", "reason": "QA"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "inactive"


RECIPE_PAYLOAD = {
    "product_service_id": PRODUCT_SERVICE_ID,
    "code": "REC-PAN",
    "name": "Receta pan",
    "base_quantity": 1,
    "base_unit": "PZA",
    "resources": [{"resource_type": "material", "resource_ref_id":"itm_demo", "resource_code": "component-a", "resource_name": "Componente A", "quantity": 1, "unit": "PZA", "unit_cost": 2}],
    "stages": [{"labor_area_ref_id": "hra_mezclado", "labor_area_name": "Mezclado", "name": "Mezclado", "expected_minutes": 10, "sort_order": 1, "weight_percent": 100}],
}


def test_create_recipe_requires_idempotency_key():
    response = client_with_fake_repo().post("/v1/production/recipes", headers={"X-Tenant-Id": TENANT_ID}, json=RECIPE_PAYLOAD)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_create_recipe_returns_initial_draft_version():
    response = client_with_fake_repo().post("/v1/production/recipes", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-create-01"}, json=RECIPE_PAYLOAD)
    assert response.status_code == 201
    assert response.json()["data"]["versions"][0]["status"] == "draft"
    assert response.json()["data"]["versions"][0]["standard_cost"] == 2
    assert response.json()["data"]["versions"][0]["stages"][0]["weight_percent"] == 100


def test_recipe_machine_without_hr_area_returns_actionable_422():
    class InvalidMachineRepository(FakeProductionRepository):
        def normalize_recipe_payload(self,tenant_id,payload,product_service_id=None,recipe_id=None):
            raise ValueError("machine_resource_invalid")

    client = client_with_fake_repo()
    app.dependency_overrides[get_production_repository] = lambda: InvalidMachineRepository()
    response = client.post(
        "/v1/production/recipes",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-machine-without-area"},
        json=RECIPE_PAYLOAD,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "machine_resource_invalid"
    assert "Human Resources area" in response.json()["error"]["message"]


def test_recipe_rejects_stage_weights_that_do_not_total_100():
    payload = {**RECIPE_PAYLOAD, "stages": [{**RECIPE_PAYLOAD["stages"][0], "weight_percent": 90}]}
    response = client_with_fake_repo().post("/v1/production/recipes", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-invalid-weight"}, json=payload)
    assert response.status_code == 422


def test_recipe_rejects_non_contiguous_phase_numbers():
    payload = {**RECIPE_PAYLOAD, "stages": [{**RECIPE_PAYLOAD["stages"][0], "sort_order": 2}]}
    response = client_with_fake_repo().post("/v1/production/recipes", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-invalid-phase"}, json=payload)
    assert response.status_code == 422


def test_recipe_read_does_not_leak_other_tenant_data():
    response = client_with_fake_repo().get("/v1/production/recipes/rec_demo", headers={"X-Tenant-Id": OTHER_TENANT_ID})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "recipe_not_found"


def test_submit_recipe_version_requires_idempotency_key():
    response = client_with_fake_repo().post("/v1/production/recipe-versions/rcv_demo/submit", headers={"X-Tenant-Id": TENANT_ID})
    assert response.status_code == 400


def test_recipe_version_can_be_submitted_and_approved():
    client = client_with_fake_repo()
    submitted = client.post("/v1/production/recipe-versions/rcv_demo/submit", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-submit-01"})
    approved = client.post("/v1/production/recipe-versions/rcv_demo/approve", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-approve-01"}, json={})
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "pending_approval"
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "approved"
