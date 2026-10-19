import hashlib, json
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from erclave_common.organization_client import deny
from erclave_common.operational_context import society_currency
from .organization_schemas import MachineDivisionRead, ProductServiceDivisionRead, ProductServiceEstimatedCostRead

ASSIGNMENT_COLUMNS = 'product_service_id,division_ref_id,cost_center_ref_id,cost_center_snapshot,status,revision,estimated_unit_cost,cost_currency,cost_society_ref_id,cost_confirmed_at'

class OrganizationStore:

    def __init__(self, repository):
        self.repository = repository

    def machine(self, access, id_):
        with self.repository.engine.connect() as conn:
            row = conn.execute(text('select id machine_id,division_ref_id,division_revision revision from production.machines where tenant_id=:t and id=:i'), {'t': access.tenant_id, 'i': id_}).mappings().first()
        if row is None:
            deny('assignment_resource_not_found', 404)
        if row['division_ref_id']:
            access.division(row['division_ref_id'], active=False)
        return dict(row)

    def products(self, access, id_, limit, offset, division=None):
        if division:
            access.division(division, active=False)
        with self.repository.engine.connect() as conn:
            if not conn.execute(text('select id from production.product_services where tenant_id=:t and id=:i'), {'t': access.tenant_id, 'i': id_}).first():
                deny('assignment_resource_not_found', 404)
            condition = 'tenant_id=:t and product_service_id=:i'
            params = {'t': access.tenant_id, 'i': id_, 'limit': limit, 'offset': offset, 'divisions': [row['id'] for row in access.divisions]}
            if not access.all_divisions:
                condition += ' and division_ref_id=any(:divisions)'
            if division:
                condition += ' and division_ref_id=:division'
                params['division'] = division
            total = conn.execute(text('select count(*) from production.product_service_division_assignments where ' + condition), params).scalar_one()
            rows = conn.execute(text('select ' + ASSIGNMENT_COLUMNS + ' from production.product_service_division_assignments where ' + condition + ' order by division_ref_id limit :limit offset :offset'), params).mappings().all()
        return {'data': [dict(row) for row in rows], 'meta': {'total': total, 'limit': limit, 'offset': offset}}

    def eligible(self, access, division, q, limit, offset, resource_id=None):
        access.division(division)
        query = q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        where = "a.tenant_id=:t and a.division_ref_id=:d and a.status='active' and i.status='active' and (i.code ilike :q or i.name ilike :q)"
        if resource_id:
            where += ' and i.id=:resource_id'
        join = ' from production.product_service_division_assignments a join production.product_services i on i.tenant_id=a.tenant_id and i.id=a.product_service_id where ' + where
        params = {'resource_id': resource_id, 't': access.tenant_id, 'd': division, 'q': '%' + query + '%', 'limit': limit, 'offset': offset}
        with self.repository.engine.connect() as conn:
            total = conn.execute(text('select count(*)' + join), params).scalar_one()
            rows = conn.execute(text('select i.id,i.code,i.name,i.base_unit,a.division_ref_id,a.cost_center_ref_id' + join + ' order by i.code limit :limit offset :offset'), params).mappings().all()
        return {'data': [dict(row) for row in rows], 'meta': {'total': total, 'limit': limit, 'offset': offset}}

    def save(self, access, kind, id_, division, payload, key, correlation, client):
        t = access.tenant_id
        data = payload.model_dump()
        operation = f'org_assignment.{kind}:{id_}:{division}'
        digest = hashlib.sha256(json.dumps({'actor': access.actor_id, 'payload': data}, sort_keys=True).encode()).hexdigest()
        table = 'machines' if kind == 'machine' else 'product_services'
        with self.repository.engine.begin() as conn:
            resource = conn.execute(text(f'select * from production.{table} where tenant_id=:t and id=:i for update'), {'t': t, 'i': id_}).mappings().first()
            if not resource:
                deny('assignment_resource_not_found', 404)
            if kind == 'machine':
                before = {'machine_id': id_, 'division_ref_id': resource['division_ref_id'], 'revision': resource['division_revision']}
                if before['division_ref_id']:
                    access.division(before['division_ref_id'], active=False)
                elif not access.all_divisions:
                    deny('assignment_machine_requires_full_scope')
                access.division(division)
            else:
                before = conn.execute(text('select ' + ASSIGNMENT_COLUMNS + ' from production.product_service_division_assignments where tenant_id=:t and product_service_id=:i and division_ref_id=:d'), {'t': t, 'i': id_, 'd': division}).mappings().first()
                before = dict(before) if before else None
                access.division(division, active=data['status'] == 'active')
            replay = self.repository._claim_idempotency(conn, t, operation, key, digest, access.actor_id)
            if replay:
                return replay
            if data['expected_revision'] != (before['revision'] if before else 0):
                deny('assignment_revision_conflict', 409)
            if resource['status'] != 'active' and (kind == 'machine' or data['status'] == 'active'):
                deny('assignment_resource_inactive', 409)
            if kind == 'machine':
                if before['division_ref_id'] and before['division_ref_id'] != division:
                    deny('assignment_machine_division_locked', 409, 'division_ref_id')
                result = MachineDivisionRead(machine_id=id_, division_ref_id=division, revision=before['revision'] + 1)
                conn.execute(text('update production.machines set division_ref_id=:d,division_revision=:r,updated_at=now() where tenant_id=:t and id=:i'), {'t': t, 'i': id_, 'd': division, 'r': result.revision})
            else:
                if data['status'] == 'inactive':
                    if not before:
                        deny('assignment_resource_not_found', 404)
                    if data['cost_center_ref_id'] != before['cost_center_ref_id']:
                        deny('assignment_inactive_reference_locked', 409)
                    snapshot = before['cost_center_snapshot']
                else:
                    snapshot = client.center(access, data['cost_center_ref_id'], division) if data['cost_center_ref_id'] else None
                preserved_cost = {name: before[name] if before else None for name in ('estimated_unit_cost','cost_currency','cost_society_ref_id','cost_confirmed_at')}
                result = ProductServiceDivisionRead(product_service_id=id_, division_ref_id=division, cost_center_ref_id=data['cost_center_ref_id'], cost_center_snapshot=snapshot, status=data['status'], revision=(before['revision'] if before else 0) + 1, **preserved_cost)
                conn.execute(text('insert into production.product_service_division_assignments(tenant_id,product_service_id,division_ref_id,cost_center_ref_id,cost_center_snapshot,status,revision)\n                    values(:t,:product_service_id,:division_ref_id,:cost_center_ref_id,cast(:snapshot as jsonb),:status,:revision)\n                    on conflict(tenant_id,product_service_id,division_ref_id) do update set cost_center_ref_id=excluded.cost_center_ref_id,cost_center_snapshot=excluded.cost_center_snapshot,status=excluded.status,revision=excluded.revision,updated_at=now()'), {'t': t, **result.model_dump(), 'snapshot': json.dumps(snapshot) if snapshot else None})
            result_data = result.model_dump(mode='json')
            self.repository._audit(conn, t, access.actor_id, 'organization_assignment.' + kind, kind, id_, before, {**result_data, 'correlation_id': correlation}, key)
            self.repository._complete_idempotency(conn, t, operation, key, result_data, 200)
            return result_data

    def estimated_cost(self, access, product_service_id, division_id):
        division = access.division(division_id)
        with self.repository.engine.connect() as conn:
            product = conn.execute(text('select status from production.product_services where tenant_id=:t and id=:i'), {'t':access.tenant_id,'i':product_service_id}).scalar()
            if product is None:deny('assignment_resource_not_found',404)
            row = conn.execute(text('select a.estimated_unit_cost,a.cost_currency,a.cost_society_ref_id,a.cost_confirmed_at,a.revision,a.status from production.product_service_division_assignments a where a.tenant_id=:t and a.product_service_id=:i and a.division_ref_id=:d'), {'t':access.tenant_id,'i':product_service_id,'d':division_id}).mappings().first()
        if product!='active' or not row or row['status']!='active' or row['cost_confirmed_at'] is None:
            return None
        try:current_currency=society_currency(access,division['society_id'])
        except ErclaveError:return None
        if row['cost_society_ref_id']!=division['society_id'] or row['cost_currency']!=current_currency:
            return None
        return ProductServiceEstimatedCostRead(product_service_id=product_service_id,division_ref_id=division_id,society_ref_id=row['cost_society_ref_id'],cost_currency=row['cost_currency'],estimated_unit_cost=row['estimated_unit_cost'],assignment_revision=row['revision'],confirmed_at=row['cost_confirmed_at'])

    def confirm_estimated_cost(self, access, product_service_id, division_id, payload, key, correlation):
        division = access.division(division_id)
        currency = society_currency(access,division['society_id']) if payload.estimated_unit_cost is not None else None
        if payload.cost_currency != currency:
            deny('operational_cost_currency_mismatch',422,'cost_currency')
        t = access.tenant_id
        operation = f'product_service.estimated_cost:{product_service_id}:{division_id}'
        digest = hashlib.sha256(json.dumps({'actor':access.actor_id,'payload':payload.model_dump(mode='json')},sort_keys=True).encode()).hexdigest()
        with self.repository.engine.begin() as conn:
            product = conn.execute(text('select status from production.product_services where tenant_id=:t and id=:i for update'), {'t':t,'i':product_service_id}).scalar()
            if product is None:deny('assignment_resource_not_found',404)
            before = conn.execute(text('select ' + ASSIGNMENT_COLUMNS + ' from production.product_service_division_assignments where tenant_id=:t and product_service_id=:i and division_ref_id=:d for update'), {'t':t,'i':product_service_id,'d':division_id}).mappings().first()
            if not before:deny('assignment_resource_not_found',404)
            replay = self.repository._claim_idempotency(conn,t,operation,key,digest,access.actor_id)
            if replay:return replay
            if payload.expected_revision != before['revision']:deny('assignment_revision_conflict',409)
            if product!='active' or before['status']!='active':deny('assignment_resource_inactive',409)
            row = conn.execute(text('update production.product_service_division_assignments set estimated_unit_cost=:cost,cost_currency=:currency,cost_society_ref_id=:society,cost_confirmed_at=case when :clearing then null else now() end,revision=revision+1,updated_at=now() where tenant_id=:t and product_service_id=:i and division_ref_id=:d returning ' + ASSIGNMENT_COLUMNS), {'cost':payload.estimated_unit_cost,'currency':currency,'society':division['society_id'] if currency else None,'clearing':payload.estimated_unit_cost is None,'t':t,'i':product_service_id,'d':division_id}).mappings().one()
            result = ProductServiceDivisionRead.model_validate(dict(row)).model_dump(mode='json')
            self.repository._audit(conn,t,access.actor_id,'product_service.estimated_cost','product_service',product_service_id,dict(before),{**result,'correlation_id':correlation},key)
            self.repository._complete_idempotency(conn,t,operation,key,result,200)
            return result
