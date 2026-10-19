import hashlib, json
from sqlalchemy import text
from erclave_common.organization_client import deny
from .organization_schemas import WarehouseDivisionRead, ItemDivisionRead

class OrganizationStore:

    def __init__(self, repository):
        self.repository = repository

    def warehouse(self, access, id_):
        with self.repository.engine.connect() as conn:
            row = conn.execute(text('select id warehouse_id,division_ref_id,division_revision revision from inventory.warehouses where tenant_id=:t and id=:i'), {'t': access.tenant_id, 'i': id_}).mappings().first()
        if row is None:
            deny('assignment_resource_not_found', 404)
        if row['division_ref_id']:
            access.division(row['division_ref_id'], active=False)
        return dict(row)

    def items(self, access, id_, limit, offset, division=None):
        if division:
            access.division(division, active=False)
        with self.repository.engine.connect() as conn:
            if not conn.execute(text('select id from inventory.items where tenant_id=:t and id=:i'), {'t': access.tenant_id, 'i': id_}).first():
                deny('assignment_resource_not_found', 404)
            condition = 'tenant_id=:t and item_id=:i'
            params = {'t': access.tenant_id, 'i': id_, 'limit': limit, 'offset': offset, 'divisions': [row['id'] for row in access.divisions]}
            if not access.all_divisions:
                condition += ' and division_ref_id=any(:divisions)'
            if division:
                condition += ' and division_ref_id=:division'
                params['division'] = division
            total = conn.execute(text('select count(*) from inventory.item_division_assignments where ' + condition), params).scalar_one()
            rows = conn.execute(text('select item_id,division_ref_id,cost_center_ref_id,cost_center_snapshot,status,revision from inventory.item_division_assignments where ' + condition + ' order by division_ref_id limit :limit offset :offset'), params).mappings().all()
        return {'data': [dict(row) for row in rows], 'meta': {'total': total, 'limit': limit, 'offset': offset}}

    def eligible(self, access, division, q, limit, offset):
        access.division(division)
        query = q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        where = "a.tenant_id=:t and a.division_ref_id=:d and a.status='active' and i.status='active' and (i.code ilike :q or i.name ilike :q)"
        join = ' from inventory.item_division_assignments a join inventory.items i on i.tenant_id=a.tenant_id and i.id=a.item_id where ' + where
        params = {'t': access.tenant_id, 'd': division, 'q': '%' + query + '%', 'limit': limit, 'offset': offset}
        with self.repository.engine.connect() as conn:
            total = conn.execute(text('select count(*)' + join), params).scalar_one()
            rows = conn.execute(text('select i.id,i.code,i.name,i.base_unit,a.division_ref_id,a.cost_center_ref_id' + join + ' order by i.code limit :limit offset :offset'), params).mappings().all()
        return {'data': [dict(row) for row in rows], 'meta': {'total': total, 'limit': limit, 'offset': offset}}

    def save(self, access, kind, id_, division, payload, key, correlation, client):
        t = access.tenant_id
        data = payload.model_dump()
        operation = f'organization_assignment.{kind}:{id_}:{division}'
        digest = hashlib.sha256(json.dumps({'actor': access.actor_id, 'payload': data}, sort_keys=True).encode()).hexdigest()
        table = 'warehouses' if kind == 'warehouse' else 'items'
        with self.repository.engine.begin() as conn:
            resource = conn.execute(text(f'select * from inventory.{table} where tenant_id=:t and id=:i for update'), {'t': t, 'i': id_}).mappings().first()
            if not resource:
                deny('assignment_resource_not_found', 404)
            if kind == 'warehouse':
                before = {'warehouse_id': id_, 'division_ref_id': resource['division_ref_id'], 'revision': resource['division_revision']}
                if before['division_ref_id']:
                    access.division(before['division_ref_id'], active=False)
                elif not access.all_divisions:
                    deny('assignment_unassigned_requires_full_scope')
                access.division(division)
            else:
                before = conn.execute(text('select item_id,division_ref_id,cost_center_ref_id,cost_center_snapshot,status,revision from inventory.item_division_assignments where tenant_id=:t and item_id=:i and division_ref_id=:d'), {'t': t, 'i': id_, 'd': division}).mappings().first()
                before = dict(before) if before else None
                access.division(division, active=data['status'] == 'active')
            try:
                replay = self.repository._claim(conn, t, operation, key, digest)
            except ValueError as exc:
                deny(str(exc), 409)
            if replay:
                return replay
            if data['expected_revision'] != (before['revision'] if before else 0):
                deny('assignment_revision_conflict', 409)
            if resource['status'] != 'active' and (kind == 'warehouse' or data['status'] == 'active'):
                deny('assignment_resource_inactive', 409)
            if kind == 'warehouse':
                if before['division_ref_id'] and before['division_ref_id'] != division:
                    deny('assignment_warehouse_division_locked', 409, 'division_ref_id')
                result = WarehouseDivisionRead(warehouse_id=id_, division_ref_id=division, revision=before['revision'] + 1)
                conn.execute(text('update inventory.warehouses set division_ref_id=:d,division_revision=:r,updated_at=now() where tenant_id=:t and id=:i'), {'t': t, 'i': id_, 'd': division, 'r': result.revision})
            else:
                if data['status'] == 'inactive':
                    if not before:
                        deny('assignment_resource_not_found', 404)
                    if data['cost_center_ref_id'] != before['cost_center_ref_id']:
                        deny('assignment_inactive_reference_locked', 409)
                    snapshot = before['cost_center_snapshot']
                else:
                    snapshot = client.center(access, data['cost_center_ref_id'], division) if data['cost_center_ref_id'] else None
                result = ItemDivisionRead(item_id=id_, division_ref_id=division, cost_center_ref_id=data['cost_center_ref_id'], cost_center_snapshot=snapshot, status=data['status'], revision=(before['revision'] if before else 0) + 1)
                conn.execute(text('insert into inventory.item_division_assignments(tenant_id,item_id,division_ref_id,cost_center_ref_id,cost_center_snapshot,status,revision)\n                    values(:t,:item_id,:division_ref_id,:cost_center_ref_id,cast(:snapshot as jsonb),:status,:revision)\n                    on conflict(tenant_id,item_id,division_ref_id) do update set cost_center_ref_id=excluded.cost_center_ref_id,cost_center_snapshot=excluded.cost_center_snapshot,status=excluded.status,revision=excluded.revision,updated_at=now()'), {'t': t, **result.model_dump(), 'snapshot': json.dumps(snapshot) if snapshot else None})
            self.repository._audit(conn, t, access.actor_id, 'organization_assignment.' + kind, kind, id_, {'before': before, 'after': result.model_dump(), 'correlation_id': correlation, 'idempotency_key': key})
            self.repository._done(conn, t, operation, key, result)
            return result.model_dump()
