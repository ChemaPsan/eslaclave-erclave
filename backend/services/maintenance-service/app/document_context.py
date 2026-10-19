"""Fixed Maintenance context and RH-authoritative technician monetary evidence."""
from datetime import datetime,time,timedelta,timezone
from decimal import Decimal,ROUND_HALF_UP,localcontext
from erclave_common.operational_context import OperationalContext,society_currency
from erclave_common.organization_client import deny

def authorize_order(value,access,*,legacy=False,active=True):
    if value is None:return
    context=value.get('organization_context')
    if context:
        if access is None:deny('assignment_division_denied',403)
        OperationalContext.model_validate(context).authorize(access,active=active)
    elif access is not None:
        if not access.all_divisions:deny('assignment_division_denied',403)
        if not legacy:deny('maintenance_document_history_review_required',409)
    return context

def divisions_for(access):return None if access.all_divisions else [row['id'] for row in access.divisions]

def create_context(payload,access,machine=None,source=None):
    if source is not None:
        context=authorize_order(source,access)
        if not context:deny('maintenance_document_history_review_required',409)
        if payload.division_ref_id and payload.division_ref_id!=context['division_ref_id']:deny('operational_context_mismatch',422,'division_ref_id')
    else:
        division_id=machine.get('division_ref_id') if machine else payload.division_ref_id
        if not division_id:deny('maintenance_document_context_required',422,'division_ref_id')
        if payload.division_ref_id and payload.division_ref_id!=division_id:deny('operational_context_mismatch',422,'division_ref_id')
        division=access.division(division_id)
        context=OperationalContext(division_ref_id=division_id,society_ref_id=division['society_id'],division_code=division['code'],division_name=division['name'],cost_currency=society_currency(access,division['society_id'])).model_dump()
    if machine and machine.get('division_ref_id')!=context['division_ref_id']:deny('operational_context_mismatch',422,'production_machine_id')
    if not context.get('cost_currency'):deny('operational_cost_currency_unavailable',409)
    return context

def validate_worker(worker,context,worker_id,field='assigned_worker_id'):
    if not worker or worker.get('id')!=worker_id or worker.get('division_ref_id')!=context['division_ref_id']:
        deny('maintenance_worker_not_eligible',422,field)
    if worker.get('society_ref_id')!=context['society_ref_id'] or worker.get('hourly_cost_currency_code')!=context['cost_currency'] or not worker.get('hourly_cost_confirmed_at'):
        deny('maintenance_worker_tariff_unavailable',409,field)
    try:
        rate=Decimal(str(worker['hourly_cost']))
        capacity=worker['minutes_per_worker']
        valid=rate.is_finite() and 0<=rate<Decimal('1000000000000') and rate.as_tuple().exponent>=-6 and isinstance(capacity,int) and capacity>0
    except (KeyError,ValueError,TypeError):valid=False
    if not valid:deny('maintenance_worker_tariff_unavailable',409,field)
    return worker

def duration_seconds(start,end):
    delta=end-start
    return Decimal(delta.days*86400+delta.seconds)+Decimal(delta.microseconds)/Decimal(1000000)

def labor_snapshot(worker,context,payload):
    validate_worker(worker,context,payload.worker_id,'worker_id')
    if payload.expected_position_assignment_revision is not None and payload.expected_position_assignment_revision!=worker.get('position_assignment_revision'):
        deny('maintenance_worker_tariff_changed',409,'worker_id')
    seconds=duration_seconds(payload.started_at,payload.ended_at)
    with localcontext() as precision:
        precision.prec=50
        cost=(seconds*Decimal(str(worker['hourly_cost']))/Decimal(3600)).quantize(Decimal('.000001'),rounding=ROUND_HALF_UP)
    if cost>=Decimal('1000000000000'):deny('maintenance_time_cost_out_of_range',422,'ended_at')
    return {key:worker[key] for key in ('labor_position_id','position_name','worker_assignment_revision','position_assignment_revision','minutes_per_worker')}|{'position_code':worker.get('position_code'),'worker_id':worker['id'],'hourly_cost':str(worker['hourly_cost']),'currency':context['cost_currency'],'society_ref_id':context['society_ref_id'],'duration_seconds':str(seconds),'labor_cost':str(cost),'rounding_rule':'half_up_6','tariff_confirmed_at':worker['hourly_cost_confirmed_at']}

def day_intervals(start,end):
    start=start.astimezone(timezone.utc);end=end.astimezone(timezone.utc)
    while start<end:
        midnight=datetime.combine(start.date()+timedelta(days=1),time.min,tzinfo=timezone.utc)
        stop=min(midnight,end)
        yield start.date(),start,stop
        start=stop
