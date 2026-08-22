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
    def list_items(self,t,q=None,use_in_recipe=None,status=None):
        if t!=TENANT: return []
        item=schemas.ItemRead(id="itm_1",code="har",name="Harina",type="rawMaterial",base_unit="KGM",inventory_policy="standard",use_in_recipe=True,status="active")
        return [item] if use_in_recipe in (None,True) and status in (None,"active") else []
    def create_item(self,t,p,k,h,a): return schemas.ItemRead(id="itm_1",status="active",default_unit_cost_per_base_unit=p.default_unit_cost,**p.model_dump())
    def get_item(self,t,i):
        return schemas.ItemRead(id="itm_1",code="har",name="Harina",type="rawMaterial",base_unit="KGM",inventory_policy="standard",use_in_recipe=True,status="active") if t==TENANT and i=="itm_1" else None
    def update_item(self,t,i,p,k,h,a):
        if p.suggested_warehouse_id=="whs_other": raise ValueError("suggested_warehouse_invalid")
        return None
    def list_movements(self,t,item=None,warehouse=None): return []
    def create_movement(self,t,p,k,h,a):
        if p.movement_type=="exit": raise ValueError("insufficient_stock")
        return schemas.MovementRead(id="mov_1",movement_code="MOV-1",movement_type=p.movement_type,inventory_item_id=p.inventory_item_id,warehouse_id=p.warehouse_id,direction="in",quantity=p.quantity,unit=p.unit,reason=p.reason,source_type=p.source.type,source_id=p.source.id,status="recorded",occurred_at=p.occurred_at)
    def list_finished_goods_receipts(self,t): return [schemas.FinishedGoodsReceiptSummaryRead(production_order_id="ord_1",received_quantity=2)] if t==TENANT else []
    def create_finished_goods_receipt(self,t,p,order,product,k,h,a):
        movement=schemas.MovementRead(id="mov_fg",movement_code="MOV-FG",movement_type="entry",inventory_item_id="itm_fg",warehouse_id=p.warehouse_id,direction="in",quantity=p.quantity,unit="H87",unit_cost=20,reason="Recepcion",source_type="production_order_receipt",source_id=order["id"],status="recorded",occurred_at=p.received_at)
        return schemas.FinishedGoodsReceiptRead(production_order_id=order["id"],production_order_code=order["code"],product_service_id=product["id"],product_service_code=product["code"],product_service_name=product["name"],inventory_item_id="itm_fg",inventory_item_code="pt",inventory_item_name="Producto terminado",warehouse_id=p.warehouse_id,unit="H87",ordered_quantity=10,received_quantity=p.quantity,cumulative_received_quantity=p.quantity,remaining_quantity=10-p.quantity,movement=movement)
    def reverse_movement(self,*args): return None
    def list_balances(self,t,**options):
        data=[schemas.BalanceRead(inventory_item_id="itm_1",item_code="har",item_name="Harina",item_type="rawMaterial",category="Insumos",item_status="active",inventory_policy="standard",warehouse_id="whs_1",warehouse_code="mp",warehouse_name="Materias primas",on_hand_quantity=5,reserved_quantity=0,available_quantity=5,unit="kg",minimum_stock=2,stock_status="normal")] if t==TENANT else []
        return data,schemas.Page(limit=options.get("limit",50),has_more=False)
    def check_availability(self,t,p):
        item=p.items[0];allocation=schemas.AvailabilityAllocation(warehouse_id="whs_1",warehouse_name="Materias primas",quantity=item.quantity,unit_cost=12)
        row=schemas.AvailabilityItemRead(inventory_item_id=item.inventory_item_id,item_code="har",item_name="Harina",unit=item.unit,required_quantity=item.quantity,on_hand_quantity=5,reserved_quantity=1,available_quantity=4,unit_cost=12,total_cost=item.quantity*12,ok=True,allocations=[allocation])
        return schemas.AvailabilityCheckRead(source=p.source,available=True,items=[row])
    def create_reservation(self,t,p,k,h,a):return schemas.ReservationRead(id="rsv_1",inventory_item_id=p.inventory_item_id,warehouse_id=p.warehouse_id,quantity=p.quantity,unit=p.unit,unit_cost_snapshot=12,source_type=p.source.type,source_id=p.source.id,source_line_id=p.source.line_id,status="active",created_at=datetime.now(timezone.utc))
    def release_reservation(self,t,i,reason,k,h,a):return schemas.ReservationRead(id=i,inventory_item_id="itm_1",warehouse_id="whs_1",quantity=2,unit="kg",unit_cost_snapshot=12,source_type="production_order",source_id="ord_1",source_line_id="line_1",status="released",created_at=datetime.now(timezone.utc))
    def consume_reservation(self,t,i,reason,k,h,a,quantity=None):return schemas.MovementRead(id="mov_consume",movement_code="MOV-C",movement_type="exit",inventory_item_id="itm_1",warehouse_id="whs_1",direction="out",quantity=quantity or 2,unit="kg",unit_cost=12,reason=reason,source_type="reservation",source_id=i,status="recorded",occurred_at=datetime.now(timezone.utc))

class FakeUnitCatalogClient:
    def require_active(self,tenant_id,code,authorization=None): return code.upper()
    def resolve_active(self,tenant_id,code,authorization=None):
        categories={"KGM":"mass","GRM":"mass","H87":"count","LTR":"volume"}
        normalized=code.upper(); return {"code":normalized,"category":categories.get(normalized,"custom"),"status":"active"}
class FakeProductionOrderClient:
    status="completed"
    def get_order(self,tenant_id,order_id,authorization=None): return {"id":order_id,"code":"OP-1","product_service_id":"prs_1","quantity":10,"unit":"H87","status":self.status,"actual_cost":200,"planned_cost":180}
    def get_product(self,tenant_id,product_id,authorization=None): return {"id":product_id,"code":"VELA","name":"Vela","type":"product","status":"active","base_unit":"H87","inventory_item_id":"itm_fg"}
def client(): app.dependency_overrides[repos.get_inventory_repository]=lambda:FakeRepo(); app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode="demo"); app.dependency_overrides[auth.get_unit_catalog_client]=lambda:FakeUnitCatalogClient(); app.dependency_overrides[auth.get_production_order_client]=lambda:FakeProductionOrderClient(); return TestClient(app)
def teardown_function(): app.dependency_overrides.clear()
def headers(command=False,tenant=TENANT): return {"X-Tenant-Id":tenant,"X-Actor-Id":"usr_demo",**({"Idempotency-Key":"test-1"} if command else {})}

def test_reservation_consumption_keeps_positive_quantity_snapshot_when_fully_consumed():
    assert repos.reservation_consumption_state(3.5,3.5)==(3.5,"consumed",0.0)
    assert repos.reservation_consumption_state(3.5,1.25)==(2.25,"active",2.25)

def test_health_and_tenant_required():
    c=client(); assert c.get("/health").status_code==200; assert c.get("/v1/inventory/warehouses").status_code==400
def test_list_is_tenant_scoped():
    c=client(); assert len(c.get("/v1/inventory/warehouses",headers=headers()).json()["data"])==1; assert c.get("/v1/inventory/warehouses",headers=headers(tenant="ten_other")).json()["data"]==[]
def test_commands_require_idempotency_key():
    response=client().post("/v1/inventory/warehouses",headers=headers(),json={"code":"MP","name":"Materias primas","type":"raw_materials","business_center":"Matriz","location":"Nave 1","owner":"Almacenes"}); assert response.status_code==400
def test_create_item():
    response=client().post("/v1/inventory/items",headers=headers(True),json={"code":"HAR","name":"Harina","type":"rawMaterial","base_unit":"kg","inventory_policy":"standard","default_unit_cost":18.5,"use_in_recipe":True}); assert response.status_code==201; assert response.json()["data"]["code"]=="HAR"; assert response.json()["data"]["use_in_recipe"] is True; assert response.json()["data"]["default_unit_cost_per_base_unit"]==18.5
def test_converts_quantity_and_cost_to_item_base_unit():
    response=client().post("/v1/inventory/items/itm_1/unit-conversion",headers=headers(),json={"source_unit":"GRM","quantity":1000,"source_unit_cost":0.02})
    assert response.status_code==200
    assert response.json()["data"]=={"inventory_item_id":"itm_1","source_unit":"GRM","base_unit":"KGM","conversion_factor":0.001,"source_quantity":1000.0,"base_quantity":1.0,"source_unit_cost":0.02,"unit_cost_per_base_unit":20.0}
def test_rejects_incompatible_or_item_specific_conversion():
    response=client().post("/v1/inventory/items/itm_1/unit-conversion",headers=headers(),json={"source_unit":"LTR","quantity":1})
    assert response.status_code==422; assert response.json()["error"]["code"]=="unit_conversion_unsupported"
def test_recipe_item_filter_is_tenant_scoped():
    response=client().get("/v1/inventory/items?use_in_recipe=true&status=active",headers=headers()); assert response.status_code==200; assert response.json()["data"][0]["use_in_recipe"] is True
    assert client().get("/v1/inventory/items?use_in_recipe=true",headers=headers(tenant="ten_other")).json()["data"]==[]
def test_negative_stock_is_rejected():
    response=client().post("/v1/inventory/movements",headers=headers(True),json={"movement_type":"exit","inventory_item_id":"itm_1","warehouse_id":"whs_1","quantity":10,"unit":"kg","reason":"Consumo manual","source":{"type":"manual","id":"DOC-1"},"occurred_at":datetime.now(timezone.utc).isoformat()}); assert response.status_code==409; assert response.json()["error"]["code"]=="insufficient_stock"
def test_lists_and_creates_finished_goods_receipts():
    c=client();listed=c.get("/v1/inventory/finished-goods-receipts",headers=headers());assert listed.status_code==200 and listed.json()["data"][0]["production_order_id"]=="ord_1"
    created=c.post("/v1/inventory/finished-goods-receipts",headers={**headers(True),"Idempotency-Key":"fg-1"},json={"production_order_id":"ord_1","warehouse_id":"whs_1","quantity":4,"received_at":datetime.now(timezone.utc).isoformat(),"notes":"Recepcion fisica"})
    assert created.status_code==201;assert created.json()["data"]["remaining_quantity"]==6;assert created.json()["data"]["movement"]["source_type"]=="production_order_receipt"
def test_finished_goods_receipt_rejects_order_not_completed():
    c=client();fake=FakeProductionOrderClient();fake.status="in_validation";app.dependency_overrides[auth.get_production_order_client]=lambda:fake
    response=c.post("/v1/inventory/finished-goods-receipts",headers={**headers(True),"Idempotency-Key":"fg-2"},json={"production_order_id":"ord_1","warehouse_id":"whs_1","quantity":1,"received_at":datetime.now(timezone.utc).isoformat()})
    assert response.status_code==409;assert response.json()["error"]["code"]=="production_order_not_completed"
def test_balances_are_read_only_calculations():
    response=client().get("/v1/inventory/balances?q=hari&category=Insumos&inventory_policy=standard&unit=kg&sort=item_name&limit=25",headers=headers()); assert response.status_code==200; assert response.json()["data"][0]["on_hand_quantity"]==5; assert response.json()["data"][0]["item_code"]=="har"; assert response.json()["page"]=={"limit":25,"next_cursor":None,"has_more":False}
def test_balance_filters_are_validated():
    response=client().get("/v1/inventory/balances?stock_status=unknown&limit=0",headers=headers()); assert response.status_code==422
def test_patch_item_rejects_warehouse_from_another_tenant():
    response=client().patch("/v1/inventory/items/itm_1",headers=headers(True),json={"suggested_warehouse_id":"whs_other"}); assert response.status_code==409; assert response.json()["error"]["code"]=="suggested_warehouse_invalid"
def test_production_availability_reservation_and_consumption_contracts():
    c=client();command=headers(True)
    availability=c.post("/v1/inventory/availability-checks",headers=command,json={"source":{"type":"production_validation","id":"rcv_1"},"items":[{"inventory_item_id":"itm_1","quantity":2,"unit":"kg"}]})
    assert availability.status_code==200 and availability.json()["data"]["items"][0]["reserved_quantity"]==1
    reservation=c.post("/v1/inventory/reservation-requests",headers={**command,"Idempotency-Key":"reserve-test"},json={"inventory_item_id":"itm_1","warehouse_id":"whs_1","quantity":2,"unit":"kg","source":{"type":"production_order","id":"ord_1","line_id":"line_1"}})
    assert reservation.status_code==201 and reservation.json()["data"]["unit_cost_snapshot"]==12
    consumed=c.post("/v1/inventory/reservations/rsv_1/consume",headers={**command,"Idempotency-Key":"consume-test"},json={"reason":"Cierre de orden"})
    assert consumed.status_code==201 and consumed.json()["data"]["unit_cost"]==12
def test_firebase_mode_requires_bearer_token():
    c=client(); app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode="firebase"); response=c.get("/v1/inventory/warehouses",headers=headers()); assert response.status_code==401; assert response.json()["error"]["code"]=="auth_required"
