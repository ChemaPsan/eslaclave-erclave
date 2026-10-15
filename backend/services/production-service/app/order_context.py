"""Production owns document context; Admin authorizes it, owners validate resources."""
import json
from sqlalchemy import text
from erclave_common.config import get_settings
from erclave_common.operational_context import OperationalContext, society_currency
from erclave_common.organization_client import OrganizationClient, resolve_organization_access, deny


def production_access(tenant, authorization, permission, actor=None):
    client=OrganizationClient(get_settings())
    return resolve_organization_access(client.session(tenant,authorization,actor),tenant,'production',permission,authorization)


def guard_order(order, tenant, authorization, permission, actor=None, active=True):
    context=getattr(order,'organization_context',None) if order else None
    if context:
        context.authorize(production_access(tenant,authorization,permission,actor),active=active)
    return context


def manual_context(division, tenant, authorization, permission, actor=None):
    if division is None:return None
    access=production_access(tenant,authorization,permission,actor)
    row=access.division(division)
    return OperationalContext(division_ref_id=division,society_ref_id=row['society_id'],division_code=row['code'],division_name=row['name'],cost_currency=society_currency(access,row['society_id']))


def scope_sql(access, column='organization_context'):
    if access is None:return f' and {column} is null',{}
    if access.all_divisions:return '',{}
    return f" and ({column} is null or {column}->>'division_ref_id'=any(:scope_divisions))",{'scope_divisions':[row['id'] for row in access.divisions]}


class ProductionContextRepository:
    def pending_creation_context(self,tenant,order_id,actor,request_hash):
        from erclave_common.operational_context import OperationalContext
        with self.engine.connect() as conn:
            row=conn.execute(text('select actor_id,request_hash,organization_context from production.order_creation_contexts where tenant_id=:t and order_id=:id'),{'t':tenant,'id':order_id}).mappings().first()
            if row is None:return None
            if row['actor_id']!=actor:deny('idempotency_actor_mismatch',403)
            if row['request_hash']!=request_hash:deny('idempotency_key_reused',409)
            return OperationalContext.model_validate(row['organization_context'])

    def division_recipes(self,access,division,q,limit,offset):
        access.division(division)
        params={'t':access.tenant_id,'d':division,'q':'%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%','limit':limit,'offset':offset}
        query=" from production.recipes r join production.product_services p on p.tenant_id=r.tenant_id and p.id=r.product_service_id join production.product_service_division_assignments a on a.tenant_id=p.tenant_id and a.product_service_id=p.id join production.recipe_versions v on v.tenant_id=r.tenant_id and v.id=r.current_version_id where r.tenant_id=:t and a.division_ref_id=:d and a.status='active' and p.status='active' and v.status='approved' and (r.code ilike :q or r.name ilike :q or p.code ilike :q or p.name ilike :q)"
        with self.engine.connect() as conn:
            total=conn.execute(text('select count(*)'+query),params).scalar_one()
            ids=conn.execute(text('select r.id'+query+' order by r.code,r.id limit :limit offset :offset'),params).scalars().all()
            data=[self._read_recipe(conn,access.tenant_id,id_) for id_ in ids]
        return {'data':data,'meta':{'total':total,'limit':limit,'offset':offset}}

    def replay_order_creation(self,tenant,key,request_hash,actor):
        from .schemas import ProductionOrderRead
        with self.engine.connect() as connection:
            row=connection.execute(text("select request_hash,actor_id,state,response_payload from production.idempotency_records where tenant_id=:t and operation='order.create' and idempotency_key=:key"),{'t':tenant,'key':key}).mappings().first()
            if row is None:return None
            if row['actor_id']!=actor:deny('idempotency_actor_mismatch',403)
            if row['request_hash']!=request_hash:deny('idempotency_key_reused',409)
            if row['state']!='completed' or row['response_payload'] is None:deny('idempotency_request_in_progress',409)
            return ProductionOrderRead.model_validate(row['response_payload'])

    def has_scoped_orders(self,tenant):
        with self.engine.connect() as connection:
            return bool(connection.execute(text('select 1 from production.production_orders where tenant_id=:t and organization_context is not null union all select 1 from production.sales_order_requests where tenant_id=:t and organization_context is not null limit 1'),{'t':tenant}).first())

    def stage_order(self,tenant,stage_id):
        with self.engine.connect() as connection:
            order_id=connection.execute(text('select production_order_id from production.production_order_stages where tenant_id=:t and id=:id'),{'t':tenant,'id':stage_id}).scalar()
            return self._read_order(connection,tenant,order_id) if order_id else None

    def validate_context_resources(self,connection,tenant,version,context):
        if context is None:
            # A legacy order cannot silently use a physically assigned machine.
            ids=[row.resource_ref_id for row in version.resources if row.resource_type=='machine']
            if ids and connection.execute(text('select 1 from production.machines where tenant_id=:t and id=any(:ids) and division_ref_id is not null limit 1'),{'t':tenant,'ids':ids}).first():deny('operational_context_required',409)
            return
        recipe=connection.execute(text('select product_service_id from production.recipes where tenant_id=:t and id=:id'),{'t':tenant,'id':version.recipe_id}).scalar()
        product=connection.execute(text('select status from production.product_services where tenant_id=:t and id=:id for share'),{'t':tenant,'id':recipe}).scalar()
        assignment=connection.execute(text('select status from production.product_service_division_assignments where tenant_id=:t and product_service_id=:id and division_ref_id=:d for share'),{'t':tenant,'id':recipe,'d':context.division_ref_id}).scalar()
        if product!='active' or assignment!='active':deny('operational_context_resource_unavailable',422,'recipe_version_id')
        ids=sorted({row.resource_ref_id for row in version.resources if row.resource_type=='machine'})
        for id_ in ids:
            machine=connection.execute(text('select division_ref_id,status from production.machines where tenant_id=:t and id=:id for share'),{'t':tenant,'id':id_}).mappings().first()
            if not machine or machine['division_ref_id']!=context.division_ref_id or machine['status']!='active':deny('operational_context_resource_unavailable',422,'recipe_version_id')

    def prepare_creation_context(self,tenant,order_id,actor,request_hash,context,preview):
        if context is None:return
        allocations=[{'line_id':f'{row.resource_ref_id}:{index}','inventory_item_id':row.resource_ref_id,'warehouse_id':allocation['warehouse_id'],'quantity':str(allocation['quantity']),'unit':row.unit} for row in preview.rows if row.resource_type=='material' for index,allocation in enumerate(row.allocations)]
        with self.engine.begin() as connection:
            connection.execute(text("insert into production.order_creation_contexts(tenant_id,order_id,actor_id,request_hash,organization_context,allocations) values(:t,:id,:actor,:hash,cast(:ctx as jsonb),cast(:allocations as jsonb)) on conflict(tenant_id,order_id) do nothing"),{'t':tenant,'id':order_id,'actor':actor,'hash':request_hash,'ctx':context.model_dump_json(),'allocations':json.dumps(allocations)})
            row=connection.execute(text('select * from production.order_creation_contexts where tenant_id=:t and order_id=:id for update'),{'t':tenant,'id':order_id}).mappings().one()
            if row['actor_id']!=actor or row['request_hash']!=request_hash or row['organization_context']!=context.model_dump() or row['allocations']!=allocations:deny('idempotency_key_reused',409)

    def creation_context(self,tenant,order_id,actor,line_id):
        with self.engine.connect() as connection:
            row=connection.execute(text('select * from production.order_creation_contexts where tenant_id=:t and order_id=:id'),{'t':tenant,'id':order_id}).mappings().first()
            if row is None:return None
            if row['actor_id']!=actor:deny('permission_denied',403)
            failed=connection.execute(text('select 1 from production.failed_order_creations where tenant_id=:t and order_id=:id'),{'t':tenant,'id':order_id}).first()
            if failed:deny('production_creation_attempt_failed',409)
            allocation=next((item for item in row['allocations'] if item['line_id']==line_id),None)
            if allocation is None:deny('operational_context_mismatch',422)
            return {'order_id':order_id,'organization_context':row['organization_context'],'allocation':allocation}


def read_scope(repository,tenant,authorization,permission):
    if not hasattr(repository,'has_scoped_orders') or not repository.has_scoped_orders(tenant):return None
    return production_access(tenant,authorization,permission)
