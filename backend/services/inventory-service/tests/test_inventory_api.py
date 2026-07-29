import importlib, sys
from datetime import datetime, timezone
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=="app" or name.startswith("app."): del sys.modules[name]
main=importlib.import_module("app.main"); repos=importlib.import_module("app.repositories"); schemas=importlib.import_module("app.schemas"); auth=importlib.import_module("app.authorization")
from erclave_common.config import Settings
app=main.app; TENANT="ten_demo"

class FakeRepo:
    def list_warehouses(self,t,q=None): return [] if t!=TENANT else [schemas.WarehouseRead(id="whs_1",code="mp",name="Materias primas",type="raw_materials",status="active",business_center="Matriz",location="Nave 1",owner="Almacenes")]
    def create_warehouse(self,t,p,k,h,a): return schemas.WarehouseRead(id="whs_1",status="active",**p.model_dump()) if t==TENANT else None
    def update_warehouse(self,t,i,p,k,h,a): return None
    def list_items(self,t,q=None): return []
    def create_item(self,t,p,k,h,a): return schemas.ItemRead(id="itm_1",status="active",**p.model_dump())
    def update_item(self,t,i,p,k,h,a):
        if p.suggested_warehouse_id=="whs_other": raise ValueError("suggested_warehouse_invalid")
        return None
    def list_movements(self,t,item=None,warehouse=None): return []
    def create_movement(self,t,p,k,h,a):
        if p.movement_type=="exit": raise ValueError("insufficient_stock")
        return schemas.MovementRead(id="mov_1",movement_code="MOV-1",movement_type=p.movement_type,inventory_item_id=p.inventory_item_id,warehouse_id=p.warehouse_id,direction="in",quantity=p.quantity,unit=p.unit,reason=p.reason,source_type=p.source.type,source_id=p.source.id,status="recorded",occurred_at=p.occurred_at)
    def reverse_movement(self,*args): return None
    def list_balances(self,t,**options):
        data=[schemas.BalanceRead(inventory_item_id="itm_1",item_code="har",item_name="Harina",item_type="rawMaterial",category="Insumos",item_status="active",inventory_policy="standard",warehouse_id="whs_1",warehouse_code="mp",warehouse_name="Materias primas",on_hand_quantity=5,reserved_quantity=0,available_quantity=5,unit="kg",minimum_stock=2,stock_status="normal")] if t==TENANT else []
        return data,schemas.Page(limit=options.get("limit",50),has_more=False)

def client(): app.dependency_overrides[repos.get_inventory_repository]=lambda:FakeRepo(); app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode="demo"); return TestClient(app)
def teardown_function(): app.dependency_overrides.clear()
def headers(command=False,tenant=TENANT): return {"X-Tenant-Id":tenant,"X-Actor-Id":"usr_demo",**({"Idempotency-Key":"test-1"} if command else {})}

def test_health_and_tenant_required():
    c=client(); assert c.get("/health").status_code==200; assert c.get("/v1/inventory/warehouses").status_code==400
def test_list_is_tenant_scoped():
    c=client(); assert len(c.get("/v1/inventory/warehouses",headers=headers()).json()["data"])==1; assert c.get("/v1/inventory/warehouses",headers=headers(tenant="ten_other")).json()["data"]==[]
def test_commands_require_idempotency_key():
    response=client().post("/v1/inventory/warehouses",headers=headers(),json={"code":"MP","name":"Materias primas","type":"raw_materials","business_center":"Matriz","location":"Nave 1","owner":"Almacenes"}); assert response.status_code==400
def test_create_item():
    response=client().post("/v1/inventory/items",headers=headers(True),json={"code":"HAR","name":"Harina","type":"rawMaterial","base_unit":"kg","inventory_policy":"standard"}); assert response.status_code==201; assert response.json()["data"]["code"]=="HAR"
def test_negative_stock_is_rejected():
    response=client().post("/v1/inventory/movements",headers=headers(True),json={"movement_type":"exit","inventory_item_id":"itm_1","warehouse_id":"whs_1","quantity":10,"unit":"kg","reason":"Consumo manual","source":{"type":"manual","id":"DOC-1"},"occurred_at":datetime.now(timezone.utc).isoformat()}); assert response.status_code==409; assert response.json()["error"]["code"]=="insufficient_stock"
def test_balances_are_read_only_calculations():
    response=client().get("/v1/inventory/balances?q=hari&category=Insumos&inventory_policy=standard&unit=kg&sort=item_name&limit=25",headers=headers()); assert response.status_code==200; assert response.json()["data"][0]["on_hand_quantity"]==5; assert response.json()["data"][0]["item_code"]=="har"; assert response.json()["page"]=={"limit":25,"next_cursor":None,"has_more":False}
def test_balance_filters_are_validated():
    response=client().get("/v1/inventory/balances?stock_status=unknown&limit=0",headers=headers()); assert response.status_code==422
def test_patch_item_rejects_warehouse_from_another_tenant():
    response=client().patch("/v1/inventory/items/itm_1",headers=headers(True),json={"suggested_warehouse_id":"whs_other"}); assert response.status_code==409; assert response.json()["error"]["code"]=="suggested_warehouse_invalid"
def test_firebase_mode_requires_bearer_token():
    c=client(); app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode="firebase"); response=c.get("/v1/inventory/warehouses",headers=headers()); assert response.status_code==401; assert response.json()["error"]["code"]=="auth_required"
