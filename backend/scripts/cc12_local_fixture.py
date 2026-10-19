"""Owned Local demo fixtures for real HTTP CC-12 acceptance; never tenant inference."""
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import json,sys
from dotenv import dotenv_values
from sqlalchemy import MetaData,Table,create_engine,select,or_,text
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend/shared'))
from organization_backfill_local import local_database_url,LOCAL_TENANT
from smoke_maintenance_local import firebase_token,call,LOCAL_APIS

class CC12Fixture:
    def __init__(self):
        self.prefix='cc12_'+uuid4().hex[:10]
        self.ids={};self.metadata=MetaData();self.tables={};self.owned=set();self.seeded=[]
        url=local_database_url(dotenv_values(ROOT/'backend/.env').get('ERCLAVE_INVENTORY_DATABASE_URL',''),'local',LOCAL_TENANT)
        self.engine=create_engine(url)
        with self.engine.connect() as c:
            assert c.execute(text('select id from admin.tenants')).scalars().all()==[LOCAL_TENANT]
            assert c.execute(text('select version_num from alembic_version')).scalar()=='20261008_0056'
        self.token=firebase_token();session=call(LOCAL_APIS['admin']+'/v1/session/context',self.token)
        assert session['tenant']['id']==LOCAL_TENANT and session['scope']['all_divisions']
        assert not session['capabilities']['accounting']['available']
        self.actor=session['user']['id'];self.manifest=ROOT/'.local'/('cc12-fixture-'+self.prefix+'.json')
    def table(self,name):
        if name not in self.tables:
            schema,table=name.split('.')
            self.tables[name]=Table(table,self.metadata,schema=schema,autoload_with=self.engine)
        return self.tables[name]
    def identity(self,name):
        value=self.prefix+'_'+name;assert len(value)<=40
        self.ids[name]=value;self.owned.add(value);return value
    def insert(self,c,table,**values):
        target=self.table(table)
        c.execute(target.insert().values(tenant_id=LOCAL_TENANT,**values))
        self.seeded.append((table,{key.name:values.get(key.name,LOCAL_TENANT if key.name=='tenant_id' else None) for key in target.primary_key}))
    def seed(self):
        for name in ['issuer','society','division','warehouse','material','finished','area','position','worker','machine','product','recipe','version','stage','customer','quote','quote_line','order','line']:
            self.identity(name)
        x=self.ids;now=datetime.now(timezone.utc)
        self.context={'division_ref_id':x['division'],'society_ref_id':x['society'],'division_code':x['division'],'division_name':'CC12 synthetic division','cost_currency':'MXN'}
        self.manifest.write_text(json.dumps({'tenant':LOCAL_TENANT,'prefix':self.prefix,'ids':x,'cleanup':'pending'},indent=2),encoding='utf-8')
        with self.engine.begin() as c:
            self.insert(c,'admin.fiscal_issuers',id=x['issuer'],code=x['issuer'],legal_name='CC12 synthetic issuer')
            self.insert(c,'admin.societies',id=x['society'],code=x['society'],name='CC12 synthetic Society',issuer_id=x['issuer'],base_currency='MXN')
            self.insert(c,'admin.divisions',id=x['division'],code=x['division'],name='CC12 synthetic division',society_id=x['society'])
            self.insert(c,'hr.labor_areas',id=x['area'],code=x['area'],name='CC12 synthetic area')
            self.insert(c,'hr.labor_roles',id=x['position'],labor_area_id=x['area'],position='CC12 '+self.prefix,recipe_name=self.prefix,resource_quantity=1,minutes_per_resource=480,hourly_cost=60,intervenes_in_production=True)
            self.insert(c,'hr.workers',id=x['worker'],employee_number=x['worker'],first_names='Synthetic',first_last_name='CC12',curp='ZZZZ010101HDFXXX'+str(int(self.prefix[-8:],16)%100).zfill(2),rfc='ZZZZ010101'+self.prefix[-3:].upper(),nss=str(int(self.prefix[-10:],16)%100000000000).zfill(11),hire_date=date.today(),labor_position_id=x['position'])
            self.insert(c,'hr.position_division_assignments',position_id=x['position'],division_ref_id=x['division'],status='active',revision=1,hourly_cost=60,hourly_cost_currency_code='MXN',hourly_cost_society_ref_id=x['society'],hourly_cost_confirmed_at=now)
            self.insert(c,'hr.worker_division_assignments',worker_id=x['worker'],division_ref_id=x['division'],labor_position_id=x['position'],status='active',revision=1)
            self.insert(c,'inventory.warehouses',id=x['warehouse'],code=x['warehouse'],name='CC12 synthetic warehouse',type='general',business_center='CC12',location='Local fixture',owner='Synthetic',division_ref_id=x['division'],division_revision=1)
            for name,kind in [('material','rawMaterial'),('finished','finishedGood')]:
                self.insert(c,'inventory.items',id=x[name],code=x[name],name='CC12 synthetic '+name,type=kind,base_unit='H87',use_in_recipe=name=='material',default_unit_cost=Decimal('5') if name=='material' else 0)
                self.insert(c,'inventory.item_division_assignments',item_id=x[name],division_ref_id=x['division'],status='active',revision=1)
            self.insert(c,'inventory.movements',id=self.identity('opening'),movement_code=self.prefix+'-OPEN',movement_type='entry',inventory_item_id=x['material'],warehouse_id=x['warehouse'],direction='in',quantity=10,unit='H87',unit_cost=5,reason='CC12 synthetic opening stock',source_type='manual',source_id=self.prefix,actor_id=self.actor,occurred_at=now,organization_context=self.context)
            self.insert(c,'production.machines',id=x['machine'],code=x['machine'],name='CC12 synthetic machine',machine_type='general',available_minutes_per_day=480,cost_per_minute=2,division_ref_id=x['division'],division_revision=1,cost_currency='MXN',cost_society_ref_id=x['society'],cost_confirmed_at=now)
            self.insert(c,'production.product_services',id=x['product'],code=x['product'],name='CC12 synthetic finished product',type='product',base_unit='H87',inventory_item_ref_id=x['finished'])
            self.insert(c,'production.product_service_division_assignments',product_service_id=x['product'],division_ref_id=x['division'],status='active',revision=1)
            self.insert(c,'production.recipes',id=x['recipe'],product_service_id=x['product'],code=x['recipe'],name='CC12 synthetic recipe')
            self.insert(c,'production.recipe_versions',id=x['version'],recipe_id=x['recipe'],version_number=1,status='approved',base_quantity=1,base_unit='H87',approved_at=now,approved_by=self.actor)
            c.execute(self.table('production.recipes').update().where(self.table('production.recipes').c.tenant_id==LOCAL_TENANT,self.table('production.recipes').c.id==x['recipe']).values(current_version_id=x['version'],status='active'))
            c.execute(self.table('production.product_services').update().where(self.table('production.product_services').c.id==x['product'],self.table('production.product_services').c.tenant_id==LOCAL_TENANT).values(current_recipe_version_id=x['version']))
            for kind,resource,quantity,unit in [('material','material',2,'H87'),('labor','position',10,'MIN'),('machine','machine',5,'MIN')]:
                self.insert(c,'production.recipe_resources',id=self.identity('resource_'+kind),recipe_version_id=x['version'],resource_type=kind,resource_ref_id=x[resource],resource_code=x[resource],resource_name='CC12 '+kind,quantity=quantity,unit=unit,sort_order=len(self.owned))
            self.insert(c,'production.recipe_stages',id=x['stage'],recipe_version_id=x['version'],name='CC12 synthetic stage',sort_order=1,weight_percent=100,status='active')
            self.insert(c,'sales.customers',id=x['customer'],code=x['customer'],commercial_name='CC12 synthetic customer',customer_type='company',status='active',responsible_worker_ref_id=x['worker'],responsible_worker_name='Synthetic CC12',payment_terms='cash',currency='USD')
            self.insert(c,'sales.customer_division_assignments',customer_id=x['customer'],division_ref_id=x['division'],society_ref_id=x['society'],status='active',revision=1)
            snapshot={'division':{'id':x['division'],'code':x['division'],'name':'CC12 synthetic division','society_id':x['society']},'division_id':x['division'],'society_id':x['society'],'values':{'currency':'USD','payment_terms':'cash','credit_limit':'0.00'},'revision':1}
            common=dict(customer_id=x['customer'],customer_code_snapshot=x['customer'],customer_name_snapshot='CC12 synthetic customer',responsible_worker_ref_id=x['worker'],responsible_worker_name='Synthetic CC12',currency='USD',payment_terms='cash',subtotal=200,discount_total=0,total=200,division_ref_id=x['division'],society_ref_id=x['society'],commercial_terms_snapshot=snapshot)
            self.insert(c,'sales.quotes',id=x['quote'],code=x['quote'],status='approved',valid_until=date.today(),organization_revision=1,**common)
            line=dict(line_number=1,product_service_ref_id=x['product'],product_service_code=x['product'],product_service_name='CC12 synthetic finished product',product_service_type='product',unit='H87',unit_price=100,discount_percentage=0,total=200)
            self.insert(c,'sales.quote_lines',id=x['quote_line'],quote_id=x['quote'],quantity=2,subtotal=200,discount_amount=0,**line)
            self.insert(c,'sales.orders',id=x['order'],code=x['order'],quote_id=x['quote'],quote_code_snapshot=x['quote'],quote_organization_revision=1,**common)
            self.insert(c,'sales.order_lines',id=x['line'],order_id=x['order'],quote_line_id=x['quote_line'],ordered_quantity=2,fulfillment_mode='pending',fulfillment_status='pending',**line)
        print('Fixture committed only to Local demo; unique namespace '+self.prefix)

    def cleanup(self):
        """Exact owned roots and dependent effects; no schema-wide/tenant-wide deletion."""
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy import inspect
        allowed={
          'production':['failed_order_creations','sales_order_requests','production_orders','production_order_resources','production_order_stages','production_order_resource_reservations','capacity_commitments','labor_worker_commitments','order_creation_contexts','material_issues','material_issue_lines','material_returns','audit_events','idempotency_records'],
          'inventory':['reservation_source_rollbacks','finished_goods_receipts','reservations','movements','audit_events','idempotency_records'],
          'sales':['production_reconciliations','order_line_reservations','order_line_allocations','deliveries','delivery_lines','delivery_line_allocations','audit_events','idempotency_records']}
        references={'id','order_id','order_line_id','sales_order_id','sales_order_line_id','production_order_id','production_order_ref_id','production_order_resource_id','production_order_stage_id','reservation_id','reservation_ref_id','source_id','source_line_id','entity_id','resource_id','request_id','creation_attempt_ref_id','inventory_item_id','delivery_id','delivery_line_id'}
        inspector=inspect(self.engine);operations=[]
        for schema,names in allowed.items():
            present=set(inspector.get_table_names(schema=schema))
            for name in names:
                if name in present:operations.append(self.table(schema+'.'+name))
        with self.engine.begin() as c:
            for _ in range(8):
                prior=len(self.owned)
                for table in operations:
                    columns=[column for column in table.c if column.name in references]
                    if not columns:continue
                    rows=c.execute(select(table).where(table.c.tenant_id==LOCAL_TENANT,or_(*(col.in_(list(self.owned)) for col in columns)))).mappings().all()
                    for row in rows:
                        if row.get('id'):self.owned.add(row['id'])
                        if table.name=='sales_order_requests':
                            for key in ('production_order_ref_id','creation_attempt_ref_id'):
                                if row.get(key):self.owned.add(row[key])
                if prior==len(self.owned):break
            targets=[]
            for table in operations:
                predicates=[col.in_(list(self.owned)) for col in table.c if col.name in references]
                if 'idempotency_key' in table.c:
                    predicates+=[table.c.idempotency_key.startswith(self.prefix,autoescape=True)]
                    predicates+=[table.c.idempotency_key.contains(value,autoescape=True) for value in self.owned if len(value)>15]
                if predicates:targets.append((table,or_(*predicates)))
            # Break only the nullable links of the fixture's own recipe/request.
            product=self.table('production.product_services')
            c.execute(product.update().where(product.c.tenant_id==LOCAL_TENANT,product.c.id==self.ids['product']).values(current_recipe_version_id=None))
            recipes=self.table('production.recipes')
            c.execute(recipes.update().where(recipes.c.tenant_id==LOCAL_TENANT,recipes.c.id==self.ids['recipe']).values(current_version_id=None))
            requests=self.table('production.sales_order_requests')
            if 'production_order_ref_id' in requests.c:
                c.execute(requests.update().where(requests.c.tenant_id==LOCAL_TENANT,requests.c.sales_order_id==self.ids['order']).values(production_order_ref_id=None))
            for table,keys in reversed(self.seeded):
                target=self.table(table)
                targets.append((target, __import__('sqlalchemy').and_(*(target.c[key]==value for key,value in keys.items()))))
            pending=targets
            for _ in range(12):
                remaining=[]
                for table,predicate in pending:
                    try:
                        with c.begin_nested():c.execute(table.delete().where(table.c.tenant_id==LOCAL_TENANT,predicate))
                    except IntegrityError:remaining.append((table,predicate))
                if not remaining:break
                if len(remaining)==len(pending):raise RuntimeError('Owned fixture cleanup blocked by references: '+','.join(t.fullname for t,p in remaining))
                pending=remaining
            else:raise RuntimeError('Owned fixture cleanup did not finish')
            for table,predicate in targets:
                assert c.execute(select(__import__('sqlalchemy').func.count()).select_from(table).where(table.c.tenant_id==LOCAL_TENANT,predicate)).scalar()==0,table.fullname
        self.manifest.write_text(json.dumps({'tenant':LOCAL_TENANT,'prefix':self.prefix,'ids':self.ids,'cleanup':'verified','owned_count':len(self.owned)},indent=2),encoding='utf-8')
        print('Cleanup verified: only fixture-owned records removed; existing records preserved')
        self.engine.dispose()

@contextmanager
def cc12_fixture():
    fixture=CC12Fixture()
    try:
        fixture.seed()
        yield fixture
    finally:fixture.cleanup()
