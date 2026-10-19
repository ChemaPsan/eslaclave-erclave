"""Machine monetary confirmation and shared physical capacity owned by Production."""
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text
from erclave_common.organization_client import deny
from erclave_common.operational_context import society_currency


def confirmed_tariff_update(before, payload, access):
    """Validate a new command against the locked master; never label legacy money."""
    division = before.get('division_ref_id')
    if division:
        if access is None: deny('organization_scope_review_required', 409)
        row = access.division(division)
    else:
        row = None
    currency = payload.cost_currency
    amount = payload.cost_per_minute
    if currency is None:
        if amount is not None and before.get('cost_currency') is not None:
            deny('machine_tariff_confirmation_required', 422, 'cost_currency')
        return {}
    if row is None:
        deny('operational_context_required', 409, 'cost_currency')
    expected = society_currency(access, row['society_id'])
    if currency != expected:
        deny('operational_cost_currency_mismatch', 422, 'cost_currency')
    return {'cost_society_ref_id':row['society_id'], 'cost_confirmed_at':datetime.now(timezone.utc)}


class MachineCapacityStore:
    def __init__(self, repository):
        self.repository = repository

    def eligible(self, access, division, planned_date, q, limit, offset, resource_id=None):
        row = access.division(division)
        currency = society_currency(access, row['society_id'])
        query = q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        where = "m.tenant_id=:t and m.division_ref_id=:d and m.status='active' and m.maintenance_order_ref_id is null and m.cost_currency=:currency and m.cost_society_ref_id=:society and m.cost_confirmed_at is not null and (m.code ilike :q or m.name ilike :q)"
        if resource_id: where += ' and m.id=:id'
        params = {'t':access.tenant_id, 'd':division, 'currency':currency, 'society':row['society_id'], 'q':'%'+query+'%', 'id':resource_id, 'limit':limit, 'offset':offset, 'day':planned_date}
        with self.repository.engine.connect() as conn:
            total = conn.execute(text('select count(*) from production.machines m where '+where),params).scalar_one()
            rows = conn.execute(text("""select m.id,m.code,m.name,m.division_ref_id,m.cost_society_ref_id,m.cost_currency,m.cost_per_minute,m.cost_confirmed_at,m.available_minutes_per_day,
                coalesce((select sum(c.quantity_minutes) from production.capacity_commitments c
                  where c.tenant_id=m.tenant_id and c.resource_type='machine' and c.resource_ref_id=m.id
                  and c.planned_date=:day and c.status='active'),0) committed_minutes
                from production.machines m where """+where+' order by m.code,m.id limit :limit offset :offset'),params).mappings().all()
        values=[]
        for source in rows:
            value=dict(source)
            gross=Decimal(str(value['available_minutes_per_day'])) if planned_date.weekday()<5 else Decimal('0')
            value.update(planned_date=planned_date, available_minutes=max(Decimal('0'),gross-Decimal(str(value['committed_minutes']))), capacity_pool_key=value['id'])
            values.append(value)
        return {'data':values,'meta':{'total':total,'limit':limit,'offset':offset,'capacity_scope':'physical_machine','commitments_included':True}}
