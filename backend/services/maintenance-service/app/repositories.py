import json
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import Depends
from sqlalchemy import create_engine,text
from sqlalchemy.exc import IntegrityError
from erclave_common.config import Settings,get_settings

class MaintenanceRepository:
    def __init__(self,database_url):
        if not database_url:raise RuntimeError("Maintenance database URL is required.")
        self.engine=create_engine(database_url,pool_pre_ping=True)
    def _claim(self,c,t,o,k,h):
        row=c.execute(text("select request_hash,response_payload from maintenance.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k for update"),{"t":t,"o":o,"k":k}).mappings().first()
        if row:
            if row["request_hash"]!=h:raise ValueError("idempotency_key_reused")
            if row["response_payload"] is None:raise ValueError("command_in_progress")
            return row["response_payload"]
        c.execute(text("insert into maintenance.idempotency_records(id,tenant_id,operation,idempotency_key,request_hash) values(:id,:t,:o,:k,:h)"),{"id":f"mid_{uuid4().hex[:26]}","t":t,"o":o,"k":k,"h":h});return None
    def _finish(self,c,t,o,k,v):c.execute(text("update maintenance.idempotency_records set response_payload=cast(:p as jsonb) where tenant_id=:t and operation=:o and idempotency_key=:k"),{"p":json.dumps(v,default=str),"t":t,"o":o,"k":k})
    def _audit(self,c,t,a,action,kind,eid,payload):c.execute(text("insert into maintenance.audit_events(id,tenant_id,actor_id,action,entity_type,entity_id,payload) values(:id,:t,:a,:ac,:kind,:eid,cast(:p as jsonb))"),{"id":f"mae_{uuid4().hex[:26]}","t":t,"a":a,"ac":action,"kind":kind,"eid":eid,"p":json.dumps(payload,default=str)})
    def _order(self,c,t,i):
        row=c.execute(text("""select id,code,status,target_type,production_machine_ref_id production_machine_id,machine_code_snapshot,machine_name_snapshot,source_type,source_production_order_ref_id source_production_order_id,source_production_order_code_snapshot,priority,title,description,location,safety_notes,diagnosis,root_cause,work_performed,verification_notes,assigned_worker_ref_id assigned_worker_id,assigned_worker_name_snapshot assigned_worker_name,integration_status,integration_operation,integration_error,integration_attempts,last_integration_at,requested_at,started_at,resolved_at,closed_at,cancelled_at,created_at,updated_at from maintenance.orders where tenant_id=:t and id=:i"""),{"t":t,"i":i}).mappings().first()
        if not row:return None
        value=dict(row)
        value["time_entries"]=[dict(x) for x in c.execute(text("select id,worker_ref_id worker_id,worker_name_snapshot worker_name,started_at,ended_at,minutes,notes,created_at from maintenance.time_entries where tenant_id=:t and order_id=:i order by started_at"),{"t":t,"i":i}).mappings()]
        reqs=[]
        for request_row in c.execute(text("select id,warehouse_ref_id warehouse_id,warehouse_name_snapshot warehouse_name,status,pending_operation,integration_error,integration_attempts,last_integration_at,created_at,updated_at from maintenance.material_requests where tenant_id=:t and order_id=:i order by created_at"),{"t":t,"i":i}).mappings():
            req=dict(request_row);req["lines"]=[dict(x) for x in c.execute(text("select id,line_number,inventory_item_ref_id item_id,item_code_snapshot item_code,item_name_snapshot item_name,quantity,unit_code,reservation_ref_id reservation_id,inventory_movement_ref_id inventory_movement_id,unit_cost_snapshot,line_status from maintenance.material_request_lines where tenant_id=:t and material_request_id=:r order by line_number"),{"t":t,"r":req["id"]}).mappings()];reqs.append(req)
        value["material_requests"]=reqs
        value["total_minutes"]=sum(x["minutes"] for x in value["time_entries"])
        return value
    def list_orders(self,t,q=None,status=None,limit=100):
        where=["tenant_id=:t"];params={"t":t,"limit":limit}
        if status:where.append("status=:status");params["status"]=status
        if q:where.append("(code ilike :q or title ilike :q or location ilike :q or coalesce(machine_name_snapshot,'') ilike :q)");params["q"]=f"%{q}%"
        with self.engine.connect() as c:
            ids=c.execute(text(f"select id from maintenance.orders where {' and '.join(where)} order by created_at desc limit :limit"),params).scalars().all();return [self._order(c,t,i) for i in ids]
    def get_order(self,t,i):
        with self.engine.connect() as c:return self._order(c,t,i)
    def create_order(self,t,p,snapshots,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"order.create",k,h)
            if replay:return replay
            i=f"mwo_{uuid4().hex[:26]}";d=p.model_dump();d.update(snapshots)
            try:c.execute(text("""insert into maintenance.orders(id,tenant_id,code,target_type,production_machine_ref_id,machine_code_snapshot,machine_name_snapshot,source_type,source_production_order_ref_id,source_production_order_code_snapshot,priority,title,description,location,safety_notes,created_by_actor_id) values(:id,:t,upper(:code),:target_type,:production_machine_id,:machine_code_snapshot,:machine_name_snapshot,:source_type,:source_production_order_id,:source_production_order_code_snapshot,:priority,:title,:description,:location,:safety_notes,:actor)"""),{"id":i,"t":t,"actor":a,**d})
            except IntegrityError as exc:raise ValueError("maintenance_order_conflict") from exc
            value=self._order(c,t,i);self._audit(c,t,a,"maintenance.order.create","order",i,{"code":p.code,"target_type":p.target_type});self._finish(c,t,"order.create",k,value);return value
    def update_order(self,t,i,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"order.update",k,h)
            if replay:return replay
            before=self._order(c,t,i)
            if not before:return None
            if before["status"] not in {"draft","requested","assigned","in_progress","waiting_parts"}:raise ValueError("maintenance_order_not_editable")
            data=p.model_dump(exclude_unset=True)
            if data:c.execute(text("update maintenance.orders set "+",".join(f"{x}=:{x}" for x in data)+",updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i,**data})
            value=self._order(c,t,i);self._audit(c,t,a,"maintenance.order.update","order",i,{"before":before,"after":value});self._finish(c,t,"order.update",k,value);return value
    def transition(self,t,i,p,worker,k,h,a):
        allowed={"request":{"draft"},"assign":{"requested","assigned"},"start":{"assigned"},"wait_for_parts":{"in_progress"},"resume":{"waiting_parts"},"resolve":{"in_progress","waiting_parts"},"close":{"resolved"},"reopen":{"resolved"},"cancel":{"draft","requested","assigned"}}
        target={"request":"requested","assign":"assigned","start":"in_progress","wait_for_parts":"waiting_parts","resume":"in_progress","resolve":"resolved","close":"closed","reopen":"in_progress","cancel":"cancelled"}[p.transition]
        with self.engine.begin() as c:
            replay=self._claim(c,t,"order.transition",k,h)
            if replay:return replay
            before=self._order(c,t,i)
            if not before:return None
            if before["status"] not in allowed[p.transition]:raise ValueError("invalid_maintenance_transition")
            if before["integration_status"] in {"processing","needs_reconciliation"} and p.transition in {"assign","start","close"}:raise ValueError("maintenance_integration_pending")
            if p.transition=="resolve":
                if not all(before.get(x) and str(before[x]).strip() for x in ("diagnosis","work_performed","verification_notes")):raise ValueError("maintenance_resolution_evidence_required")
                if before["total_minutes"]<=0:raise ValueError("maintenance_time_required")
                if any(req["status"] not in {"issued","cancelled"} for req in before["material_requests"]):raise ValueError("maintenance_materials_not_reconciled")
            values={"t":t,"i":i,"status":target,"error":None}
            assignments=""
            if p.transition=="assign":
                values.update({"worker_id":worker["id"],"worker_name":worker["full_name"]});assignments=",assigned_worker_ref_id=:worker_id,assigned_worker_name_snapshot=:worker_name"
            timestamp={"request":"requested_at","start":"started_at","resolve":"resolved_at","close":"closed_at","cancel":"cancelled_at"}.get(p.transition)
            timestamp_sql=f",{timestamp}=now()" if timestamp else ""
            integration=""
            if before["production_machine_id"] and p.transition in {"request","resolve","cancel","reopen"}:
                operation="block" if p.transition in {"request","reopen"} else "release"
                integration=",integration_status='processing',integration_operation='"+operation+"',integration_error=null"
            try:c.execute(text(f"update maintenance.orders set status=:status{assignments}{timestamp_sql}{integration},updated_at=now() where tenant_id=:t and id=:i"),values)
            except IntegrityError as exc:raise ValueError("maintenance_order_conflict") from exc
            if p.transition=="assign":
                c.execute(text("update maintenance.assignments set is_primary=false where tenant_id=:t and order_id=:o and is_primary"),{"t":t,"o":i})
                c.execute(text("""insert into maintenance.assignments(id,tenant_id,order_id,worker_ref_id,worker_name_snapshot,is_primary,assigned_by_actor_id)
                    values(:id,:t,:o,:w,:n,true,:a)
                    on conflict(tenant_id,order_id,worker_ref_id) do update set worker_name_snapshot=excluded.worker_name_snapshot,is_primary=true,assigned_by_actor_id=excluded.assigned_by_actor_id,assigned_at=now()"""),{"id":f"mas_{uuid4().hex[:26]}","t":t,"o":i,"w":worker["id"],"n":worker["full_name"],"a":a})
            value=self._order(c,t,i);self._audit(c,t,a,f"maintenance.order.{p.transition}","order",i,{"from":before["status"],"to":target,"reason":p.reason});self._finish(c,t,"order.transition",k,value);return value
    def set_order_integration(self,t,i,status,error=None,actor="system"):
        with self.engine.begin() as c:
            before=self._order(c,t,i)
            c.execute(text("""update maintenance.orders set integration_status=:s,integration_error=:e,
                integration_operation=:operation,
                integration_attempts=integration_attempts+1,last_integration_at=now(),updated_at=now()
                where tenant_id=:t and id=:i"""),{"s":status,"e":error,"operation":None if status=="completed" else before.get("integration_operation"),"t":t,"i":i})
            value=self._order(c,t,i);self._audit(c,t,actor,"maintenance.order.integration","order",i,{"operation":before.get("integration_operation") if before else None,"status":status,"error":error});return value
    def create_time(self,t,i,p,worker,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"time.create",k,h)
            if replay:return replay
            order=self._order(c,t,i)
            if not order:return None
            if order["status"] not in {"assigned","in_progress","waiting_parts"}:raise ValueError("maintenance_time_status_invalid")
            if order["assigned_worker_id"]!=worker["id"]:raise ValueError("maintenance_time_worker_not_assigned")
            overlap=c.execute(text("select 1 from maintenance.time_entries where tenant_id=:t and order_id=:o and worker_ref_id=:w and started_at<:end and ended_at>:start limit 1"),{"t":t,"o":i,"w":worker["id"],"start":p.started_at,"end":p.ended_at}).first()
            if overlap:raise ValueError("maintenance_time_overlap")
            eid=f"mte_{uuid4().hex[:26]}";minutes=max(1,int((p.ended_at-p.started_at).total_seconds()//60))
            c.execute(text("insert into maintenance.time_entries(id,tenant_id,order_id,worker_ref_id,worker_name_snapshot,started_at,ended_at,minutes,notes,created_by_actor_id) values(:id,:t,:o,:w,:n,:start,:end,:m,:notes,:a)"),{"id":eid,"t":t,"o":i,"w":worker["id"],"n":worker["full_name"],"start":p.started_at,"end":p.ended_at,"m":minutes,"notes":p.notes,"a":a})
            value={"id":eid,"worker_id":worker["id"],"worker_name":worker["full_name"],"started_at":p.started_at,"ended_at":p.ended_at,"minutes":minutes,"notes":p.notes};self._audit(c,t,a,"maintenance.time.create","time_entry",eid,{"order_id":i,"minutes":minutes});self._finish(c,t,"time.create",k,value);return value
    def prepare_material_request(self,t,order_id,p,snapshots,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"material_request.create",k,h)
            if replay:return replay,None
            order=self._order(c,t,order_id)
            if not order:return None,None
            if order["status"] not in {"assigned","in_progress","waiting_parts"}:raise ValueError("maintenance_material_status_invalid")
            rid=f"mmr_{uuid4().hex[:26]}";c.execute(text("insert into maintenance.material_requests(id,tenant_id,order_id,warehouse_ref_id,warehouse_name_snapshot,status,pending_operation,requested_by_actor_id) values(:id,:t,:o,:w,:n,'processing','reserve',:a)"),{"id":rid,"t":t,"o":order_id,"w":p.warehouse_id,"n":snapshots["warehouse_name"],"a":a})
            plan=[]
            for number,(line,snapshot) in enumerate(zip(p.lines,snapshots["items"]),1):
                lid=f"mml_{uuid4().hex[:26]}";c.execute(text("insert into maintenance.material_request_lines(id,tenant_id,material_request_id,line_number,inventory_item_ref_id,item_code_snapshot,item_name_snapshot,quantity,unit_code) values(:id,:t,:r,:n,:item,:code,:name,:q,:u)"),{"id":lid,"t":t,"r":rid,"n":number,"item":line.item_id,"code":snapshot["code"],"name":snapshot["name"],"q":line.quantity,"u":line.unit_code});plan.append({"line_id":lid,"item_id":line.item_id,"quantity":line.quantity,"unit_code":line.unit_code})
            self._audit(c,t,a,"maintenance.material_request.create","material_request",rid,{"order_id":order_id,"warehouse_id":p.warehouse_id,"line_count":len(plan)})
            return {"id":rid,"order_id":order_id},plan
    def complete_material_request(self,t,rid,k,reservations,error=None,actor="system"):
        with self.engine.begin() as c:
            lines=c.execute(text("select id from maintenance.material_request_lines where tenant_id=:t and material_request_id=:r order by line_number"),{"t":t,"r":rid}).scalars().all()
            for line_id,reservation in zip(lines,reservations):c.execute(text("update maintenance.material_request_lines set reservation_ref_id=:reservation,line_status='reserved',unit_cost_snapshot=:cost where tenant_id=:t and id=:id"),{"reservation":reservation.get("id"),"cost":reservation.get("unit_cost_snapshot"),"t":t,"id":line_id})
            if error:
                for line_id in lines[len(reservations):]:c.execute(text("update maintenance.material_request_lines set line_status='failed' where tenant_id=:t and id=:id"),{"t":t,"id":line_id})
            status="needs_reconciliation" if error else "reserved";c.execute(text("""update maintenance.material_requests set status=:s,pending_operation=:pending,
                integration_error=:e,integration_attempts=integration_attempts+1,last_integration_at=now(),updated_at=now() where tenant_id=:t and id=:r"""),{"s":status,"pending":"reserve" if error else None,"e":error,"t":t,"r":rid});value=self._material(c,t,rid);self._audit(c,t,actor,"maintenance.material_request.reserve","material_request",rid,{"status":status,"completed_lines":len(reservations),"error":error});self._finish(c,t,"material_request.create",k,value);return value
    def _material(self,c,t,rid):
        row=c.execute(text("select id,order_id,warehouse_ref_id warehouse_id,warehouse_name_snapshot warehouse_name,status,pending_operation,integration_error,integration_attempts,last_integration_at,created_at from maintenance.material_requests where tenant_id=:t and id=:r"),{"t":t,"r":rid}).mappings().first()
        if not row:return None
        value=dict(row);value["lines"]=[dict(x) for x in c.execute(text("select id,line_number,inventory_item_ref_id item_id,item_code_snapshot item_code,item_name_snapshot item_name,quantity,unit_code,reservation_ref_id reservation_id,inventory_movement_ref_id inventory_movement_id,unit_cost_snapshot,line_status from maintenance.material_request_lines where tenant_id=:t and material_request_id=:r order by line_number"),{"t":t,"r":rid}).mappings()];return value
    def get_material_request(self,t,rid):
        with self.engine.connect() as c:return self._material(c,t,rid)
    def material_plan(self,t,order_id):
        with self.engine.connect() as c:return [dict(x) for x in c.execute(text("select l.id line_id,l.reservation_ref_id reservation_id,l.quantity from maintenance.material_request_lines l join maintenance.material_requests r on r.tenant_id=l.tenant_id and r.id=l.material_request_id where l.tenant_id=:t and r.order_id=:o and r.status in ('reserved','needs_reconciliation') and coalesce(r.pending_operation,'issue')='issue' and l.line_status='reserved' order by r.created_at,l.line_number"),{"t":t,"o":order_id}).mappings()]
    def complete_material_issue(self,t,order_id,movements,error=None,actor="system"):
        with self.engine.begin() as c:
            plan=[dict(x) for x in c.execute(text("select l.id line_id,r.id request_id from maintenance.material_request_lines l join maintenance.material_requests r on r.tenant_id=l.tenant_id and r.id=l.material_request_id where l.tenant_id=:t and r.order_id=:o and r.status='reserved' and l.line_status='reserved' order by r.created_at,l.line_number for update"),{"t":t,"o":order_id}).mappings()]
            for item,movement in zip(plan,movements):c.execute(text("update maintenance.material_request_lines set inventory_movement_ref_id=:m,line_status='issued' where tenant_id=:t and id=:i"),{"m":movement.get("id"),"t":t,"i":item["line_id"]})
            request_ids={x["request_id"] for x in plan}
            for rid in request_ids:
                c.execute(text("""update maintenance.material_requests set status=:s,pending_operation=:pending,
                    integration_error=:e,integration_attempts=integration_attempts+1,last_integration_at=now(),updated_at=now() where tenant_id=:t and id=:r"""),{"s":"needs_reconciliation" if error else "issued","pending":"issue" if error else None,"e":error,"t":t,"r":rid})
                self._audit(c,t,actor,"maintenance.material_request.issue","material_request",rid,{"status":"needs_reconciliation" if error else "issued","error":error})
    def prepare_material_reconciliation(self,t,rid,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"material_request.reconcile",k,h)
            if replay:return replay,None
            value=self._material(c,t,rid)
            if not value:return None,None
            if value["status"]!="needs_reconciliation" or value["pending_operation"] not in {"reserve","cancel"}:raise ValueError("material_request_not_reconcilable")
            if value["pending_operation"]=="reserve":
                plan=[{"line_id":x["id"],"item_id":x["item_id"],"quantity":x["quantity"],"unit_code":x["unit_code"]} for x in value["lines"] if x["line_status"] in {"pending","failed"}]
            else:plan=[{"line_id":x["id"],"reservation_id":x["reservation_id"]} for x in value["lines"] if x["reservation_id"] and x["line_status"]=="reserved"]
            c.execute(text("update maintenance.material_requests set status=:s,integration_error=null,updated_at=now() where tenant_id=:t and id=:r"),{"s":"cancelling" if value["pending_operation"]=="cancel" else "processing","t":t,"r":rid})
            return self._material(c,t,rid),plan
    def complete_material_reconciliation(self,t,rid,k,results,error,a):
        with self.engine.begin() as c:
            value=self._material(c,t,rid);operation=value["pending_operation"]
            candidates=[x for x in value["lines"] if (operation=="reserve" and x["line_status"] in {"pending","failed"}) or (operation=="cancel" and x["line_status"]=="reserved")]
            for line,result in zip(candidates,results):
                if operation=="reserve":c.execute(text("update maintenance.material_request_lines set reservation_ref_id=:reservation,line_status='reserved',unit_cost_snapshot=:cost where tenant_id=:t and id=:id"),{"reservation":result.get("id"),"cost":result.get("unit_cost_snapshot"),"t":t,"id":line["id"]})
                else:c.execute(text("update maintenance.material_request_lines set line_status='released' where tenant_id=:t and id=:id"),{"t":t,"id":line["id"]})
            remaining=c.execute(text("select count(*) from maintenance.material_request_lines where tenant_id=:t and material_request_id=:r and reservation_ref_id is not null and line_status='reserved'"),{"t":t,"r":rid}).scalar_one() if operation=="cancel" else None
            done=not error and remaining==0 if operation=="cancel" else not error and c.execute(text("select count(*) from maintenance.material_request_lines where tenant_id=:t and material_request_id=:r and line_status!='reserved'"),{"t":t,"r":rid}).scalar_one()==0
            status=("cancelled" if operation=="cancel" else "reserved") if done else "needs_reconciliation"
            c.execute(text("""update maintenance.material_requests set status=:s,pending_operation=case when :done then null else pending_operation end,
                integration_error=:e,integration_attempts=integration_attempts+1,last_integration_at=now(),updated_at=now() where tenant_id=:t and id=:r"""),{"s":status,"done":done,"e":None if done else error or "maintenance_reconciliation_incomplete","t":t,"r":rid})
            value=self._material(c,t,rid);self._audit(c,t,a,"maintenance.material_request.reconcile","material_request",rid,{"operation":operation,"status":status,"error":error});self._finish(c,t,"material_request.reconcile",k,value);return value
    def prepare_material_cancellation(self,t,rid,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"material_request.cancel",k,h)
            if replay:return replay,None
            value=self._material(c,t,rid)
            if not value:return None,None
            if value["status"] not in {"reserved","needs_reconciliation","cancelling"}:raise ValueError("material_request_not_cancellable")
            if value["status"]=="needs_reconciliation" and value["pending_operation"] not in {"reserve","cancel"}:raise ValueError("material_request_not_cancellable")
            c.execute(text("update maintenance.material_requests set status='cancelling',pending_operation='cancel',integration_error=null,updated_at=now() where tenant_id=:t and id=:r"),{"t":t,"r":rid})
            plan=[{"line_id":x["id"],"reservation_id":x["reservation_id"]} for x in value["lines"] if x["reservation_id"] and x["line_status"]=="reserved"]
            return self._material(c,t,rid),plan
    def complete_material_cancellation(self,t,rid,k,released,error,a):
        with self.engine.begin() as c:
            for line_id in released:c.execute(text("update maintenance.material_request_lines set line_status='released' where tenant_id=:t and id=:id"),{"t":t,"id":line_id})
            remaining=c.execute(text("select count(*) from maintenance.material_request_lines where tenant_id=:t and material_request_id=:r and reservation_ref_id is not null and line_status='reserved'"),{"t":t,"r":rid}).scalar_one();done=not error and remaining==0
            status="cancelled" if done else "needs_reconciliation"
            c.execute(text("""update maintenance.material_requests set status=:s,pending_operation=case when :done then null else 'cancel' end,
                integration_error=:e,integration_attempts=integration_attempts+1,last_integration_at=now(),updated_at=now() where tenant_id=:t and id=:r"""),{"s":status,"done":done,"e":None if done else error or "maintenance_cancellation_incomplete","t":t,"r":rid})
            value=self._material(c,t,rid);self._audit(c,t,a,"maintenance.material_request.cancel","material_request",rid,{"status":status,"error":error});self._finish(c,t,"material_request.cancel",k,value);return value

def get_maintenance_repository(settings:Settings=Depends(get_settings)):return MaintenanceRepository(settings.effective_database_url)
