"""Division-bound validation. Production commits physical workers globally, never per Division."""
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import text
from erclave_common.organization_client import deny
from .schemas import ResourceValidationRead, ResourceValidationRow

ZERO=Decimal('0')
def decimal(value):return Decimal(str(value))
def money(value):return decimal(value).quantize(Decimal('0.000001'),rounding=ROUND_HALF_UP)

def lock_resources(connection,tenant,version,observations,days):
    keys={f'production:{tenant}:labor-capacity:{day}' for day in days}
    for row in version.resources:
        if row.resource_type=='machine':
            keys.update(f'production:{tenant}:machine:{row.resource_ref_id}:{day}' for day in days)
    for observation in observations:
        if observation.resource_type=='labor':
            keys.update(f'production:{tenant}:worker:{worker}:{day}' for worker in observation.eligible_worker_ids for day in days)
            # Same position lock as legacy commands prevents concurrent use of unallocated legacy labor.
            keys.update(f'production:{tenant}:labor:{observation.resource_ref_id}:{day}' for day in days)
    for key in sorted(keys):connection.execute(text('select pg_advisory_xact_lock(hashtextextended(:key,0))'),{'key':key})

def validate(repository,connection,tenant,payload,observations,context,version):
    from .repositories import production_dates
    repository.validate_context_resources(connection,tenant,version,context)
    planned_start=payload.planned_start_date or payload.planned_for or date.today()
    horizon=production_dates(planned_start,365)
    days=horizon[:payload.planned_duration_days]
    observed={(row.resource_type,row.resource_ref_id,row.unit):row for row in observations}
    rows=[];blockers=[];used_workers={};used_machines={};seen=set();minimum=1
    for resource in version.resources:
        identity=(resource.resource_type,resource.resource_ref_id,resource.unit)
        if identity in seen:deny('recipe_resource_duplicate',422,'recipe_version_id')
        seen.add(identity)
        required=money(decimal(resource.quantity)*decimal(payload.quantity)/decimal(version.base_quantity))
        obs=observed.get(identity)
        source=obs.source if obs else 'unavailable'
        cost=ZERO;available=ZERO;allocations=[];daily=[];blocker=None
        if resource.resource_type=='material':
            if obs is None or obs.original_unit_cost is None or obs.cost_currency!=context.cost_currency:
                deny('operational_cost_currency_unavailable',409)
            cost=obs.original_unit_cost;available=decimal(obs.available_quantity);allocations=obs.allocations
        elif resource.resource_type=='machine':
            machine=connection.execute(text('select division_ref_id,cost_currency,cost_society_ref_id,cost_confirmed_at,status,maintenance_order_ref_id,available_minutes_per_day,cost_per_minute from production.machines where tenant_id=:t and id=:id for share'),{'t':tenant,'id':resource.resource_ref_id}).mappings().first()
            if not machine or machine['division_ref_id']!=context.division_ref_id or machine['cost_currency']!=context.cost_currency or machine['cost_society_ref_id']!=context.society_ref_id or not machine['cost_confirmed_at']:
                deny('operational_context_resource_unavailable',422,'recipe_version_id')
            cost=decimal(machine['cost_per_minute']);source='production.machines'
            gross=decimal(machine['available_minutes_per_day']) if machine['status']=='active' and not machine['maintenance_order_ref_id'] else ZERO
            commits=connection.execute(text("select planned_date,sum(quantity_minutes) quantity from production.capacity_commitments where tenant_id=:t and resource_type='machine' and resource_ref_id=:id and status='active' and planned_date between :start and :end group by planned_date"),{'t':tenant,'id':resource.resource_ref_id,'start':horizon[0],'end':horizon[-1]}).mappings().all()
            by_day={r['planned_date']:decimal(r['quantity']) for r in commits};remaining=required;cumulative=ZERO;needed=None
            for n,day in enumerate(horizon,1):
                committed=by_day.get(day,ZERO)+used_machines.get((resource.resource_ref_id,day),ZERO)
                net=max(ZERO,gross-committed);cumulative+=net
                if needed is None and cumulative>=required:needed=n
                if day in days:
                    taken=min(remaining,net);remaining-=taken;available+=net
                    used_machines[(resource.resource_ref_id,day)]=used_machines.get((resource.resource_ref_id,day),ZERO)+taken
                    daily.append({'planned_date':day,'gross_capacity':gross,'committed_quantity':committed,'available_quantity':net,'allocated_quantity':taken,'remaining_capacity':net-taken})
            minimum=max(minimum,needed or 366)
        elif resource.resource_type=='labor':
            if obs is None or obs.original_unit_cost is None or obs.cost_currency!=context.cost_currency or obs.minutes_per_worker is None:
                deny('operational_context_resource_unavailable',422,'recipe_version_id')
            workers=sorted(set(obs.eligible_worker_ids));per_worker=obs.minutes_per_worker;cost=obs.original_unit_cost
            commits=connection.execute(text("select worker_ref_id,planned_date,sum(quantity_minutes) quantity from production.labor_worker_commitments where tenant_id=:t and worker_ref_id=any(:workers) and status='active' and planned_date between :start and :end group by worker_ref_id,planned_date"),{'t':tenant,'workers':workers,'start':horizon[0],'end':horizon[-1]}).mappings().all()
            by_worker={(r['worker_ref_id'],r['planned_date']):decimal(r['quantity']) for r in commits}
            legacy=connection.execute(text("select c.planned_date,sum(c.quantity_minutes) quantity from production.capacity_commitments c join production.production_orders o on o.tenant_id=c.tenant_id and o.id=c.production_order_id where c.tenant_id=:t and c.resource_type='labor' and c.status='active' and o.organization_context is null and c.planned_date between :start and :end group by c.planned_date"),{'t':tenant,'id':resource.resource_ref_id,'start':horizon[0],'end':horizon[-1]}).mappings().all()
            legacy_days={r['planned_date'] for r in legacy if decimal(r['quantity'])>0}
            remaining=required;cumulative=ZERO;needed=None
            for n,day in enumerate(horizon,1):
                free={worker:max(ZERO,per_worker-by_worker.get((worker,day),ZERO)-used_workers.get((worker,day),ZERO)) for worker in workers}
                net=sum(free.values(),ZERO) if day not in legacy_days else ZERO
                cumulative+=net
                if needed is None and cumulative>=required:needed=n
                if day not in days:continue
                available+=net;day_remaining=min(remaining,net);taken=day_remaining;assignments=[]
                if day in legacy_days:blocker='production_legacy_labor_capacity_review_required'
                for worker in workers:
                    quantity=min(day_remaining,free[worker])
                    if quantity<=0:continue
                    day_remaining-=quantity
                    assignments.append({'worker_ref_id':worker,'quantity_minutes':str(quantity)})
                    used_workers[(worker,day)]=used_workers.get((worker,day),ZERO)+quantity
                remaining-=taken
                gross=per_worker*len(workers)
                daily.append({'planned_date':day,'gross_capacity':gross,'committed_quantity':gross-net,'available_quantity':net,'allocated_quantity':taken,'remaining_capacity':net-taken,'worker_allocations':assignments})
            minimum=max(minimum,needed or 366)
        else:deny('recipe_resource_invalid',422,'recipe_version_id')
        ok=available>=required and blocker is None
        if not ok:
            blocker=blocker or f'insufficient_{resource.resource_type}:{resource.resource_code}'
            blockers.append(blocker)
        total=money(required*cost)
        rows.append(ResourceValidationRow(resource_type=resource.resource_type,resource_ref_id=resource.resource_ref_id,resource_code=resource.resource_code,resource_name=resource.resource_name,unit=resource.unit,required_quantity=required,available_quantity=available,unit_cost=cost,total_cost=total,original_unit_cost=cost,original_total_cost=total,cost_currency=context.cost_currency,source=source,ok=ok,blocker_code=blocker,allocations=allocations,daily_allocations=daily))
    total=sum((row.original_total_cost for row in rows),ZERO)
    return ResourceValidationRead(recipe_version_id=version.id,quantity=payload.quantity,unit=payload.unit,can_release=not blockers,planned_cost=total,original_planned_cost=total,organization_context=context,cost_currency=context.cost_currency,planned_start_date=days[0],planned_end_date=days[-1],planned_duration_days=payload.planned_duration_days,minimum_duration_days=minimum,validated_at=datetime.now(timezone.utc),rows=rows,blockers=blockers)
