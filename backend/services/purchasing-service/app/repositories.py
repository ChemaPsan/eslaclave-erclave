import json
from decimal import Decimal
from uuid import uuid4
from fastapi import Depends
from sqlalchemy import create_engine,text
from sqlalchemy.exc import IntegrityError
from erclave_common.config import Settings,get_settings

class PurchasingRepository:
    def __init__(self,database_url):
        if not database_url: raise RuntimeError("Purchasing database URL is required.")
        self.engine=create_engine(database_url,pool_pre_ping=True)
    def _claim(self,c,tenant,operation,key,digest):
        row=c.execute(text("select request_hash,response_payload from purchasing.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k for update"),{"t":tenant,"o":operation,"k":key}).mappings().first()
        if row:
            if row["request_hash"]!=digest: raise ValueError("idempotency_key_reused")
            if row["response_payload"] is None: raise ValueError("command_in_progress")
            return row["response_payload"]
        c.execute(text("insert into purchasing.idempotency_records(id,tenant_id,operation,idempotency_key,request_hash) values(:id,:t,:o,:k,:h)"),{"id":f"pid_{uuid4().hex[:26]}","t":tenant,"o":operation,"k":key,"h":digest}); return None
    def _finish(self,c,tenant,operation,key,value): c.execute(text("update purchasing.idempotency_records set response_payload=cast(:p as jsonb) where tenant_id=:t and operation=:o and idempotency_key=:k"),{"p":json.dumps(value,default=str),"t":tenant,"o":operation,"k":key})
    def _audit(self,c,tenant,actor,action,kind,entity,payload): c.execute(text("insert into purchasing.audit_events(id,tenant_id,actor_id,action,entity_type,entity_id,payload) values(:id,:t,:a,:x,:y,:e,cast(:p as jsonb))"),{"id":f"pae_{uuid4().hex[:26]}","t":tenant,"a":actor,"x":action,"y":kind,"e":entity,"p":json.dumps(payload,default=str)})
    def _supplier(self,c,t,id):
        row=c.execute(text("select id,code,commercial_name,legal_name,tax_id,tax_regime,billing_email,contact_name,email,phone,website,fiscal_street,fiscal_exterior_number,fiscal_interior_number,fiscal_neighborhood,fiscal_municipality,fiscal_state,fiscal_postal_code,fiscal_country,currency,payment_terms,lead_time_days,status,created_at,updated_at from purchasing.suppliers where tenant_id=:t and id=:id"),{"t":t,"id":id}).mappings().first(); return dict(row) if row else None
    def list_suppliers(self,t):
        with self.engine.connect() as c:return [dict(x) for x in c.execute(text("select id,code,commercial_name,legal_name,tax_id,tax_regime,billing_email,contact_name,email,phone,website,fiscal_street,fiscal_exterior_number,fiscal_interior_number,fiscal_neighborhood,fiscal_municipality,fiscal_state,fiscal_postal_code,fiscal_country,currency,payment_terms,lead_time_days,status,created_at,updated_at from purchasing.suppliers where tenant_id=:t order by commercial_name"),{"t":t}).mappings()]
    def get_supplier(self,t,id):
        with self.engine.connect() as c:return self._supplier(c,t,id)
    def create_supplier(self,t,p,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"supplier.create",key,digest)
            if replay:return replay
            id=f"sup_{uuid4().hex[:26]}"; d=p.model_dump()
            try:c.execute(text("insert into purchasing.suppliers(id,tenant_id,code,commercial_name,legal_name,tax_id,tax_regime,billing_email,contact_name,email,phone,website,fiscal_street,fiscal_exterior_number,fiscal_interior_number,fiscal_neighborhood,fiscal_municipality,fiscal_state,fiscal_postal_code,fiscal_country,currency,payment_terms,lead_time_days,status) values(:id,:t,:code,:commercial_name,:legal_name,:tax_id,:tax_regime,:billing_email,:contact_name,:email,:phone,:website,:fiscal_street,:fiscal_exterior_number,:fiscal_interior_number,:fiscal_neighborhood,:fiscal_municipality,:fiscal_state,:fiscal_postal_code,:fiscal_country,:currency,:payment_terms,:lead_time_days,:status)"),{"id":id,"t":t,**d})
            except IntegrityError as exc: raise ValueError("supplier_identity_conflict") from exc
            value=self._supplier(c,t,id); self._audit(c,t,actor,"supplier.create","supplier",id,{"code":p.code}); self._finish(c,t,"supplier.create",key,value); return value
    def update_supplier(self,t,id,p,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"supplier.update",key,digest)
            if replay:return replay
            before=self._supplier(c,t,id)
            if not before:return None
            d=p.model_dump(exclude_unset=True)
            if d:
                try:c.execute(text(f"update purchasing.suppliers set {','.join(f'{k}=:{k}' for k in d)},updated_at=now() where tenant_id=:t and id=:id"),{"t":t,"id":id,**d})
                except IntegrityError as exc:raise ValueError("supplier_identity_conflict") from exc
            value=self._supplier(c,t,id); self._audit(c,t,actor,"supplier.update","supplier",id,{"fields":list(d)}); self._finish(c,t,"supplier.update",key,value); return value
    def _lines(self,c,t,table,parent_col,parent,lock=False): return [dict(x) for x in c.execute(text(f"select * from purchasing.{table} where tenant_id=:t and {parent_col}=:id order by line_number"+(" for update" if lock else "")),{"t":t,"id":parent}).mappings()]
    def _req(self,c,t,id,lock=False):
        row=c.execute(text("select id,code,status,required_date,priority,source_type,source_id,requested_by_actor_id,approved_by_actor_id,rejection_reason,submitted_at,approved_at,cancellation_reason,cancelled_by_actor_id,cancelled_at,created_at,updated_at from purchasing.requisitions where tenant_id=:t and id=:id"+(" for update" if lock else "")),{"t":t,"id":id}).mappings().first()
        if not row:return None
        return {**dict(row),"lines":self._lines(c,t,"requisition_lines","requisition_id",id,lock)}
    def list_requisitions(self,t):
        with self.engine.connect() as c:
            ids=c.execute(text("select id from purchasing.requisitions where tenant_id=:t order by created_at desc"),{"t":t}).scalars(); return [self._req(c,t,id) for id in ids]
    def get_requisition(self,t,id):
        with self.engine.connect() as c:return self._req(c,t,id)
    def _write_req_lines(self,c,t,id,lines,snapshots=None):
        for n,line in enumerate(lines,1):
            d=line.model_dump(); item=(snapshots or {}).get(line.inventory_item_id,{})
            c.execute(text("insert into purchasing.requisition_lines(id,tenant_id,requisition_id,line_number,line_type,inventory_item_ref_id,item_code_snapshot,item_name_snapshot,description,quantity,unit_code) values(:id,:t,:parent,:n,:line_type,:inventory_item_id,:item_code,:item_name,:description,:quantity,:unit_code)"),{"id":f"prl_{uuid4().hex[:26]}","t":t,"parent":id,"n":n,"item_code":item.get("code"),"item_name":item.get("name"),**d})
    def create_requisition(self,t,p,key,digest,actor,snapshots=None):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"requisition.create",key,digest)
            if replay:return replay
            id=f"pre_{uuid4().hex[:26]}"; d=p.model_dump(exclude={"lines"})
            try:c.execute(text("insert into purchasing.requisitions(id,tenant_id,code,required_date,priority,source_type,source_id,requested_by_actor_id) values(:id,:t,:code,:required_date,:priority,:source_type,:source_id,:actor)"),{"id":id,"t":t,"actor":actor,**d})
            except IntegrityError as exc: raise ValueError("requisition_code_conflict") from exc
            self._write_req_lines(c,t,id,p.lines,snapshots); value=self._req(c,t,id); self._audit(c,t,actor,"requisition.create","requisition",id,{"code":p.code,"line_count":len(p.lines)}); self._finish(c,t,"requisition.create",key,value); return value
    def update_requisition(self,t,id,p,key,digest,actor,snapshots=None):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"requisition.update",key,digest)
            if replay:return replay
            current=self._req(c,t,id,True)
            if not current:return None
            if current["status"]!="draft":raise ValueError("requisition_not_editable")
            d=p.model_dump(exclude={"lines"}); c.execute(text("update purchasing.requisitions set code=:code,required_date=:required_date,priority=:priority,source_type=:source_type,source_id=:source_id,updated_at=now() where tenant_id=:t and id=:id"),{"t":t,"id":id,**d}); c.execute(text("delete from purchasing.requisition_lines where tenant_id=:t and requisition_id=:id"),{"t":t,"id":id}); self._write_req_lines(c,t,id,p.lines,snapshots)
            value=self._req(c,t,id); self._audit(c,t,actor,"requisition.update","requisition",id,{}); self._finish(c,t,"requisition.update",key,value); return value
    def transition_requisition(self,t,id,target,reason,key,digest,actor):
        allowed={"draft":{"submitted"},"submitted":{"approved","rejected"}}
        with self.engine.begin() as c:
            replay=self._claim(c,t,f"requisition.{target}",key,digest)
            if replay:return replay
            value=self._req(c,t,id,True)
            if not value:return None
            if target not in allowed.get(value["status"],set()):raise ValueError("invalid_requisition_transition")
            extras="submitted_at=now()" if target=="submitted" else "approved_at=now(),approved_by_actor_id=:actor" if target=="approved" else "rejection_reason=:reason"
            c.execute(text(f"update purchasing.requisitions set status=:target,{extras},updated_at=now() where tenant_id=:t and id=:id"),{"target":target,"t":t,"id":id,"actor":actor,"reason":reason}); value=self._req(c,t,id); self._audit(c,t,actor,f"requisition.{target}","requisition",id,{"reason":reason}); self._finish(c,t,f"requisition.{target}",key,value); return value
    def cancel_requisition(self,t,id,reason,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"requisition.cancel",key,digest)
            if replay:return replay
            value=self._req(c,t,id,True)
            if not value:return None
            if value["status"] not in {"draft","submitted","approved"}:raise ValueError("requisition_not_cancellable")
            c.execute(text("update purchasing.requisitions set status='cancelled',cancellation_reason=:reason,cancelled_by_actor_id=:actor,cancelled_at=now(),updated_at=now() where tenant_id=:t and id=:id"),{"reason":reason,"actor":actor,"t":t,"id":id})
            value=self._req(c,t,id);self._audit(c,t,actor,"requisition.cancel","requisition",id,{"reason":reason});self._finish(c,t,"requisition.cancel",key,value);return value
    def _order(self,c,t,id,lock=False):
        row=c.execute(text("select id,code,requisition_id,supplier_id,supplier_code_snapshot,supplier_name_snapshot,status,currency,payment_terms,direct_purchase_reason,subtotal,buyer_actor_id,issued_at,cancellation_reason,cancelled_by_actor_id,cancelled_at,created_at,updated_at from purchasing.purchase_orders where tenant_id=:t and id=:id"+(" for update" if lock else "")),{"t":t,"id":id}).mappings().first()
        if not row:return None
        return {**dict(row),"lines":self._lines(c,t,"purchase_order_lines","purchase_order_id",id,lock)}
    def list_orders(self,t):
        with self.engine.connect() as c:return [self._order(c,t,id) for id in c.execute(text("select id from purchasing.purchase_orders where tenant_id=:t order by created_at desc"),{"t":t}).scalars()]
    def get_order(self,t,id):
        with self.engine.connect() as c:return self._order(c,t,id)
    def _assert_order_matches_requisition(self,req,p):
        if len(req["lines"])!=len(p.lines):raise ValueError("order_requisition_lines_mismatch")
        for source,target in zip(req["lines"],p.lines):
            if source["line_type"]!=target.line_type or source["inventory_item_ref_id"]!=target.inventory_item_id or Decimal(source["quantity"])!=target.quantity or source["unit_code"].upper()!=target.unit_code.upper() or source["description"]!=target.description:
                raise ValueError("order_requisition_lines_mismatch")
    def _write_order_lines(self,c,t,id,lines,snapshots=None):
        for n,line in enumerate(lines,1):
            d=line.model_dump();item=(snapshots or {}).get(line.inventory_item_id,{})
            c.execute(text("insert into purchasing.purchase_order_lines(id,tenant_id,purchase_order_id,line_number,line_type,inventory_item_ref_id,item_code_snapshot,item_name_snapshot,description,quantity,unit_code,unit_price,line_total) values(:id,:t,:parent,:n,:line_type,:inventory_item_id,:item_code,:item_name,:description,:quantity,:unit_code,:unit_price,:total)"),{"id":f"pol_{uuid4().hex[:26]}","t":t,"parent":id,"n":n,"item_code":item.get("code"),"item_name":item.get("name"),"total":line.quantity*(line.unit_price or 0),**d})
    def create_order(self,t,p,key,digest,actor,snapshots=None):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"order.create",key,digest)
            if replay:return replay
            supplier=self._supplier(c,t,p.supplier_id)
            if not supplier or supplier["status"]!="active":raise ValueError("active_supplier_required")
            if p.requisition_id:
                req=self._req(c,t,p.requisition_id,True)
                if not req or req["status"]!="approved":raise ValueError("approved_requisition_required")
                self._assert_order_matches_requisition(req,p)
            id=f"por_{uuid4().hex[:26]}"; subtotal=sum((x.quantity*(x.unit_price or Decimal("0")) for x in p.lines),Decimal("0"))
            try:c.execute(text("insert into purchasing.purchase_orders(id,tenant_id,code,requisition_id,supplier_id,supplier_code_snapshot,supplier_name_snapshot,currency,payment_terms,direct_purchase_reason,subtotal,buyer_actor_id) values(:id,:t,:code,:req,:supplier,:supplier_code,:supplier_name,:currency,:terms,:reason,:subtotal,:actor)"),{"id":id,"t":t,"code":p.code,"req":p.requisition_id,"supplier":p.supplier_id,"supplier_code":supplier["code"],"supplier_name":supplier["commercial_name"],"currency":p.currency,"terms":p.payment_terms,"reason":p.direct_purchase_reason,"subtotal":subtotal,"actor":actor})
            except IntegrityError as exc:raise ValueError("order_code_conflict") from exc
            self._write_order_lines(c,t,id,p.lines,snapshots)
            if p.requisition_id:c.execute(text("update purchasing.requisitions set status='converted',updated_at=now() where tenant_id=:t and id=:id"),{"t":t,"id":p.requisition_id})
            value=self._order(c,t,id); self._audit(c,t,actor,"order.create","purchase_order",id,{"code":p.code}); self._finish(c,t,"order.create",key,value); return value
    def update_order(self,t,id,p,key,digest,actor,snapshots=None):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"order.update",key,digest)
            if replay:return replay
            current=self._order(c,t,id,True)
            if not current:return None
            if current["status"]!="draft":raise ValueError("order_not_editable")
            if current["requisition_id"]!=p.requisition_id:raise ValueError("order_origin_locked")
            supplier=self._supplier(c,t,p.supplier_id)
            if not supplier or supplier["status"]!="active":raise ValueError("active_supplier_required")
            if p.requisition_id:
                req=self._req(c,t,p.requisition_id,True);self._assert_order_matches_requisition(req,p)
            subtotal=sum((line.quantity*(line.unit_price or Decimal("0")) for line in p.lines),Decimal("0"))
            try:c.execute(text("update purchasing.purchase_orders set code=:code,supplier_id=:supplier,supplier_code_snapshot=:supplier_code,supplier_name_snapshot=:supplier_name,currency=:currency,payment_terms=:terms,direct_purchase_reason=:reason,subtotal=:subtotal,updated_at=now() where tenant_id=:t and id=:id"),{"code":p.code,"supplier":p.supplier_id,"supplier_code":supplier["code"],"supplier_name":supplier["commercial_name"],"currency":p.currency,"terms":p.payment_terms,"reason":p.direct_purchase_reason,"subtotal":subtotal,"t":t,"id":id})
            except IntegrityError as exc:raise ValueError("order_code_conflict") from exc
            c.execute(text("delete from purchasing.purchase_order_lines where tenant_id=:t and purchase_order_id=:id"),{"t":t,"id":id});self._write_order_lines(c,t,id,p.lines,snapshots)
            value=self._order(c,t,id);self._audit(c,t,actor,"order.update","purchase_order",id,{"line_count":len(p.lines)});self._finish(c,t,"order.update",key,value);return value
    def issue_order(self,t,id,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"order.issue",key,digest)
            if replay:return replay
            value=self._order(c,t,id,True)
            if not value:return None
            if value["status"]!="draft":raise ValueError("order_not_issuable")
            supplier=self._supplier(c,t,value["supplier_id"])
            if not supplier or supplier["status"]!="active":raise ValueError("active_supplier_required")
            c.execute(text("update purchasing.purchase_orders set status='issued',issued_at=now(),updated_at=now() where tenant_id=:t and id=:id"),{"t":t,"id":id}); value=self._order(c,t,id); self._audit(c,t,actor,"order.issue","purchase_order",id,{}); self._finish(c,t,"order.issue",key,value); return value
    def cancel_order(self,t,id,reason,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"order.cancel",key,digest)
            if replay:return replay
            value=self._order(c,t,id,True)
            if not value:return None
            if value["status"] not in {"draft","issued","partially_received"}:raise ValueError("order_not_cancellable")
            pending=c.execute(text("select 1 from purchasing.purchase_receipt_lines rl join purchasing.purchase_receipts r on r.tenant_id=rl.tenant_id and r.id=rl.receipt_id where rl.tenant_id=:t and r.purchase_order_id=:id and rl.reconciliation_status!='completed' limit 1"),{"t":t,"id":id}).first()
            if pending:raise ValueError("receipt_reconciliation_pending")
            received=sum(Decimal(line["received_quantity"]) for line in value["lines"])
            c.execute(text("update purchasing.purchase_orders set status='cancelled',cancellation_reason=:reason,cancelled_by_actor_id=:actor,cancelled_at=now(),updated_at=now() where tenant_id=:t and id=:id"),{"reason":reason,"actor":actor,"t":t,"id":id})
            if value["requisition_id"] and received==0:c.execute(text("update purchasing.requisitions set status='approved',updated_at=now() where tenant_id=:t and id=:req and status='converted'"),{"t":t,"req":value["requisition_id"]})
            value=self._order(c,t,id);self._audit(c,t,actor,"order.cancel","purchase_order",id,{"reason":reason,"received_quantity":str(received)});self._finish(c,t,"order.cancel",key,value);return value
    def _receipt(self,c,t,id,lock=False):
        row=c.execute(text("select id,code,purchase_order_id,status,supplier_document_reference,received_at,receiver_actor_id,reconciliation_error,reconciliation_attempts,last_reconciliation_at,reconciled_by_actor_id,created_at from purchasing.purchase_receipts where tenant_id=:t and id=:id"+(" for update" if lock else "")),{"t":t,"id":id}).mappings().first()
        if not row:return None
        lines=[dict(x) for x in c.execute(text("select id,line_number,order_line_id,quantity,warehouse_ref_id,inventory_movement_ref_id,inventory_idempotency_key,reconciliation_status from purchasing.purchase_receipt_lines where tenant_id=:t and receipt_id=:id order by line_number"+(" for update" if lock else "")),{"t":t,"id":id}).mappings()]
        return {**dict(row),"lines":lines}
    def list_receipts(self,t):
        with self.engine.connect() as c:
            ids=c.execute(text("select id from purchasing.purchase_receipts where tenant_id=:t order by received_at desc"),{"t":t}).scalars();return [self._receipt(c,t,id) for id in ids]
    def prepare_receipt(self,t,p,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"receipt.create",key,digest)
            if replay:return replay,None
            order=self._order(c,t,p.purchase_order_id,True)
            if not order:return None,None
            if order["status"] not in {"issued","partially_received"}:raise ValueError("order_not_receivable")
            by_id={x["id"]:x for x in order["lines"]}; seen=set(); plan=[]
            for item in p.lines:
                if item.order_line_id in seen:raise ValueError("duplicate_receipt_line")
                seen.add(item.order_line_id); line=by_id.get(item.order_line_id)
                if not line:raise ValueError("order_line_not_found")
                pending=Decimal(c.execute(text("select coalesce(sum(rl.quantity),0) from purchasing.purchase_receipt_lines rl join purchasing.purchase_receipts r on r.tenant_id=rl.tenant_id and r.id=rl.receipt_id where rl.tenant_id=:t and rl.order_line_id=:line and rl.reconciliation_status!='completed' and r.status in ('processing','needs_reconciliation')"),{"t":t,"line":line["id"]}).scalar_one())
                if item.quantity > Decimal(line["quantity"])-Decimal(line["received_quantity"])-pending:raise ValueError("over_receipt")
                if line["line_type"]=="inventory_item" and not item.warehouse_id:raise ValueError("inventory_warehouse_required")
                if line["line_type"]=="service" and item.warehouse_id:raise ValueError("service_warehouse_not_allowed")
                plan.append({"order_line_id":line["id"],"inventory_item_id":line["inventory_item_ref_id"],"line_type":line["line_type"],"quantity":item.quantity,"warehouse_id":item.warehouse_id,"unit_code":line["unit_code"],"unit_price":line["unit_price"],"received_at":p.received_at.isoformat()})
            rid=f"rcp_{uuid4().hex[:26]}"; c.execute(text("insert into purchasing.purchase_receipts(id,tenant_id,code,purchase_order_id,supplier_document_reference,received_at,receiver_actor_id) values(:id,:t,:code,:order,:doc,:at,:actor)"),{"id":rid,"t":t,"code":p.code,"order":p.purchase_order_id,"doc":p.supplier_document_reference,"at":p.received_at,"actor":actor})
            for n,item in enumerate(plan,1):
                item["receipt_line_id"]=f"rcl_{uuid4().hex[:26]}";item["inventory_idempotency_key"]=f"purchase-receipt-{item['receipt_line_id']}"
                c.execute(text("insert into purchasing.purchase_receipt_lines(id,tenant_id,receipt_id,line_number,order_line_id,quantity,warehouse_ref_id,inventory_idempotency_key) values(:id,:t,:receipt,:n,:line,:quantity,:warehouse,:inventory_key)"),{"id":item["receipt_line_id"],"t":t,"receipt":rid,"n":n,"line":item["order_line_id"],"quantity":item["quantity"],"warehouse":item["warehouse_id"],"inventory_key":item["inventory_idempotency_key"]})
            return self._receipt(c,t,rid),plan
    def prepare_reconciliation(self,t,id,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"receipt.reconcile",key,digest)
            if replay:return replay,None
            receipt=self._receipt(c,t,id,True)
            if not receipt:return None,None
            if receipt["status"] not in {"processing","needs_reconciliation"}:raise ValueError("receipt_not_reconcilable")
            c.execute(text("update purchasing.purchase_receipts set reconciliation_attempts=reconciliation_attempts+1,last_reconciliation_at=now(),reconciled_by_actor_id=:actor where tenant_id=:t and id=:id"),{"actor":actor,"t":t,"id":id})
            rows=c.execute(text("""select rl.id receipt_line_id,rl.order_line_id,rl.quantity,rl.warehouse_ref_id warehouse_id,rl.inventory_idempotency_key,ol.inventory_item_ref_id inventory_item_id,ol.line_type,ol.unit_code,ol.unit_price,r.received_at
                from purchasing.purchase_receipt_lines rl join purchasing.purchase_receipts r on r.tenant_id=rl.tenant_id and r.id=rl.receipt_id
                join purchasing.purchase_order_lines ol on ol.tenant_id=rl.tenant_id and ol.id=rl.order_line_id
                where rl.tenant_id=:t and rl.receipt_id=:id and rl.reconciliation_status!='completed' order by rl.line_number for update of rl"""),{"t":t,"id":id}).mappings()
            plan=[{**dict(row),"received_at":row["received_at"].isoformat()} for row in rows]
            return self._receipt(c,t,id),plan
    def _apply_receipt_movements(self,c,t,receipt,plan,movements):
        for item,movement in zip(plan,movements):
            status=c.execute(text("select reconciliation_status from purchasing.purchase_receipt_lines where tenant_id=:t and id=:id for update"),{"t":t,"id":item["receipt_line_id"]}).scalar_one()
            if status=="completed":continue
            c.execute(text("update purchasing.purchase_receipt_lines set reconciliation_status='completed',inventory_movement_ref_id=:m where tenant_id=:t and id=:id"),{"m":movement.get("id"),"t":t,"id":item["receipt_line_id"]})
            c.execute(text("update purchasing.purchase_order_lines set received_quantity=received_quantity+:q where tenant_id=:t and id=:id"),{"q":item["quantity"],"t":t,"id":item["order_line_id"]})
    def _refresh_order_status(self,c,t,order_id):
        totals=c.execute(text("select bool_and(received_quantity=quantity) all_received,bool_or(received_quantity>0) any_received from purchasing.purchase_order_lines where tenant_id=:t and purchase_order_id=:id"),{"t":t,"id":order_id}).mappings().one()
        status="received" if totals["all_received"] else "partially_received" if totals["any_received"] else "issued"
        c.execute(text("update purchasing.purchase_orders set status=:s,updated_at=now() where tenant_id=:t and id=:id and status!='cancelled'"),{"s":status,"t":t,"id":order_id});return status
    def complete_receipt(self,t,receipt,plan,movements,key,actor,error=None,operation="receipt.create"):
        with self.engine.begin() as c:
            self._apply_receipt_movements(c,t,receipt,plan,movements)
            order_status=self._refresh_order_status(c,t,receipt["purchase_order_id"])
            if error:
                remaining=[item["receipt_line_id"] for item in plan[len(movements):]]
                if remaining:c.execute(text("update purchasing.purchase_receipt_lines set reconciliation_status='failed' where tenant_id=:t and id=any(:ids) and reconciliation_status!='completed'"),{"t":t,"ids":remaining})
                c.execute(text("update purchasing.purchase_receipts set status='needs_reconciliation',reconciliation_error=:e where tenant_id=:t and id=:id"),{"e":error,"t":t,"id":receipt["id"]})
                value=self._receipt(c,t,receipt["id"]);self._audit(c,t,actor,operation,"purchase_receipt",receipt["id"],{"result":"needs_reconciliation","completed_lines":len(movements),"error":error});self._finish(c,t,operation,key,value);return value
            c.execute(text("update purchasing.purchase_receipts set status='completed',reconciliation_error=null where tenant_id=:t and id=:id"),{"t":t,"id":receipt["id"]})
            value=self._receipt(c,t,receipt["id"]);self._audit(c,t,actor,operation,"purchase_receipt",receipt["id"],{"result":"completed","order_status":order_status});self._finish(c,t,operation,key,value);return value

def get_purchasing_repository(settings:Settings=Depends(get_settings)): return PurchasingRepository(settings.effective_database_url)
