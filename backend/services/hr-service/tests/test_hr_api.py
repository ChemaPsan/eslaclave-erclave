import importlib,sys
from datetime import date
from pathlib import Path
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=="app" or name.startswith("app."):del sys.modules[name]
main=importlib.import_module("app.main");repos=importlib.import_module("app.repositories");schemas=importlib.import_module("app.schemas");auth=importlib.import_module("app.authorization")
from erclave_common.config import Settings
app=main.app;TENANT="ten_demo"
class FakeRepo:
    def list_areas(self,t):return [schemas.AreaRead(id="hra_1",code="OPS",name="Operaciones",status="active")] if t==TENANT else []
    def create_area(self,t,p,k,h,a):return schemas.AreaRead(id="hra_1",status="active",**p.model_dump()) if t==TENANT else None
    def update_area(self,t,i,p,k,h,a):return None
    def list_roles(self,t,area=None,production_only=False):return [schemas.RoleRead(id="hrp_1",labor_area_id="hra_1",position="Operador",recipe_name="Operador",resource_quantity=2,minutes_per_resource=480,hourly_cost=120,intervenes_in_production=True,status="active")] if t==TENANT else []
    def create_role(self,t,p,k,h,a):
        if p.labor_area_id!="hra_1":raise ValueError("labor_area_invalid")
        return schemas.RoleRead(id="hrp_1",status="active",**p.model_dump())
    def update_role(self,t,i,p,k,h,a):return None
    def list_workers(self,t,position=None,production_only=False,active_only=False):
        return [schemas.WorkerRead(id="hrw_1",employee_number="EMP-1",first_names="Ana",first_last_name="Garcia",curp="GARC900101HDFRRL09",rfc="GARC900101ABC",nss="12345678903",hire_date=date(2026,1,1),labor_position_id="hrp_1",status="active",full_name="Ana Garcia",position_name="Operador",labor_area_id="hra_1",labor_area_name="Operaciones",intervenes_in_production=True)] if t==TENANT else []
    def create_worker(self,t,p,k,h,a):return self.list_workers(t)[0] if p.labor_position_id=="hrp_1" else (_ for _ in ()).throw(ValueError("labor_position_invalid"))
    def update_worker(self,t,i,p,k,h,a):return self.list_workers(t)[0] if i=="hrw_1" else None
def client():app.dependency_overrides[repos.get_hr_repository]=lambda:FakeRepo();app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode="demo");return TestClient(app)
def teardown_function():app.dependency_overrides.clear()
def headers(command=False,tenant=TENANT):return {"X-Tenant-Id":tenant,"X-Actor-Id":"usr_demo",**({"Idempotency-Key":"hr-test-1"} if command else {})}
def test_tenant_isolation():assert client().get("/v1/hr/areas",headers=headers(tenant="ten_other")).json()["data"]==[]
def test_create_area_requires_idempotency():assert client().post("/v1/hr/areas",headers=headers(),json={"code":"OPS","name":"Operaciones"}).status_code==400
def test_create_area():assert client().post("/v1/hr/areas",headers=headers(True),json={"code":"OPS","name":"Operaciones"}).status_code==201
def test_position_requires_existing_area():
    response=client().post("/v1/hr/positions",headers=headers(True),json={"labor_area_id":"hra_other","position":"Operador","recipe_name":"Operador"});assert response.status_code==409;assert response.json()["error"]["code"]=="labor_area_invalid"
def test_production_projection_filters_server_side():
    response=client().get("/v1/hr/positions?production_only=true",headers=headers());assert response.status_code==200;assert response.json()["data"][0]["intervenes_in_production"] is True
def test_create_worker_validates_identity_and_position():
    payload={"employee_number":"EMP-1","first_names":"Ana","first_last_name":"Garcia","curp":"GARC900101HDFRRL09","rfc":"GARC900101ABC","nss":"12345678903","hire_date":"2026-01-01","labor_position_id":"hrp_1"}
    response=client().post("/v1/hr/workers",headers=headers(True),json=payload);assert response.status_code==201;assert response.json()["data"]["labor_position_id"]=="hrp_1"
def test_worker_rejects_invalid_nss_check_digit():
    payload={"employee_number":"EMP-1","first_names":"Ana","first_last_name":"Garcia","curp":"GARC900101HDFRRL09","rfc":"GARC900101ABC","nss":"12345678900","hire_date":"2026-01-01","labor_position_id":"hrp_1"}
    assert client().post("/v1/hr/workers",headers=headers(True),json=payload).status_code==422
def test_worker_short_nss_returns_actionable_error_without_echoing_sensitive_input():
    payload={"employee_number":"EMP-1","first_names":"Ana","first_last_name":"Garcia","curp":"GARC900101HDFRRL09","rfc":"GARC900101ABC","nss":"146543123","hire_date":"2026-01-01","labor_position_id":"hrp_1"}
    response=client().post("/v1/hr/workers",headers=headers(True),json=payload);body=response.json()
    assert response.status_code==422
    assert body["error"]["code"]=="invalid_nss"
    assert body["error"]["message"]=="El NSS debe contener exactamente 11 digitos."
    assert body["error"]["details"]["issues"]==[{"field":"nss","code":"invalid_nss"}]
    assert "146543123" not in response.text
    assert payload["curp"] not in response.text and payload["rfc"] not in response.text
def test_worker_invalid_position_is_actionable_and_safe():
    payload={"employee_number":"EMP-1","first_names":"Ana","first_last_name":"Garcia","curp":"GARC900101HDFRRL09","rfc":"GARC900101ABC","nss":"12345678903","hire_date":"2026-01-01","labor_position_id":"hrp_missing"}
    response=client().post("/v1/hr/workers",headers=headers(True),json=payload)
    assert response.status_code==409
    assert response.json()["error"]["code"]=="labor_position_invalid"
    assert response.json()["error"]["message"]=="Selecciona un puesto activo de Recursos Humanos."
def test_workers_are_tenant_scoped():assert client().get("/v1/hr/workers",headers=headers(tenant="ten_other")).json()["data"]==[]
def test_firebase_requires_token():
    c=client();app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode="firebase");assert c.get("/v1/hr/areas",headers=headers()).status_code==401
def test_firebase_denies_missing_permission():
    class SessionClient:
        def get_context(self,tenant_id,authorization):
            return {"tenant":{"id":tenant_id,"status":"active"},"user":{"id":"usr_demo"},"active_modules":["hr"],"permissions":[]}
    c=client()
    app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode="firebase")
    app.dependency_overrides[auth.get_admin_session_client]=lambda:SessionClient()
    response=c.get("/v1/hr/areas",headers={**headers(),"Authorization":"Bearer test"})
    assert response.status_code==403
    assert response.json()["error"]["code"]=="permission_denied"
