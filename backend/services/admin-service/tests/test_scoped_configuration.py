from fastapi.testclient import TestClient
from app.main import app
from app.auth import AuthenticatedActor, get_authenticated_actor
from app.repositories import get_admin_repository
from erclave_common.config import get_settings, Settings
from test_admin_api import FakeAdminRepository, TENANT_ID
from types import SimpleNamespace
from uuid import uuid4
import pytest
from sqlalchemy import select
from erclave_common.errors import ErclaveError
from app.models import ScopedSetting
from app.scoped_configuration import ScopedConfigurationStore, ScopedTemplateCommand, authorize_scope
from app.schemas import SessionScopeRead
from app.repositories import IdempotencyConflictError
from test_organization_commands import store, hierarchy, command, TENANT


def test_restricted_user_cannot_apply_parent_override_or_other_division():
    ctx = SimpleNamespace(tenant=SimpleNamespace(status='active'), user=SimpleNamespace(status='active'),
        scope=SessionScopeRead(version=2, division_ids=['div-a']))
    authorize_scope(ctx, 'division', 'div-a')
    for kind, id_ in [('division','div-b'), ('society','soc-a')]:
        with pytest.raises(ErclaveError) as error: authorize_scope(ctx, kind, id_)
        assert error.value.status_code == 403
    ctx.scope = SessionScopeRead(version=1)
    with pytest.raises(ErclaveError): authorize_scope(ctx, 'division','div-a')


@pytest.mark.parametrize('payload', [dict(expected_revision=-1,value=None), dict(expected_revision=0,value={'primary_color':'bad'}), dict(expected_revision=0,value={},unknown=True)])
def test_scoped_schema_rejects_invalid_commands(payload):
    with pytest.raises(ValueError): ScopedTemplateCommand.model_validate(payload)


def save(scoped, kind, id_, revision, value, key=None):
    return scoped.update(TENANT, kind, id_, {'expected_revision':revision, 'value':value}, key or str(uuid4()), 'configuration-test', None)


def test_postgres_inheritance_reset_revision_and_idempotency(store):
    issuer, society, division = hierarchy(store)
    scoped = ScopedConfigurationStore(store.repository)
    initial = scoped.read(TENANT, 'division', division['id'])
    assert initial['resolved_from_scope'] == 'corporate'
    parent = save(scoped, 'society', society['id'], 0, {'footer_text':'Society footer'})
    inherited = scoped.read(TENANT, 'division', division['id'])
    assert inherited['value']['footer_text'] == 'Society footer'
    assert inherited['resolved_from_scope'] == 'society' and not inherited['override']
    presentation = scoped.presentation(TENANT, division['id'])
    assert presentation.issuer_ref_id == issuer['id']
    assert presentation.society_ref_id == society['id'] and presentation.division_ref_id == division['id']
    assert presentation.template.footer_text == 'Society footer'
    key = str(uuid4())
    custom = save(scoped, 'division', division['id'], 0, {'footer_text':'Division footer'}, key)
    assert presentation.template.footer_text == 'Society footer'
    assert scoped.presentation(TENANT, division['id']).template.footer_text == 'Division footer'
    assert save(scoped, 'division', division['id'], 0, {'footer_text':'Division footer'}, key) == custom
    with pytest.raises(IdempotencyConflictError): save(scoped, 'division', division['id'], 0, {'footer_text':'Changed'}, key)
    with pytest.raises(ErclaveError) as error: save(scoped, 'division', division['id'], 0, {'footer_text':'Stale'})
    assert error.value.code == 'configuration_revision_conflict'
    # A new parent value does not mutate a saved child override/snapshot.
    save(scoped, 'society', society['id'], parent['revision'], {'footer_text':'New parent'})
    assert scoped.read(TENANT, 'division', division['id'])['value']['footer_text'] == 'Division footer'
    restored = save(scoped, 'division', division['id'], custom['revision'], None)
    assert not restored['override'] and restored['revision'] == 2
    assert restored['value']['footer_text'] == 'New parent'
    again = save(scoped, 'division', division['id'], 2, {'footer_text':'Again'})
    assert again['revision'] == 3


def test_postgres_invalid_scope_and_inactive_ancestry_do_not_write(store):
    _, society, division = hierarchy(store)
    scoped = ScopedConfigurationStore(store.repository)
    for kind in ['society','division']:
        with pytest.raises(ErclaveError): save(scoped,kind,'foreign-or-absent',0,{})
    assert store.test_connection.execute(select(ScopedSetting.scope_ref_id).where(ScopedSetting.tenant_id==TENANT)).all() == []
    command(store,'divisions',{'status':'inactive'},division['id'],'deactivate')
    with pytest.raises(ErclaveError): save(scoped,'division',division['id'],0,{})


def test_scoped_routes_require_permission_and_validate_payload(monkeypatch):
    repo = FakeAdminRepository()
    original = repo.get_session_context
    def context(tenant, user):
        ctx = original(tenant,user)
        if ctx: ctx.scope = SessionScopeRead(version=2, all_divisions=True)
        return ctx
    repo.get_session_context = context
    repo.session_permissions = ['admin.setting.read','admin.setting.update']
    app.dependency_overrides[get_admin_repository] = lambda:repo
    app.dependency_overrides[get_settings] = lambda:Settings(environment='local',auth_mode='firebase')
    app.dependency_overrides[get_authenticated_actor] = lambda:AuthenticatedActor(uid='test',email='admin.qa@erclave.local')
    result = dict(scope_type='division',scope_id='div',revision=0,override=False,resolved_from_scope='corporate',resolved_from_id=TENANT_ID,value={})
    monkeypatch.setattr(ScopedConfigurationStore,'read',lambda *args:result)
    monkeypatch.setattr(ScopedConfigurationStore,'presentation',lambda *args:dict(
        division_ref_id='div',division_code='DIV',division_name='Division',
        society_ref_id='soc',society_code='SOC',society_name='Society',
        issuer_ref_id='emi',issuer_code='EMI',issuer_legal_name='Issuer',
        template_origin='corporate',template_origin_id=TENANT_ID,template={}))
    calls=[]
    def update(*args): calls.append(args); return result
    monkeypatch.setattr(ScopedConfigurationStore,'update',update)
    try:
        client=TestClient(app);path='/v1/configuration/document-template/division/div';headers={'X-Tenant-Id':TENANT_ID}
        assert client.get(path,headers=headers).status_code==200
        assert client.put(path,headers=headers,json={'expected_revision':0,'value':None}).status_code==400
        assert not calls
        assert client.put(path,headers={**headers,'Idempotency-Key':'config-test'},json={'expected_revision':0,'value':None}).status_code==200
        repo.session_permissions=['sales.quote.read']
        presentation=client.get('/v1/configuration/document-presentation/division/div',headers=headers)
        assert presentation.status_code==200 and presentation.json()['data']['issuer_legal_name']=='Issuer'
        repo.session_permissions=[]
        assert client.get('/v1/configuration/document-presentation/division/div',headers=headers).status_code==403
        assert client.get(path,headers=headers).status_code==403
        assert client.put(path,headers=headers,json={'expected_revision':0,'value':None}).status_code==403
    finally: app.dependency_overrides.clear()


def test_postgres_downgrade_refuses_to_destroy_override_history(store):
    import importlib.util
    from pathlib import Path
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    _, society, _ = hierarchy(store)
    scoped = ScopedConfigurationStore(store.repository)
    save(scoped, 'society', society['id'], 0, None)
    path = Path(__file__).resolve().parents[3] / 'alembic/versions/20260927_0039_scoped_settings.py'
    spec = importlib.util.spec_from_file_location('scoped_migration_guard', path)
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError, match='Scoped configuration history exists'):
        with store.test_connection.begin_nested():
            with Operations.context(MigrationContext.configure(store.test_connection)):
                migration.downgrade()
    assert scoped.read(TENANT, 'society', society['id'])['revision'] == 1
