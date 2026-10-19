"""Maintenance's durable material intent; Inventory remains movement authority."""
from sqlalchemy import text
from erclave_common.config import get_settings
from erclave_common.operational_context import OperationalContext, society_currency
from erclave_common.organization_client import OrganizationClient, resolve_organization_access, deny


PROOF_PERMISSIONS = ('maintenance.material_request.create', 'maintenance.material_request.reconcile', 'maintenance.material_request.cancel', 'maintenance.order.cancel', 'inventory.movement.create')


def organization_access(tenant, authorization, permission, actor=None):
    client = OrganizationClient(get_settings())
    return resolve_organization_access(client.session(tenant, authorization, actor), tenant, 'maintenance', permission, authorization)


def guard_material(value, tenant, authorization, permission, actor=None, active=True):
    context = value.get('organization_context') if value else None
    access=organization_access(tenant, authorization, permission, actor)
    if context:
        OperationalContext.model_validate(context).authorize(access, active=active)
    elif value and not access.all_divisions:deny('assignment_division_denied',403)
    return context


def material_context(warehouse, order, authority, tenant, authorization, actor):
    division = warehouse.get('division_ref_id')
    if order.get('organization_context'):
        context=OperationalContext.model_validate(order['organization_context'])
        access=authority.organization_access(tenant,'maintenance.material_request.create',authorization,actor)
        context.authorize(access)
        if division!=context.division_ref_id:deny('operational_context_mismatch',422,'warehouse_id')
        if not context.cost_currency:deny('operational_cost_currency_unavailable',409)
        return context.model_dump()
    source_context = None
    machine_division = None
    if order.get('source_production_order_id'):
        source = authority.production_order(tenant, order['source_production_order_id'], authorization)
        source_context = source.get('organization_context')
    if order.get('production_machine_id'):
        machine_division = authority.machine(tenant, order['production_machine_id'], authorization).get('division_ref_id')
    if (source_context and source_context['division_ref_id'] != division) or (machine_division and machine_division != division):
        deny('operational_context_mismatch', 409)
    if not division:
        return None
    access = organization_access(tenant, authorization, 'maintenance.material_request.create', actor)
    row = access.division(division)
    if source_context:
        context = OperationalContext.model_validate(source_context).authorize(access)
        if not context.cost_currency:
            deny('operational_cost_currency_unavailable', 409)
        return context.model_dump()
    return OperationalContext(division_ref_id=division, society_ref_id=row['society_id'], division_code=row['code'], division_name=row['name'], cost_currency=society_currency(access, row['society_id'])).model_dump()


class MaintenanceInventoryContext:
    def has_scoped_material_requests(self, tenant):
        with self.engine.connect() as connection:
            return bool(connection.execute(text('select 1 from maintenance.material_requests where tenant_id=:tenant and organization_context is not null limit 1'), {'tenant': tenant}).first())

    def inventory_context(self, tenant, order_id, line_id):
        with self.engine.connect() as connection:
            row = connection.execute(text('''select r.id request_id,r.order_id,r.organization_context,
                r.warehouse_ref_id warehouse_id,r.status request_status,r.pending_operation,
                o.status order_status,l.id line_id,l.inventory_item_ref_id inventory_item_id,
                l.quantity,l.unit_code unit,l.line_status,l.reservation_ref_id reservation_id,
                l.inventory_movement_ref_id movement_id,l.unit_cost_snapshot
                from maintenance.material_requests r
                join maintenance.material_request_lines l on l.tenant_id=r.tenant_id and l.material_request_id=r.id
                join maintenance.orders o on o.tenant_id=r.tenant_id and o.id=r.order_id
                where r.tenant_id=:tenant and r.order_id=:order and l.id=:line'''),
                {'tenant': tenant, 'order': order_id, 'line': line_id}).mappings().first()
        if row is None:
            deny('maintenance_material_source_invalid', 404)
        value = dict(row)
        if value['line_status'] not in {'pending', 'failed', 'reserved', 'issued', 'released'}:
            deny('maintenance_material_source_invalid', 409)
        value['source'] = {'type': 'maintenance_order', 'id': order_id, 'line_id': line_id}
        return value


def material_divisions(repository, tenant, authorization, permission, actor=None):
    access = organization_access(tenant, authorization, permission, actor)
    return None if access.all_divisions else [row['id'] for row in access.divisions]
