import importlib
import os
import sys
from pathlib import Path
from uuid import uuid4
from decimal import Decimal
import pytest
from sqlalchemy import text

DATABASE_URL=os.getenv('ERCLAVE_TEST_DATABASE_URL')
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason='Local PostgreSQL required')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
repositories=importlib.import_module('app.repositories')
schemas=importlib.import_module('app.schemas')
reports=importlib.import_module('app.reports')

def test_maintenance_return_requires_terminal_request_and_reconciles_after_concurrent_reopen():
    t=os.getenv('ERCLAVE_TEST_TENANT_ID','ten_739ee59d765d5e14818674800d')
    assert t=='ten_739ee59d765d5e14818674800d'
    repo=repositories.MaintenanceRepository(DATABASE_URL)
    suffix=uuid4().hex[:12];actor='usr_ret_'+suffix;key='ret-'+suffix;order=None
    try:
        order=repo.create_order(t,schemas.OrderCreate(code='MT-RET-'+suffix,target_type='facility',priority='high',title='Equipo de prueba',description='Validación de devolución',location='Local'),{'machine_code_snapshot':None,'machine_name_snapshot':None,'source_production_order_code_snapshot':None},key+'-create','create',actor)
        for action in ['request','assign']:
            worker={'id':'hrw_'+suffix,'full_name':'Técnico de prueba'} if action=='assign' else None
            repo.transition(t,order['id'],schemas.TransitionRequest(transition=action,assigned_worker_id=worker['id'] if worker else None),worker,key+'-'+action,action,actor)
        request,_=repo.prepare_material_request(t,order['id'],schemas.MaterialRequestCreate(warehouse_id='wh_'+suffix,lines=[schemas.MaterialLine(item_id='itm_'+suffix,quantity=4,unit_code='PZA')]),{'warehouse_name':'Refacciones','items':[{'code':'REF-01','name':'Refacción'}]},key+'-request-parts','parts',actor)
        repo.complete_material_request(t,request['id'],key+'-request-parts',[{'id':'res_'+suffix,'unit_cost_snapshot':Decimal('10')}])
        _,plan=repo.prepare_warehouse_issue(t,request['id'],actor)
        repo.complete_warehouse_issue(t,request['id'],[(plan[0]['id'],{'id':'mov_'+suffix})],None,actor)
        payload={'source_id':order['id'],'reservation_id':'res_'+suffix,'original_movement_id':'mov_'+suffix,'quantity':2}
        with pytest.raises(ValueError,match='material_return_terminal_order_required'):repo.validate_material_return(t,payload)
        with repo.engine.begin() as c:c.execute(text("update maintenance.orders set status='resolved' where tenant_id=:t and id=:id"),{'t':t,'id':order['id']})
        assert repo.validate_material_return(t,payload)['source_code']==order['code']
        with pytest.raises(ValueError,match='material_return_source_invalid'):repo.validate_material_return('other-tenant',payload)
        with repo.engine.begin() as c:c.execute(text("update maintenance.orders set status='in_progress' where tenant_id=:t and id=:id"),{'t':t,'id':order['id']})
        confirmed={**payload,'id':'mrt_'+suffix,'source_type':'maintenance_order','status':'received_pending_reconciliation','movement_id':'retmov_'+suffix,'unit_cost':10}
        assert repo.reconcile_material_return(t,confirmed,actor)['status']=='completed'
        assert repo.reconcile_material_return(t,confirmed,actor)['status']=='completed'
        actual=repo.get_order(t,order['id'])
        assert len(actual['material_returns'])==1
        assert actual['material_requests'][0]['lines'][0]['quantity']==4
        with repo.engine.connect() as c:
            assert c.execute(text('select sum(quantity*unit_cost) from maintenance.material_return_adjustments where tenant_id=:t and order_id=:id'),{'t':t,'id':order['id']}).scalar_one()==20
    finally:
        with repo.engine.begin() as c:
            if order:
                values={'t':t,'id':order['id']}
                c.execute(text('delete from maintenance.material_return_adjustments where tenant_id=:t and order_id=:id'),values)
                c.execute(text('delete from maintenance.material_request_lines where tenant_id=:t and material_request_id in (select id from maintenance.material_requests where tenant_id=:t and order_id=:id)'),values)
                for table in ['material_requests','time_entries','assignments']:c.execute(text(f'delete from maintenance.{table} where tenant_id=:t and order_id=:id'),values)
                c.execute(text('delete from maintenance.orders where tenant_id=:t and id=:id'),values)
            c.execute(text('delete from maintenance.audit_events where tenant_id=:t and actor_id=:a'),{'t':t,'a':actor})
            c.execute(text('delete from maintenance.idempotency_records where tenant_id=:t and idempotency_key like :k'),{'t':t,'k':key+'%'})
        repo.engine.dispose()
