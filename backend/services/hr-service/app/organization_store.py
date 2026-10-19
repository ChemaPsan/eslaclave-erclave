import hashlib
import json
import re
from datetime import datetime, timezone
from sqlalchemy import text
from erclave_common.organization_client import deny
from .organization_schemas import PositionDivisionRead, WorkerDivisionRead


class OrganizationStore:
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def model(kind):
        return PositionDivisionRead if kind == 'position' else WorkerDivisionRead

    @staticmethod
    def table(kind):
        if kind not in ('position', 'worker'):
            raise ValueError('Unknown HR assignment kind')
        return 'labor_roles' if kind == 'position' else 'workers'

    @staticmethod
    def tariff_context(access, division):
        organization = access.division(division)
        society = next((row for row in access.societies if row.get('id') == organization['society_id']), None)
        currency = society.get('base_currency') if society else None
        if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
            deny('assignment_authority_unavailable', 503)
        return organization['society_id'], currency

    def assignments(self, access, kind, id_, limit, offset, division=None):
        table = self.table(kind)
        if division:
            access.division(division, active=False)
        with self.repository.engine.connect() as conn:
            if not conn.execute(text(f'select id from hr.{table} where tenant_id=:t and id=:i'), {'t': access.tenant_id, 'i': id_}).first():
                deny('assignment_resource_not_found', 404)
            condition = f'tenant_id=:t and {kind}_id=:i'
            params = {'t': access.tenant_id, 'i': id_, 'limit': limit, 'offset': offset, 'divisions': [row['id'] for row in access.divisions]}
            if not access.all_divisions:
                condition += ' and division_ref_id=any(:divisions)'
            if division:
                condition += ' and division_ref_id=:division'
                params['division'] = division
            total = conn.execute(text(f'select count(*) from hr.{kind}_division_assignments where ' + condition), params).scalar_one()
            rows = conn.execute(text(f'select * from hr.{kind}_division_assignments where ' + condition + f' order by division_ref_id limit :limit offset :offset'), params).mappings().all()
        return {'data': [self.model(kind).model_validate(dict(row)).model_dump(mode='json') for row in rows], 'meta': {'total': total, 'limit': limit, 'offset': offset}}

    def eligible(self, access, kind, division, purpose, q, limit, offset, resource_id=None):
        self.table(kind)
        access.division(division)
        query = q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        join = " from hr.position_division_assignments pa join hr.labor_roles r on r.tenant_id=pa.tenant_id and r.id=pa.position_id join hr.labor_areas a on a.tenant_id=r.tenant_id and a.id=r.labor_area_id"
        where = "pa.tenant_id=:t and pa.division_ref_id=:d and pa.status='active' and r.status='active' and a.status='active'"
        if purpose in ('production', 'maintenance'):
            where += f' and r.intervenes_in_{purpose}=true'
        if kind == 'position':
            columns = 'r.id,r.code,r.position name,r.recipe_name,r.labor_area_id,a.name labor_area_name,pa.division_ref_id,pa.hourly_cost,pa.hourly_cost_currency_code,pa.hourly_cost_society_ref_id,pa.hourly_cost_confirmed_at,pa.cost_center_ref_id,r.intervenes_in_production,r.intervenes_in_maintenance'
            where += ' and (r.position ilike :q or r.recipe_name ilike :q or a.name ilike :q)'
            order = 'r.position,r.id'
        else:
            join += ' join hr.worker_division_assignments wa on wa.tenant_id=pa.tenant_id and wa.division_ref_id=pa.division_ref_id and wa.labor_position_id=pa.position_id join hr.workers w on w.tenant_id=wa.tenant_id and w.id=wa.worker_id and w.labor_position_id=wa.labor_position_id'
            where += " and wa.status='active' and w.status='active' and (w.employee_number ilike :q or concat_ws(' ',w.first_names,w.first_last_name,w.second_last_name) ilike :q)"
            columns = "w.id,w.employee_number,concat_ws(' ',w.first_names,w.first_last_name,w.second_last_name) full_name,w.labor_position_id,r.position position_name,r.code position_code,wa.division_ref_id"
            if purpose == 'maintenance':
                society, currency = self.tariff_context(access, division)
                where += ' and pa.hourly_cost_currency_code=:currency and pa.hourly_cost_society_ref_id=:society and pa.hourly_cost_confirmed_at is not null'
                columns += ',wa.revision worker_assignment_revision,pa.revision position_assignment_revision,pa.hourly_cost,pa.hourly_cost_currency_code,pa.hourly_cost_society_ref_id,pa.hourly_cost_society_ref_id society_ref_id,pa.hourly_cost_confirmed_at,r.minutes_per_resource minutes_per_worker'
            order = 'w.employee_number,w.id'
        if resource_id:
            where += ' and ' + ('w.id' if kind == 'worker' else 'r.id') + '=:resource_id'
        params = {'resource_id': resource_id, 't': access.tenant_id, 'd': division, 'q': '%' + query + '%', 'limit': limit, 'offset': offset}
        if kind == 'worker' and purpose == 'maintenance':
            params.update(currency=currency, society=society)
        if kind == 'position':
            society, currency = self.tariff_context(access, division)
            where += ' and pa.hourly_cost_currency_code=:currency and pa.hourly_cost_society_ref_id=:society and pa.hourly_cost_confirmed_at is not null'
            params.update(currency=currency, society=society)
        with self.repository.engine.connect() as conn:
            total = conn.execute(text('select count(*)' + join + ' where ' + where), params).scalar_one()
            rows = conn.execute(text('select ' + columns + join + ' where ' + where + ' order by ' + order + ' limit :limit offset :offset'), params).mappings().all()
        return {'data': [dict(row) for row in rows], 'meta': {'total': total, 'limit': limit, 'offset': offset}}

    def division_production_capacity(self, access, division):
        society, currency = self.tariff_context(access, division)
        # Assignments grant eligibility, never create another physical worker.
        # Consumers must reconcile global worker/date commitments before promising capacity.
        sql = """select r.id position_id,r.position position_name,r.recipe_name,r.labor_area_id,
            a.name labor_area_name,pa.division_ref_id,pa.hourly_cost_society_ref_id society_ref_id,
            count(distinct w.id)::int active_worker_count,r.minutes_per_resource minutes_per_worker,
            count(distinct w.id)*r.minutes_per_resource available_minutes,
            pa.hourly_cost,pa.hourly_cost/60.0 cost_per_minute,pa.hourly_cost_currency_code,
            coalesce(array_agg(distinct w.id order by w.id) filter (where w.id is not null),ARRAY[]::varchar[]) eligible_worker_ids,
            r.id capacity_pool_key
            from hr.position_division_assignments pa
            join hr.labor_roles r on r.tenant_id=pa.tenant_id and r.id=pa.position_id
            join hr.labor_areas a on a.tenant_id=r.tenant_id and a.id=r.labor_area_id
            left join hr.worker_division_assignments wa on wa.tenant_id=pa.tenant_id
                and wa.division_ref_id=pa.division_ref_id and wa.labor_position_id=pa.position_id and wa.status='active'
            left join hr.workers w on w.tenant_id=wa.tenant_id and w.id=wa.worker_id
                and w.labor_position_id=wa.labor_position_id and w.status='active'
            where pa.tenant_id=:tenant and pa.division_ref_id=:division and pa.status='active'
                and pa.hourly_cost_currency_code=:currency and pa.hourly_cost_society_ref_id=:society
                and pa.hourly_cost_confirmed_at is not null
                and r.status='active' and a.status='active' and r.intervenes_in_production=true
            group by r.id,r.position,r.recipe_name,r.labor_area_id,a.name,pa.division_ref_id,
                pa.hourly_cost_society_ref_id,r.minutes_per_resource,pa.hourly_cost,pa.hourly_cost_currency_code
            order by r.recipe_name,r.id"""
        with self.repository.engine.connect() as conn:
            rows = conn.execute(text(sql), {'tenant': access.tenant_id, 'division': division,
                                          'society': society, 'currency': currency}).mappings().all()
        return {'data': [dict(row) for row in rows],
                'meta': {'capacity_scope': 'shared_workers', 'commitments_included': False}}

    def save(self, access, kind, id_, division, payload, key, correlation, client):
        table = self.table(kind)
        t = access.tenant_id
        data = payload.model_dump(mode='json')
        # Omitted expansion fields must not change hashes of pre-confirmation retries.
        if 'hourly_cost_currency_code' not in payload.model_fields_set:
            data.pop('hourly_cost_currency_code', None)
        operation = f'org_assignment.{kind}:{id_}:{division}'
        digest = hashlib.sha256(json.dumps({'actor': access.actor_id, 'payload': data}, sort_keys=True).encode()).hexdigest()
        access.division(division, active=payload.status == 'active')
        with self.repository.engine.begin() as conn:
            # Select only operational fields; never copy a worker's personal identifiers to audit.
            columns = 'id,status,labor_area_id' if kind == 'position' else 'id,status,labor_position_id'
            resource = conn.execute(text(f'select {columns} from hr.{table} where tenant_id=:t and id=:i for update'), {'t': t, 'i': id_}).mappings().first()
            if not resource:
                deny('assignment_resource_not_found', 404)
            before = conn.execute(text(f'select * from hr.{kind}_division_assignments where tenant_id=:t and {kind}_id=:i and division_ref_id=:d'), {'t': t, 'i': id_, 'd': division}).mappings().first()
            before = self.model(kind).model_validate(dict(before)) if before else None
            try:
                replay = self.repository._claim(conn, t, operation, key, digest)
            except ValueError as exc:
                deny(str(exc), 409)
            if replay:
                return replay
            if payload.expected_revision != (before.revision if before else 0):
                deny('assignment_revision_conflict', 409)
            result = {f'{kind}_id': id_, 'division_ref_id': division, 'status': payload.status, 'revision': (before.revision if before else 0) + 1}
            if payload.status == 'inactive':
                if not before:
                    deny('assignment_resource_not_found', 404)
                if kind == 'position' and (payload.hourly_cost != before.hourly_cost or payload.cost_center_ref_id != before.cost_center_ref_id or ('hourly_cost_currency_code' in payload.model_fields_set and payload.hourly_cost_currency_code != before.hourly_cost_currency_code)):
                    deny('hr_assignment_history_locked', 409)
                result = {**before.model_dump(mode='json'), **result}
            else:
                if resource['status'] != 'active':
                    deny('assignment_resource_inactive', 409)
                role = resource if kind == 'position' else conn.execute(text('select id,status,labor_area_id from hr.labor_roles where tenant_id=:t and id=:i for share'), {'t': t, 'i': resource['labor_position_id']}).mappings().first()
                if not role or role['status'] != 'active':
                    deny('hr_assignment_position_unavailable', 409)
                area = conn.execute(text('select status from hr.labor_areas where tenant_id=:t and id=:i for share'), {'t': t, 'i': role['labor_area_id']}).scalar()
                if area != 'active':
                    deny('hr_assignment_area_unavailable', 409)
                if kind == 'worker':
                    enabled = conn.execute(text("select position_id from hr.position_division_assignments where tenant_id=:t and position_id=:i and division_ref_id=:d and status='active' for share"), {'t': t, 'i': role['id'], 'd': division}).first()
                    if not enabled:
                        deny('hr_assignment_position_unavailable', 409)
                    result['labor_position_id'] = role['id']
                else:
                    society, currency = self.tariff_context(access, division)
                    if not payload.hourly_cost_currency_code:
                        deny('hr_tariff_currency_required', 422, 'hourly_cost_currency_code')
                    if payload.hourly_cost_currency_code != currency:
                        deny('hr_tariff_currency_mismatch', 422, 'hourly_cost_currency_code')
                    result.update(hourly_cost_currency_code=currency, hourly_cost_society_ref_id=society, hourly_cost_confirmed_at=datetime.now(timezone.utc))
                    snapshot = client.center(access, payload.cost_center_ref_id, division) if payload.cost_center_ref_id else None
                    result.update(hourly_cost=payload.hourly_cost, cost_center_ref_id=payload.cost_center_ref_id, cost_center_snapshot=snapshot)
            value = self.model(kind).model_validate(result)
            params = {'t': t, **value.model_dump(mode='python')}
            fields = list(type(value).model_fields)
            if kind == 'position':
                params['cost_center_snapshot'] = json.dumps(params['cost_center_snapshot']) if params['cost_center_snapshot'] else None
            values = ['cast(:cost_center_snapshot as jsonb)' if field == 'cost_center_snapshot' else ':' + field for field in fields]
            updates = ','.join(f'{field}=excluded.{field}' for field in fields if field not in (f'{kind}_id', 'division_ref_id'))
            conn.execute(text(f"insert into hr.{kind}_division_assignments(tenant_id,{','.join(fields)}) values(:t,{','.join(values)}) on conflict(tenant_id,{kind}_id,division_ref_id) do update set {updates},updated_at=now()"), params)
            self.repository._audit(conn, t, access.actor_id, 'organization_assignment.' + kind, kind, id_, {'before': before.model_dump(mode='json') if before else None, 'after': value.model_dump(mode='json'), 'correlation_id': correlation, 'idempotency_key': key})
            self.repository._done(conn, t, operation, key, value)
            return value.model_dump(mode='json')
