from copy import deepcopy
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from costing_app.main import app
from costing_app.authority import resolve_access, get_admin_client, AdminClient
from costing_app.repository import get_repository
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError
TENANT='ten_739ee59d765d5e14818674800d'
PERMISSIONS=['costing.cost_center.'+a for a in ('read','create','update','status')]
def context():
    return {'tenant':{'id':TENANT,'status':'active'},'user':{'id':'actor','status':'active'},'active_modules':['admin'],
        'permissions':PERMISSIONS.copy(),'capabilities':{'cost_center_catalog':{'available':True}},
        'scope':{'version':2,'division_ids':['division'],'divisions':[{'id':'division'}],'all_divisions':False}}

@pytest.mark.parametrize('field,value,code',[
 ('tenant',{'id':'foreign','status':'active'},'tenant_access_denied'),('user',{'id':'actor','status':'inactive'},'tenant_access_denied'),
 ('permissions',[],'permission_denied'),('active_modules',['costing','accounting'],'module_not_enabled'),
 ('capabilities',{'cost_center_catalog':{'available':False}},'module_not_enabled'),('scope',{'version':1},'organization_scope_review_required'),
 ('scope',[],'cost_center_authority_unavailable'),('tenant','bad','cost_center_authority_unavailable'),('capabilities',{'cost_center_catalog':True},'cost_center_authority_unavailable')])
def test_authority_fails_closed(field,value,code):
    data=context();data[field]=value
    with pytest.raises(ErclaveError) as exc:resolve_access(data,TENANT,PERMISSIONS[0])
    assert exc.value.code==code

def test_division_scope_and_active_eligibility():
    data=context();access=resolve_access(data,TENANT,PERMISSIONS[0]);access.require_division('division',active=True)
    with pytest.raises(ErclaveError):access.require_division('foreign')
    data['scope']['all_divisions']=True;access=resolve_access(data,TENANT,PERMISSIONS[0])
    access.require_division('historical')
    with pytest.raises(ErclaveError):access.require_division('historical',active=True)

class Client:
    value=None
    def session(self,*args):return deepcopy(self.value or context())
class Repo:
    calls=[]
    def list(self,*args):self.calls.append(args);return {'data':[],'meta':{'total':0,'limit':args[-2],'offset':args[-1]}}
    def command(self,access,action,payload,*args,**kwargs):
        self.calls.append((action,payload));return {'id':'cc','code':'CC-000001','name':payload.get('name','Existing'),'division_ref_id':'division','status':'active','revision':1}
@pytest.fixture
def client():
    fake=Client();repo=Repo();repo.calls=[]
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase',cost_center_catalog_enabled=True)
    app.dependency_overrides[get_admin_client]=lambda:fake
    app.dependency_overrides[get_repository]=lambda:repo
    with TestClient(app) as http:yield http,fake,repo
    app.dependency_overrides.clear()
HEADERS={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic','Idempotency-Key':'test-key'}
def test_api_permissions_validation_and_eligible(client):
    http,authority,repo=client
    assert http.get('/v1/cost-centers',headers={'X-Tenant-Id':TENANT}).status_code==401
    assert http.get('/v1/cost-centers/eligible?division_id=foreign',headers=HEADERS).status_code==403
    assert http.get('/v1/cost-centers/eligible?division_id=division&limit=26',headers=HEADERS).status_code==422
    assert http.get('/v1/cost-centers/eligible?division_id=division',headers=HEADERS).status_code==200
    assert repo.calls[-1][3]=='active'
    payload={'name':' Test ','division_ref_id':'division'}
    assert http.post('/v1/cost-centers',headers=HEADERS,json={**payload,'code':'MANUAL'}).status_code==422
    assert http.post('/v1/cost-centers',headers={k:v for k,v in HEADERS.items() if k!='Idempotency-Key'},json=payload).status_code==400
    assert http.post('/v1/cost-centers',headers=HEADERS,json=payload).status_code==201
    assert repo.calls[-1][1]['name']=='Test'
    assert http.patch('/v1/cost-centers/cc',headers=HEADERS,json={'name':'Changed','expected_revision':1,'division_ref_id':'other'}).status_code==422
    authority.value=context();authority.value['permissions']=[PERMISSIONS[0]]
    for method,path,body in [('post','/v1/cost-centers',payload),('patch','/v1/cost-centers/cc',{'name':'Changed','expected_revision':1}),('post','/v1/cost-centers/cc/deactivate',{'expected_revision':1})]:
        assert getattr(http,method)(path,headers=HEADERS,json=body).status_code==403

def test_disabled_catalog_denies_even_owner(client):
    http,_,_=client;app.dependency_overrides[get_settings]=lambda:Settings(cost_center_catalog_enabled=False)
    assert http.get('/v1/cost-centers',headers=HEADERS).status_code==403

@pytest.mark.parametrize('result',[None,[],{}, {'mode':'manual','code':'CC'}, {'mode':'managed','code':''}])
def test_numbering_must_be_managed(result):
    authority=AdminClient(Settings());authority.call=lambda *args:result
    with pytest.raises(ErclaveError) as exc:authority.code(TENANT,None,'actor','key')
    assert exc.value.code=='cost_center_code_unavailable'


def test_database_disconnect_returns_safe_retryable_error(client):
    from sqlalchemy.exc import OperationalError
    http,_,repo=client
    def unavailable(*args):raise OperationalError('PRIVATE SQL',{},Exception('private connection'))
    repo.list=unavailable
    response=http.get('/v1/cost-centers',headers=HEADERS)
    assert response.status_code==503
    assert response.json()['error']['code']=='cost_center_storage_unavailable'
    assert 'PRIVATE' not in response.text


def test_admin_transport_disconnect_fails_closed(monkeypatch):
    from costing_app import authority
    def unavailable(*args,**kwargs):raise ConnectionResetError('private dependency diagnostic')
    monkeypatch.setattr(authority,'open_dependency',unavailable)
    with pytest.raises(ErclaveError) as exc:AdminClient(Settings()).session(TENANT,None,'actor')
    assert exc.value.code=='cost_center_authority_unavailable' and exc.value.status_code==503
