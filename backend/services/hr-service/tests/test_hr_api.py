import importlib,sys
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
