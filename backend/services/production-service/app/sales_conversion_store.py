"""Production-owned Sales request conversion, serialized before external reservations."""
from decimal import Decimal
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from .schemas import ProductionSalesRequestRead, ProductionSalesStatusRead


def reject(code, details=None):
    raise ErclaveError(code,'Sales production request cannot continue with this source or state.',status_code=409,details=details)

class SalesConversionRepository:
    def get_sales_request(self,tenant,id):
        with self.engine.connect() as c:return self._read_sales_request(c,tenant,id)

    def sales_request_source(self,tenant,id):
        with self.engine.connect() as c:
            row=c.execute(text('select source_snapshot from production.sales_order_requests where tenant_id=:t and id=:id'),{'t':tenant,'id':id}).mappings().first()
            return row['source_snapshot'] if row else None

    def request_for_order(self,tenant,order_id):
        with self.engine.connect() as c:
            id=c.execute(text('select id from production.sales_order_requests where tenant_id=:t and production_order_ref_id=:id'),{'t':tenant,'id':order_id}).scalar()
            return self._read_sales_request(c,tenant,id) if id else None

    def replay_sales_request(self,tenant,key,request_hash,actor):
        with self.engine.connect() as c:
            row=c.execute(text("select * from production.idempotency_records where tenant_id=:t and operation='sales_order_request.create' and idempotency_key=:k"),{'t':tenant,'k':key}).mappings().first()
            if not row:return None
            if row['actor_id']!=actor:raise ErclaveError('idempotency_actor_mismatch','Actor mismatch.',status_code=403)
            if row['request_hash']!=request_hash:reject('idempotency_key_reused')
            if row['state']!='completed':reject('idempotency_request_in_progress')
            return ProductionSalesRequestRead.model_validate(row['response_payload'])

    def sales_request_status(self,tenant,id):
        with self.engine.connect() as c:
            row=c.execute(text('select r.id request_id,r.status,r.sales_order_id,r.sales_order_line_id,r.product_service_ref_id product_service_id,r.quantity,r.unit,r.organization_context,r.production_order_ref_id production_order_id,o.status production_order_status,o.planned_cost,o.actual_cost from production.sales_order_requests r left join production.production_orders o on o.tenant_id=r.tenant_id and o.id=r.production_order_ref_id where r.tenant_id=:t and r.id=:id'),{'t':tenant,'id':id}).mappings().first()
            if not row:return None
            values=dict(row);planned=values.pop('planned_cost');actual=values.pop('actual_cost');context=values['organization_context']
            return ProductionSalesStatusRead(**values,original_planned_cost=planned if context else None,original_actual_cost=actual if context else None,cost_currency=context['cost_currency'] if context else None)

    def select_sales_attempt(self,tenant,request_id,attempt_id):
        with self.engine.begin() as c:
            row=c.execute(text('select * from production.sales_order_requests where tenant_id=:t and id=:id for update'),{'t':tenant,'id':request_id}).mappings().one()
            if row['production_order_ref_id']:
                if row['production_order_ref_id']!=attempt_id:reject('production_request_already_converted',{'order_id':row['production_order_ref_id']})
                return
            if row['status']=='cancelled':reject('production_request_cancelled')
            old=row['creation_attempt_ref_id']
            if old and old!=attempt_id:
                self._require_attempt_recovered(c,tenant,old)
            c.execute(text('update production.sales_order_requests set creation_attempt_ref_id=:a,updated_at=now() where tenant_id=:t and id=:id'),{'t':tenant,'id':request_id,'a':attempt_id})

    def _require_attempt_recovered(self,c,tenant,attempt):
        intent=c.execute(text('select 1 from production.order_creation_contexts where tenant_id=:t and order_id=:id'),{'t':tenant,'id':attempt}).first()
        status=c.execute(text('select status from production.failed_order_creations where tenant_id=:t and order_id=:id'),{'t':tenant,'id':attempt}).scalar()
        if status!='recovered':reject('production_creation_recovery_pending',{'attempt_id':attempt})

    def link_sales_conversion(self,c,tenant,id,order_id,payload,context,actor,key):
        before=self._read_sales_request(c,tenant,id)
        row=c.execute(text('select * from production.sales_order_requests where tenant_id=:t and id=:id for update'),{'t':tenant,'id':id}).mappings().one()
        product=c.execute(text('select r.product_service_id from production.recipes r join production.recipe_versions v on v.tenant_id=r.tenant_id and v.recipe_id=r.id where v.tenant_id=:t and v.id=:id'),{'t':tenant,'id':payload.recipe_version_id}).scalar()
        if row['status']!='pending_configuration' or row['production_order_ref_id']:reject('production_request_already_converted')
        if row['creation_attempt_ref_id']!=order_id or product!=row['product_service_ref_id'] or Decimal(str(payload.quantity))!=row['quantity'] or payload.unit!=row['unit'] or payload.source_id!=row['sales_order_id'] or payload.source_line_id!=row['sales_order_line_id'] or (context.model_dump(mode='json') if context else None)!=row['organization_context']:reject('production_request_source_conflict')
        c.execute(text("update production.sales_order_requests set production_order_ref_id=:o,status='converted',updated_at=now() where tenant_id=:t and id=:id"),{'t':tenant,'id':id,'o':order_id})
        after=self._read_sales_request(c,tenant,id)
        self._audit(c,tenant,actor,'sales_order_request.convert','sales_order_request',id,before.model_dump(mode='json'),after.model_dump(mode='json'),key)

    def cancel_sales_request(self,tenant,id,payload,key,request_hash,actor):
        with self.engine.begin() as c:
            replay=self._claim_idempotency(c,tenant,'sales_order_request.cancel',key,request_hash,actor)
            if replay is not None:return ProductionSalesRequestRead.model_validate(replay)
            before=self._read_sales_request(c,tenant,id)
            if before.production_order_ref_id:
                state=c.execute(text('select status from production.production_orders where tenant_id=:t and id=:id for share'),{'t':tenant,'id':before.production_order_ref_id}).scalar()
                if state!='cancelled':reject('production_request_has_order',{'order_id':before.production_order_ref_id})
            row=c.execute(text('select creation_attempt_ref_id from production.sales_order_requests where tenant_id=:t and id=:id for update'),{'t':tenant,'id':id}).mappings().one()
            if not before.production_order_ref_id and row['creation_attempt_ref_id']:self._require_attempt_recovered(c,tenant,row['creation_attempt_ref_id'])
            c.execute(text("update production.sales_order_requests set status='cancelled',updated_at=now() where tenant_id=:t and id=:id"),{'t':tenant,'id':id})
            value=self._read_sales_request(c,tenant,id)
            self._audit(c,tenant,actor,'sales_order_request.cancel','sales_order_request',id,before.model_dump(mode='json'),dict(value.model_dump(mode='json'),reason=payload.reason),key)
            self._complete_idempotency(c,tenant,'sales_order_request.cancel',key,value.model_dump(mode='json'),200)
            return value

    def sales_request_by_line(self,tenant,line_id):
        with self.engine.connect() as c:
            id=c.execute(text('select id from production.sales_order_requests where tenant_id=:t and sales_order_line_id=:line'),{'t':tenant,'line':line_id}).scalar()
            return self._read_sales_request(c,tenant,id) if id else None

    def sales_request_recipes(self,tenant,request,q,limit,offset):
        params={'t':tenant,'p':request.product_service_id,'q':'%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%','limit':limit,'offset':offset}
        query=" from production.recipes r join production.recipe_versions v on v.tenant_id=r.tenant_id and v.id=r.current_version_id join production.product_services p on p.tenant_id=r.tenant_id and p.id=r.product_service_id where r.tenant_id=:t and r.product_service_id=:p and p.status='active' and v.status='approved' and (r.code ilike :q or r.name ilike :q)"
        if request.organization_context:
            query+=" and exists(select 1 from production.product_service_division_assignments a where a.tenant_id=r.tenant_id and a.product_service_id=r.product_service_id and a.division_ref_id=:d and a.status='active')"
            params['d']=request.organization_context.division_ref_id
        with self.engine.connect() as c:
            total=c.execute(text('select count(*)'+query),params).scalar_one()
            ids=c.execute(text('select r.id'+query+' order by r.code,r.id limit :limit offset :offset'),params).scalars().all()
            return {'data':[self._read_recipe(c,tenant,id) for id in ids],'page':{'total':total,'limit':limit,'offset':offset}}

    def sales_requests_count(self,tenant,status,q,scope):
        from .order_context import scope_sql
        clause,params=scope_sql(scope)
        if status:clause+=' and status=:status'
        if q:clause+=' and (sales_order_id ilike :q or product_service_code_snapshot ilike :q or product_service_name_snapshot ilike :q)'
        params.update(t=tenant,status=status,q='%'+q.replace('%','\\%').replace('_','\\_')+'%')
        with self.engine.connect() as c:return c.execute(text('select count(*) from production.sales_order_requests where tenant_id=:t'+clause),params).scalar_one()

    def release_unstarted_sales_attempt(self,tenant,request_id,attempt_id):
        with self.engine.begin() as c:
            c.execute(text("update production.sales_order_requests set creation_attempt_ref_id=null,updated_at=now() where tenant_id=:t and id=:id and creation_attempt_ref_id=:a and production_order_ref_id is null and not exists(select 1 from production.order_creation_contexts where tenant_id=:t and order_id=:a) and not exists(select 1 from production.failed_order_creations where tenant_id=:t and order_id=:a)"),{'t':tenant,'id':request_id,'a':attempt_id})
