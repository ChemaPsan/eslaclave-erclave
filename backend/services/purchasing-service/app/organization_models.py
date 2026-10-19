from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime, UniqueConstraint, ForeignKeyConstraint, CheckConstraint, Index, text
metadata=MetaData(schema='purchasing')
from sqlalchemy.dialects.postgresql import JSONB
document_tables = {}
for document in ('requisitions', 'purchase_orders', 'purchase_receipts'):
    columns = [Column('id',String(40),primary_key=True),Column('tenant_id',String(40),nullable=False),
               Column('organization_context',JSONB(),nullable=True),
               CheckConstraint("organization_context is null or jsonb_typeof(organization_context)='object'",name=f'ck_cc15_{document}_organization_context'),
               Index(f'ix_cc15_{document}_division','tenant_id',text("(organization_context->>'division_ref_id')"))]
    if document == 'purchase_orders':
        columns.extend([Column('commercial_terms_snapshot',JSONB(),nullable=True),
                        CheckConstraint("commercial_terms_snapshot is null or jsonb_typeof(commercial_terms_snapshot)='object'",name='ck_cc15_purchase_orders_commercial_terms_snapshot')])
    document_tables[document] = Table(document,metadata,*columns)
receipt_line_context=Table('purchase_receipt_lines',metadata,Column('id',String(40),primary_key=True),Column('tenant_id',String(40),nullable=False),Column('inventory_context_snapshot',JSONB(),nullable=True))
resources=Table('suppliers',metadata,Column('id',String(40),primary_key=True),Column('tenant_id',String(40),nullable=False),UniqueConstraint('tenant_id','id',name='uq_purchasing_supplier_tenant_id'))
assignments=Table('supplier_division_assignments',metadata,Column('tenant_id',String(40),primary_key=True),Column('supplier_id',String(40),primary_key=True),Column('division_ref_id',String(40),primary_key=True),Column('society_ref_id',String(40),nullable=False),Column('status',String(16),nullable=False),Column('revision',Integer(),nullable=False),Column('created_at',DateTime(timezone=True),nullable=False,server_default=text('now()')),Column('updated_at',DateTime(timezone=True),nullable=False,server_default=text('now()')),ForeignKeyConstraint(['tenant_id','supplier_id'],['purchasing.suppliers.tenant_id','purchasing.suppliers.id'],name='fk_purchasing_supplier_assignment',ondelete='RESTRICT'),CheckConstraint("status in ('active','inactive') and revision>0",name='ck_purchasing_supplier_assignment'),Index('ix_purchasing_supplier_assignment_division','tenant_id','division_ref_id','status'))

import sqlalchemy as sa
commercial_terms=sa.Table('supplier_division_terms',metadata,sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('supplier_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),sa.Column('society_ref_id',sa.String(40),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('currency',sa.String(12),nullable=False),sa.Column('payment_terms',sa.String(40),nullable=False),sa.Column('lead_time_days',sa.Integer(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.ForeignKeyConstraint(['tenant_id','supplier_id','division_ref_id'],['purchasing.supplier_division_assignments.tenant_id','purchasing.supplier_division_assignments.supplier_id','purchasing.supplier_division_assignments.division_ref_id'],name='fk_purchasing_supplier_terms',ondelete='RESTRICT'),sa.CheckConstraint("revision > 0 and currency ~ '^[A-Z0-9._-]{3,12}$' and payment_terms ~ '^[a-z0-9._-]{1,40}$' and lead_time_days between 0 and 3650",name='ck_purchasing_supplier_terms'),sa.Index('ix_purchasing_supplier_terms_division','tenant_id','division_ref_id'))
