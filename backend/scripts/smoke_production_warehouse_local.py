"""HTTP smoke of warehouse issue/start using the PostgreSQL tests' isolated fixtures."""
import importlib.util
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import text

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend/shared'))
from smoke_maintenance_local import call, firebase_token, require_local, LOCAL_APIS, TENANT


def fixture_module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    line=next(line for line in (ROOT/'backend/.env').read_text(encoding='utf-8').splitlines() if line.startswith('ERCLAVE_INVENTORY_DATABASE_URL='))
    database=line.split('=',1)[1].strip();require_local(database)
    token=firebase_token();context=call(LOCAL_APIS['admin']+'/v1/session/context',token)
    assert context['tenant']['id']==TENANT
    print('Local HTTP smoke tenant '+TENANT+'; loopback:5434/erclave_local')
    os.environ['ERCLAVE_TEST_DATABASE_URL']=database
    os.environ['ERCLAVE_TEST_TENANT_ID']=TENANT
    inventory=fixture_module('smoke_inventory_fixtures','backend/services/inventory-service/tests/test_inventory_repository_integration.py')
    production=fixture_module('smoke_production_fixtures','backend/services/production-service/tests/test_production_warehouse_integration.py')
    with contextmanager(inventory.stocked_resource.__wrapped__)() as stock, contextmanager(production.material_order.__wrapped__)() as order:
        inv,t,item,warehouse,suffix,actor,prefix=stock
        repo,t,oid,actor,order_suffix=order
        try:
            workers=call(LOCAL_APIS['hr']+'/v1/hr/workers/production-eligible',token)
            assert workers,'Local requires an eligible production worker'
            with repo.engine.begin() as c:
                c.execute(text('update production.production_orders set responsible_worker_ref_id=:w where tenant_id=:t and id=:i'),{'w':workers[0]['id'],'t':t,'i':oid})
            # Fixture creation stays in the existing test builders; operational commands below use real HTTP.
            for n in range(2):
                reservation=inv.create_reservation(t,inventory.schemas.ReservationCreateRequest(inventory_item_id=item.id,warehouse_id=warehouse.id,quantity=2,unit=item.base_unit,source=inventory.schemas.SourceRef(type='production_order',id=oid,line_id=str(n))),prefix+f'-reserve{n}',f'reserve{n}',actor)
                with repo.engine.begin() as c:
                    c.execute(text('update production.production_order_resource_reservations set reservation_ref_id=:r where tenant_id=:t and production_order_resource_id=:i'),{'r':reservation.id,'t':t,'i':f'resource{n}_{order_suffix}'})
                    c.execute(text('update production.production_order_resources set unit=:u where tenant_id=:t and id=:i'),{'u':item.base_unit,'t':t,'i':f'resource{n}_{order_suffix}'})
            url=LOCAL_APIS['production']+f'/v1/production/orders/{oid}'
            try:call(url+'/status',token,'PATCH',{'status':'in_progress','reason':'Inicio antes de salida'},prefix+'-blocked')
            except RuntimeError as exc:assert 'material_consumption_required' in str(exc)
            else:raise AssertionError('Order started before warehouse issue')
            assert any(row['id']==oid for row in call(LOCAL_APIS['production']+'/v1/production/warehouse-material-requests?limit=100',token))
            result=call(url+'/issue-materials',token,'POST',{},prefix+'-issue')
            assert result['status']=='issued',result
            assert call(url,token)['status']=='released'
            assert call(url+'/issue-materials',token,'POST',{},prefix+'-issue-again')['status']=='issued'
            started=call(url+'/status',token,'PATCH',{'status':'in_progress','reason':'Materiales entregados'},prefix+'-start')
            assert started['status']=='in_progress' and started['actual_cost']==40
            with inv.engine.connect() as c:
                count,quantity=c.execute(text("select count(*),sum(quantity) from inventory.movements where tenant_id=:t and inventory_item_id=:i and movement_type='exit'"),{'t':t,'i':item.id}).one()
                assert count==2 and quantity==4
            print('PASS: blocked start, queue, HTTP issue, replay, unchanged released status, start, actual cost, two unique exits / four units.')
            call(url+'/status',token,'PATCH',{'status':'cancelled','reason':'Prueba de devolución de sobrante'},prefix+'-cancel')
            with inv.engine.connect() as c:
                original=c.execute(text("select id from inventory.movements where tenant_id=:t and inventory_item_id=:i and source_type='reservation' order by id limit 1"),{'t':t,'i':item.id}).scalar_one()
            returns_url=LOCAL_APIS['inventory']+'/v1/inventory/material-returns'
            requested=call(returns_url,token,'POST',{'original_movement_id':original,'quantity':1,'reason':'Sobrante confirmado en prueba Local'},prefix+'-return-request')
            assert requested['status']=='pending'
            received=call(returns_url+'/'+requested['id']+'/receive',token,'POST',{},prefix+'-return-receive')
            assert received['status']=='completed',received
            replay=call(returns_url+'/'+requested['id']+'/receive',token,'POST',{},prefix+'-return-retry')
            assert replay['movement_id']==received['movement_id']
            returned_order=call(url,token)
            assert returned_order['actual_cost']==30 and len(returned_order['material_returns'])==1
            print('PASS: real Inventory -> Production validation and reconciliation, one returned entry and net order cost 30.')
        finally:
            # Remove only identifiers owned by this invocation, including the HTTP actor's audit rows.
            with repo.engine.begin() as c:
                c.execute(text('delete from production.audit_events where tenant_id=:t and resource_id=:i'),{'t':t,'i':oid})
                c.execute(text('delete from production.idempotency_records where tenant_id=:t and idempotency_key like :p'),{'t':t,'p':prefix+'%'})
            with inv.engine.begin() as c:
                c.execute(text('delete from inventory.audit_events where tenant_id=:t and entity_id in (select id from inventory.material_returns where tenant_id=:t and source_id=:o)'),{'t':t,'o':oid})
                c.execute(text('delete from inventory.audit_events where tenant_id=:t and entity_id in (select id from inventory.reservations where tenant_id=:t and inventory_item_id=:i)'),{'t':t,'i':item.id})
                c.execute(text('delete from inventory.idempotency_records where tenant_id=:t and idempotency_key like :p'),{'t':t,'p':f'production-order-{oid}%'})


if __name__=='__main__':main()
