import json
from uuid import uuid4
from sqlalchemy import create_engine,text
from erclave_common.config import get_settings
from .schemas import AreaRead,ProductionCapacityRead,RoleRead,SalesEligibleWorkerRead,WorkerRead
class HrRepository:
    def __init__(self,engine):self.engine=engine
    def _claim(self,c,t,o,k,h):
        row=c.execute(text("select request_hash,response_payload from hr.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k for update"),{"t":t,"o":o,"k":k}).mappings().first()
        if row:
            if row["request_hash"]!=h:raise ValueError("idempotency_key_reused")
            return row["response_payload"]
        c.execute(text("insert into hr.idempotency_records(id,tenant_id,operation,idempotency_key,request_hash) values(:id,:t,:o,:k,:h)"),{"id":f"ide_{uuid4().hex[:26]}","t":t,"o":o,"k":k,"h":h});return None
    def _done(self,c,t,o,k,v):c.execute(text("update hr.idempotency_records set response_payload=cast(:p as jsonb) where tenant_id=:t and operation=:o and idempotency_key=:k"),{"p":json.dumps(v.model_dump(mode="json")),"t":t,"o":o,"k":k})
    def _release(self,c,t,o,k):c.execute(text("delete from hr.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k and response_payload is null"),{"t":t,"o":o,"k":k})
    def _audit(self,c,t,a,action,kind,eid,payload):c.execute(text("insert into hr.audit_events(id,tenant_id,actor_id,action,entity_type,entity_id,payload) values(:id,:t,:a,:ac,:kind,:eid,cast(:p as jsonb))"),{"id":f"aud_{uuid4().hex[:26]}","t":t,"a":a,"ac":action,"kind":kind,"eid":eid,"p":json.dumps(payload)})
    def _area(self,c,t,i):
        row=c.execute(text("select id,code,name,description,status from hr.labor_areas where tenant_id=:t and id=:i"),{"t":t,"i":i}).mappings().first();return AreaRead.model_validate(dict(row)) if row else None
    def list_areas(self,t):
        with self.engine.connect() as c:rows=c.execute(text("select id,code,name,description,status from hr.labor_areas where tenant_id=:t order by code"),{"t":t}).mappings()
        return [AreaRead.model_validate(dict(x)) for x in rows]
    def create_area(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"area.create",k,h)
            if replay:return AreaRead.model_validate(replay)
            i=f"hra_{uuid4().hex[:26]}";row=c.execute(text("insert into hr.labor_areas(id,tenant_id,code,name,description) values(:i,:t,upper(:code),:name,:description) on conflict(tenant_id,code) do nothing returning id"),{"i":i,"t":t,**p.model_dump()}).first()
            if not row:self._release(c,t,"area.create",k);return None
            value=self._area(c,t,i);self._audit(c,t,a,"hr.area.create","area",i,p.model_dump());self._done(c,t,"area.create",k,value);return value
    def update_area(self,t,i,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"area.update",k,h)
            if replay:return AreaRead.model_validate(replay)
            before=self._area(c,t,i)
            if not before:self._release(c,t,"area.update",k);return None
            data=p.model_dump(exclude_none=True)
            if data:c.execute(text("update hr.labor_areas set "+",".join(f"{x}=:{x}" for x in data)+",updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i,**data})
            value=self._area(c,t,i);self._audit(c,t,a,"hr.area.update","area",i,{"before":before.model_dump(),"after":value.model_dump()});self._done(c,t,"area.update",k,value);return value
    def _role(self,c,t,i):
        row=c.execute(text("select id,labor_area_id,position,recipe_name,resource_quantity,minutes_per_resource,hourly_cost,intervenes_in_production,status from hr.labor_roles where tenant_id=:t and id=:i"),{"t":t,"i":i}).mappings().first();return RoleRead.model_validate(dict(row)) if row else None
    def list_roles(self,t,area=None,production_only=False):
        where=["tenant_id=:t"];params={"t":t}
        if area:where.append("labor_area_id=:area");params["area"]=area
        if production_only:where.extend(["intervenes_in_production=true","status='active'"])
        with self.engine.connect() as c:rows=c.execute(text("select id,labor_area_id,position,recipe_name,resource_quantity,minutes_per_resource,hourly_cost,intervenes_in_production,status from hr.labor_roles where "+" and ".join(where)+" order by recipe_name"),params).mappings()
        return [RoleRead.model_validate(dict(x)) for x in rows]
    def create_role(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"position.create",k,h)
            if replay:return RoleRead.model_validate(replay)
            area=self._area(c,t,p.labor_area_id)
            if not area or area.status!="active":self._release(c,t,"position.create",k);raise ValueError("labor_area_invalid")
            i=f"hrp_{uuid4().hex[:26]}";row=c.execute(text("insert into hr.labor_roles(id,tenant_id,labor_area_id,position,recipe_name,resource_quantity,minutes_per_resource,hourly_cost,intervenes_in_production) values(:i,:t,:labor_area_id,:position,:recipe_name,:resource_quantity,:minutes_per_resource,:hourly_cost,:intervenes_in_production) on conflict(tenant_id,labor_area_id,position) do nothing returning id"),{"i":i,"t":t,**p.model_dump()}).first()
            if not row:self._release(c,t,"position.create",k);return None
            value=self._role(c,t,i);self._audit(c,t,a,"hr.position.create","position",i,p.model_dump());self._done(c,t,"position.create",k,value);return value
    def update_role(self,t,i,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"position.update",k,h)
            if replay:return RoleRead.model_validate(replay)
            before=self._role(c,t,i)
            if not before:self._release(c,t,"position.update",k);return None
            data=p.model_dump(exclude_none=True)
            if "labor_area_id" in data:
                area=self._area(c,t,data["labor_area_id"])
                if not area or area.status!="active":self._release(c,t,"position.update",k);raise ValueError("labor_area_invalid")
            if data:c.execute(text("update hr.labor_roles set "+",".join(f"{x}=:{x}" for x in data)+",updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i,**data})
            value=self._role(c,t,i);self._audit(c,t,a,"hr.position.update","position",i,{"before":before.model_dump(),"after":value.model_dump()});self._done(c,t,"position.update",k,value);return value
    def _worker(self,c,t,i):
        row=c.execute(text("""select w.*,concat_ws(' ',w.first_names,w.first_last_name,w.second_last_name) full_name,r.position position_name,r.labor_area_id,a.name labor_area_name,r.intervenes_in_production from hr.workers w join hr.labor_roles r on r.tenant_id=w.tenant_id and r.id=w.labor_position_id join hr.labor_areas a on a.tenant_id=r.tenant_id and a.id=r.labor_area_id where w.tenant_id=:t and w.id=:i"""),{"t":t,"i":i}).mappings().first()
        return WorkerRead.model_validate(dict(row)) if row else None
    def list_workers(self,t,position=None,production_only=False,active_only=False):
        where=["w.tenant_id=:t"];params={"t":t}
        if position:where.append("w.labor_position_id=:position");params["position"]=position
        if active_only or production_only:where.extend(["w.status='active'","r.status='active'","a.status='active'"])
        if production_only:where.append("r.intervenes_in_production=true")
        with self.engine.connect() as c:
            ids=c.execute(text("select w.id from hr.workers w join hr.labor_roles r on r.tenant_id=w.tenant_id and r.id=w.labor_position_id join hr.labor_areas a on a.tenant_id=r.tenant_id and a.id=r.labor_area_id where "+" and ".join(where)+" order by w.first_last_name,w.first_names"),params).scalars().all()
            return [self._worker(c,t,i) for i in ids]
    def list_sales_eligible_workers(self,t):
        with self.engine.connect() as c:
            rows=c.execute(text("""select w.id,w.employee_number,concat_ws(' ',w.first_names,w.first_last_name,w.second_last_name) full_name,
                r.position position_name,a.name labor_area_name,w.status
                from hr.workers w join hr.labor_roles r on r.tenant_id=w.tenant_id and r.id=w.labor_position_id
                join hr.labor_areas a on a.tenant_id=r.tenant_id and a.id=r.labor_area_id
                where w.tenant_id=:t and w.status='active' and r.status='active' and a.status='active'
                order by w.first_last_name,w.first_names"""),{"t":t}).mappings().all()
        return [SalesEligibleWorkerRead.model_validate(dict(row)) for row in rows]
    def list_production_capacity(self,t):
        with self.engine.connect() as c:
            rows=c.execute(text("""select r.id position_id,r.position position_name,r.recipe_name,r.labor_area_id,a.name labor_area_name,
                count(w.id)::int active_worker_count,r.minutes_per_resource minutes_per_worker,
                count(w.id)*r.minutes_per_resource available_minutes,r.hourly_cost,r.hourly_cost/60.0 cost_per_minute
                from hr.labor_roles r join hr.labor_areas a on a.tenant_id=r.tenant_id and a.id=r.labor_area_id
                left join hr.workers w on w.tenant_id=r.tenant_id and w.labor_position_id=r.id and w.status='active'
                where r.tenant_id=:t and r.status='active' and a.status='active' and r.intervenes_in_production=true
                group by r.id,r.position,r.recipe_name,r.labor_area_id,a.name,r.minutes_per_resource,r.hourly_cost order by r.recipe_name"""),{"t":t}).mappings().all()
        return [ProductionCapacityRead.model_validate(dict(row)) for row in rows]
    def create_worker(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"worker.create",k,h)
            if replay:return WorkerRead.model_validate(replay)
            position=self._role(c,t,p.labor_position_id)
            if not position or position.status!="active":self._release(c,t,"worker.create",k);raise ValueError("labor_position_invalid")
            i=f"hrw_{uuid4().hex[:26]}";data=p.model_dump(mode="json")
            columns=",".join(data);values=",".join(f":{x}" for x in data)
            row=c.execute(text(f"insert into hr.workers(id,tenant_id,{columns}) values(:i,:t,{values}) on conflict do nothing returning id"),{"i":i,"t":t,**data}).first()
            if not row:self._release(c,t,"worker.create",k);return None
            value=self._worker(c,t,i);self._audit(c,t,a,"hr.worker.create","worker",i,{"employee_number":value.employee_number,"position_id":value.labor_position_id});self._done(c,t,"worker.create",k,value);return value
    def update_worker(self,t,i,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"worker.update",k,h)
            if replay:return WorkerRead.model_validate(replay)
            before=self._worker(c,t,i)
            if not before:self._release(c,t,"worker.update",k);return None
            data=p.model_dump(exclude_none=True)
            if "labor_position_id" in data:
                position=self._role(c,t,data["labor_position_id"])
                if not position or position.status!="active":self._release(c,t,"worker.update",k);raise ValueError("labor_position_invalid")
            if data:c.execute(text("update hr.workers set "+",".join(f"{x}=:{x}" for x in data)+",updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i,**data})
            value=self._worker(c,t,i);self._audit(c,t,a,"hr.worker.update","worker",i,{"before":{"position_id":before.labor_position_id,"status":before.status},"after":{"position_id":value.labor_position_id,"status":value.status}});self._done(c,t,"worker.update",k,value);return value
_repository=None
def get_hr_repository():
    global _repository
    if _repository is None:
        settings=get_settings();url=settings.hr_database_url or settings.database_url
        if not url:raise RuntimeError("ERCLAVE_HR_DATABASE_URL or ERCLAVE_DATABASE_URL is required.")
        _repository=HrRepository(create_engine(url,pool_pre_ping=True))
    return _repository
