"""Production-owned dimension assignments; external IDs have no cross-schema FKs."""
from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime, Numeric, CheckConstraint, UniqueConstraint, ForeignKeyConstraint, Index, text
from sqlalchemy.dialects.postgresql import JSONB
metadata = MetaData(schema='production')
product_services = Table('product_services', metadata, Column('tenant_id', String(40), nullable=False), Column('id', String(40), primary_key=True), UniqueConstraint('tenant_id', 'id', name='uq_production_product_services_tenant_id'))
machines = Table('machines', metadata, Column('id', String(40), primary_key=True), Column('tenant_id', String(40), nullable=False), Column('division_ref_id', String(40)), Column('cost_currency', String(3)), Column('cost_society_ref_id', String(40)), Column('cost_confirmed_at', DateTime(timezone=True)), Column('division_revision', Integer, nullable=False, server_default='0'), CheckConstraint('(division_ref_id is null and division_revision=0) or (division_ref_id is not null and division_revision>0)', name='ck_production_machine_division'), Index('ix_production_machine_division', 'tenant_id', 'division_ref_id'))
assignments = Table('product_service_division_assignments', metadata, Column('tenant_id', String(40), primary_key=True), Column('product_service_id', String(40), primary_key=True), Column('division_ref_id', String(40), primary_key=True), Column('cost_center_ref_id', String(40)), Column('cost_center_snapshot', JSONB), Column('status', String(16), nullable=False), Column('revision', Integer, nullable=False), Column('estimated_unit_cost', Numeric(18,6)), Column('cost_currency', String(3)), Column('cost_society_ref_id', String(40)), Column('cost_confirmed_at', DateTime(timezone=True)), Column('created_at', DateTime(timezone=True), nullable=False, server_default=text('now()')), Column('updated_at', DateTime(timezone=True), nullable=False, server_default=text('now()')), ForeignKeyConstraint(['tenant_id', 'product_service_id'], ['production.product_services.tenant_id', 'production.product_services.id'], name='fk_production_assignment_product_service', ondelete='RESTRICT'), CheckConstraint("status in ('active','inactive') and revision>0", name='ck_production_assignment_state'), CheckConstraint("(estimated_unit_cost is null and cost_currency is null and cost_society_ref_id is null and cost_confirmed_at is null) or (estimated_unit_cost is not null and estimated_unit_cost >= 0 and estimated_unit_cost != 'NaN'::numeric and cost_currency ~ '^[A-Z]{3}$' and length(cost_society_ref_id)>0 and cost_confirmed_at is not null)", name='ck_cc21_product_assignment_estimated_cost'), Index('ix_production_assignment_division', 'tenant_id', 'division_ref_id', 'status'))

production_orders = Table('production_orders', metadata, Column('tenant_id', String(40), nullable=False), Column('id', String(40), primary_key=True), Column('organization_context', JSONB), Index('ix_production_orders_division','tenant_id',text("(organization_context->>'division_ref_id')")))
sales_order_requests = Table('sales_order_requests', metadata, Column('tenant_id', String(40), nullable=False), Column('id', String(40), primary_key=True), Column('organization_context', JSONB), Index('ix_sales_order_requests_division','tenant_id',text("(organization_context->>'division_ref_id')")))
order_creation_contexts = Table('order_creation_contexts',metadata,Column('tenant_id',String(40),primary_key=True),Column('order_id',String(40),primary_key=True),Column('actor_id',String(128),nullable=False),Column('request_hash',String(64),nullable=False),Column('organization_context',JSONB,nullable=False),Column('allocations',JSONB,nullable=False),Column('created_at',DateTime(timezone=True),nullable=False,server_default=text('now()')),CheckConstraint("jsonb_typeof(allocations)='array'",name='ck_creation_allocations'))

_context_check = "organization_context is null or (jsonb_typeof(organization_context)='object' and organization_context ?& array['division_ref_id','society_ref_id','division_code','division_name','cost_currency'] and length(organization_context->>'division_ref_id')>0 and length(organization_context->>'society_ref_id')>0 and (organization_context->>'cost_currency') ~ '^[A-Z]{3}$') is true"
for table in (production_orders,sales_order_requests):
    table.append_constraint(CheckConstraint(_context_check,name='ck_'+table.name+'_context'))
order_creation_contexts.append_constraint(CheckConstraint(_context_check,name='ck_creation_context'))

machines.append_constraint(CheckConstraint("(cost_currency is null and cost_society_ref_id is null and cost_confirmed_at is null) or (cost_currency is not null and cost_currency ~ '^[A-Z]{3}$' and cost_society_ref_id is not null and length(cost_society_ref_id)>0 and cost_confirmed_at is not null and division_ref_id is not null)", name="ck_production_machine_cost_currency"))

from sqlalchemy import Date, Numeric
production_orders.append_constraint(UniqueConstraint('tenant_id','id',name='uq_production_orders_tenant_id'))
labor_worker_commitments=Table('labor_worker_commitments',metadata,
    Column('id',String(40),primary_key=True),Column('tenant_id',String(40),nullable=False),Column('production_order_id',String(40),nullable=False),
    Column('labor_position_ref_id',String(40),nullable=False),Column('worker_ref_id',String(40),nullable=False),Column('planned_date',Date,nullable=False),
    Column('quantity_minutes',Numeric(18,6),nullable=False),Column('status',String(16),nullable=False,server_default='active'),
    Column('created_at',DateTime(timezone=True),nullable=False,server_default=text('now()')),Column('updated_at',DateTime(timezone=True),nullable=False,server_default=text('now()')),
    ForeignKeyConstraint(['tenant_id','production_order_id'],['production.production_orders.tenant_id','production.production_orders.id'],name='fk_labor_worker_commitment_order',ondelete='RESTRICT'),
    CheckConstraint("quantity_minutes>0 and quantity_minutes != 'NaN'::numeric",name='ck_labor_worker_commitment_minutes'),CheckConstraint("status in ('active','completed','released')",name='ck_labor_worker_commitment_status'),
    UniqueConstraint('tenant_id','production_order_id','labor_position_ref_id','worker_ref_id','planned_date',name='uq_labor_worker_commitment_allocation'),
    Index('ix_labor_worker_commitment_worker_day','tenant_id','worker_ref_id','planned_date','status'),Index('ix_labor_worker_commitment_order','tenant_id','production_order_id'))

# Sales IDs are references only; the linked Production order has a tenant-safe local FK.
sales_order_requests.append_column(Column('production_order_ref_id',String(40)))
sales_order_requests.append_column(Column('creation_attempt_ref_id',String(40)))
sales_order_requests.append_column(Column('source_snapshot',JSONB))
sales_order_requests.append_constraint(UniqueConstraint('tenant_id','production_order_ref_id',name='uq_sales_request_production_order'))
sales_order_requests.append_constraint(ForeignKeyConstraint(['tenant_id','production_order_ref_id'],['production.production_orders.tenant_id','production.production_orders.id'],name='fk_sales_request_production_order',ondelete='RESTRICT'))
sales_order_requests.append_constraint(CheckConstraint("source_snapshot is null or jsonb_typeof(source_snapshot)='object'",name='ck_sales_request_source_snapshot'))
