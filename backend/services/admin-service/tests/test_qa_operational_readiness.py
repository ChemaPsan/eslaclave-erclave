"""Release data readiness: no QA connections and only rollback Local fixtures."""
import importlib.util
import json
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest
from contextlib import contextmanager
from sqlalchemy import text
from test_organization_commands import store, hierarchy
from test_organization_migration import TENANT

SCRIPT = Path(__file__).resolve().parents[3] / 'scripts/check_qa_operational_readiness.py'
spec = importlib.util.spec_from_file_location('qa_operational_readiness', SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_guard_import_is_independent_of_other_services_app_alias(monkeypatch):
    monkeypatch.setitem(sys.modules,'app',SimpleNamespace(__path__=[]))
    alternate_spec=importlib.util.spec_from_file_location('qa_operational_readiness_other_app',SCRIPT)
    module=importlib.util.module_from_spec(alternate_spec)
    alternate_spec.loader.exec_module(module)
    assert module.catalog.__module__.startswith('_erclave_admin_qa_readiness.')


@pytest.mark.parametrize('raw', ['', '{}', '[]', '{"soc_a":"mxn"}', '{"soc_a":"MXNN"}', '{"soc_a":true}', '{"soc_a":"MXN","soc_a":"USD"}', '{"email@example.invalid":"MXN"}', '{"soc_a":{"secret":"value"}}'])
def test_currency_confirmation_is_explicit_strict_and_never_echoes_input(raw):
    with pytest.raises(guard.ReadinessError) as exc:guard.parse_currency_confirmations(raw)
    assert str(exc.value) in ('qa_currency_confirmation_invalid','qa_currency_confirmation_required')
    assert raw not in str(exc.value) if raw else True


def test_currency_confirmation_parses_only_explicit_society_codes():
    assert guard.parse_currency_confirmations('{"soc_a":"MXN","soc_b":"USD"}')=={'soc_a':'MXN','soc_b':'USD'}


@pytest.mark.parametrize('environment,confirmation,tenant,expected',[
    ('local','CHECK_ERCLAVE_QA','ten_a','qa_readiness_confirmation_required'),
    ('qa','wrong','ten_a','qa_readiness_confirmation_required'),
    ('qa','CHECK_ERCLAVE_QA','','qa_target_tenant_required'),
])
def test_cli_rejects_missing_scope_before_constructing_engine(monkeypatch,capsys,environment,confirmation,tenant,expected):
    monkeypatch.setenv('ERCLAVE_ENVIRONMENT',environment)
    monkeypatch.setenv('ERCLAVE_QA_READINESS_CONFIRMATION',confirmation)
    monkeypatch.setenv('ERCLAVE_QA_CONFIGURATION_TENANT_ID',tenant)
    monkeypatch.setattr(guard,'create_engine',lambda *args:pytest.fail('Invalid gate configuration reached DB'))
    assert guard.main()==2
    assert json.loads(capsys.readouterr().out)=={'error':{'code':expected}}


def test_cli_enforces_read_only_transaction_and_never_logs_secret(monkeypatch,capsys):
    calls=[]
    class Connection:
        @contextmanager
        def begin(self):yield self
        def exec_driver_sql(self,sql):calls.append(sql)
    class Engine:
        @contextmanager
        def connect(self):yield Connection()
        def dispose(self):calls.append('dispose')
    monkeypatch.setenv('ERCLAVE_ENVIRONMENT','qa')
    monkeypatch.setenv('ERCLAVE_QA_READINESS_CONFIRMATION','CHECK_ERCLAVE_QA')
    monkeypatch.setenv('ERCLAVE_QA_CONFIGURATION_TENANT_ID','ten_authorized')
    monkeypatch.setenv('ERCLAVE_QA_CONFIRMED_SOCIETY_CURRENCIES','{"soc_a":"MXN"}')
    monkeypatch.setenv('ERCLAVE_DATABASE_URL','postgresql://private-user:never-log-secret@qa.invalid/db')
    monkeypatch.setenv('ERCLAVE_COST_CENTER_CATALOG_ENABLED','true')
    monkeypatch.setattr(guard,'create_engine',lambda *args:Engine())
    def check(connection,tenant,currencies,*,catalog_enabled):
        assert calls==['SET TRANSACTION READ ONLY']
        assert tenant=='ten_authorized' and currencies=={'soc_a':'MXN'} and catalog_enabled
        return {'status':'ready'}
    monkeypatch.setattr(guard,'check_operational_readiness',check)
    assert guard.main()==0
    assert json.loads(capsys.readouterr().out)=={'status':'ready'}
    assert calls==['SET TRANSACTION READ ONLY','dispose']


@pytest.fixture
def ready_local(store):
    issuer,society,division=hierarchy(store);conn=store.test_connection
    # The imported fixture owns a rollback-only transaction on the allowed tenant.
    # Existing memberships/roles are never deleted or persisted with changed grants.
    eligible=conn.execute(text("""select m.id,m.metadata from admin.memberships m join admin.users u on u.id=m.user_id
        where m.tenant_id=:t and m.status in ('active','invited') and u.status in ('active','invited')"""),{'t':TENANT}).mappings().all()
    owners=set(conn.execute(text("""select m.id from admin.memberships m join admin.users u on u.id=m.user_id
        join admin.membership_roles mr on mr.tenant_id=m.tenant_id and mr.membership_id=m.id
        join admin.roles r on r.tenant_id=m.tenant_id and r.id=mr.role_id
        where m.tenant_id=:t and m.status='active' and u.status='active' and r.code='owner' and r.system_role=true and r.status='active'"""),{'t':TENANT}).scalars())
    assert owners
    for row in eligible:
        scope={'version':2,'society_ids':['*'] if row['id'] in owners else [],'division_ids':['*'] if row['id'] in owners else []}
        metadata={**(row['metadata'] or {}),'scope':scope}
        conn.execute(text('update admin.memberships set metadata=cast(:v as jsonb) where tenant_id=:t and id=:i'),{'t':TENANT,'i':row['id'],'v':json.dumps(metadata)})
    return conn,issuer,society,division,owners


def check(fixture,*,currencies=None,catalog_enabled=False):
    conn,_,society,_,_=fixture
    return guard.check_operational_readiness(conn,TENANT,currencies if currencies is not None else {society['id']:'MXN'},catalog_enabled=catalog_enabled)


def test_postgres_ready_has_no_optional_center_dependency_or_pii(ready_local):
    result=check(ready_local)
    assert result['status']=='ready' and result['counts']['active_divisions']==1
    output=json.dumps(result)
    assert '@' not in output and 'metadata' not in output and 'email' not in output


def test_postgres_catalog_flag_checks_existing_owner_permissions_without_requiring_center(ready_local):
    assert check(ready_local,catalog_enabled=True)['status']=='ready'


@pytest.mark.parametrize('change,expected',[
    ('authority-missing','qa_organization_authority_required'),
    ('authority-hash','qa_organization_authority_incoherent'),
    ('projection','qa_organization_projection_incoherent'),
    ('fiscal-projection','qa_organization_projection_incoherent'),
    ('owner-empty','qa_owner_operational_scope_required'),
    ('legacy-branch-unknown','qa_membership_scope_unresolvable'),
    ('costing-owner-permissions','qa_cost_center_owner_permissions_required'),
])
def test_postgres_inoperable_target_blocks_gate(ready_local,change,expected):
    conn,issuer,society,division,owners=ready_local
    if change=='authority-missing':conn.execute(text('delete from admin.organization_authorities where tenant_id=:t'),{'t':TENANT})
    elif change=='authority-hash':conn.execute(text('update admin.organization_authorities set projection_hash=:h where tenant_id=:t'),{'t':TENANT,'h':'0'*64})
    elif change=='projection':conn.execute(text("update admin.divisions set name='Unprojected synthetic name' where tenant_id=:t and id=:i"),{'t':TENANT,'i':division['id']})
    elif change=='fiscal-projection':conn.execute(text("update admin.fiscal_issuers set legal_name='Unprojected synthetic issuer' where tenant_id=:t and id=:i"),{'t':TENANT,'i':issuer['id']})
    elif change in ('owner-empty','legacy-branch-unknown'):
        metadata={'scope':{'version':2,'society_ids':[],'division_ids':[]}} if change=='owner-empty' else {'scope':{'branch_ids':['unknown-legacy-branch']}}
        conn.execute(text('update admin.memberships set metadata=cast(:v as jsonb) where tenant_id=:t and id=:i'),{'t':TENANT,'i':sorted(owners)[0],'v':json.dumps(metadata)})
    else:conn.execute(text("delete from admin.role_permissions where tenant_id=:t and permission_id in (select id from admin.permissions where code='costing.cost_center.read')"),{'t':TENANT})
    with pytest.raises(guard.ReadinessError) as exc:check(ready_local,catalog_enabled=change=='costing-owner-permissions')
    assert exc.value.code==expected


@pytest.mark.parametrize('currencies,expected',[({},'qa_currency_confirmation_required'),({'soc_unknown':'MXN'},'qa_currency_confirmation_incomplete')])
def test_postgres_currency_missing_or_unscoped_never_defaults(ready_local,currencies,expected):
    with pytest.raises(guard.ReadinessError) as exc:check(ready_local,currencies=currencies)
    assert exc.value.code==expected


def test_postgres_currency_mismatch_does_not_confirm_import_default(ready_local):
    with pytest.raises(guard.ReadinessError) as exc:check(ready_local,currencies={ready_local[2]['id']:'USD'})
    assert exc.value.code=='qa_currency_confirmation_mismatch'


@pytest.mark.parametrize('scope',[{}, {'branch_ids':['*']}])
def test_postgres_existing_legacy_unrestricted_semantics_are_preserved(ready_local,scope):
    conn,_,_,_,owners=ready_local
    conn.execute(text('update admin.memberships set metadata=cast(:v as jsonb) where tenant_id=:t and id=:i'),{'t':TENANT,'i':sorted(owners)[0],'v':json.dumps({'scope':scope})})
    assert check(ready_local)['status']=='ready'


def test_postgres_existing_legacy_branch_equivalence_resolves_without_scope_write(ready_local):
    conn,_,_,division,owners=ready_local
    # A direct normalized ID is already a valid legacy branch reference in runtime.
    conn.execute(text('update admin.memberships set metadata=cast(:v as jsonb) where tenant_id=:t and id=:i'),{'t':TENANT,'i':sorted(owners)[0],'v':json.dumps({'scope':{'branch_ids':[division['id']]}})})
    before=conn.execute(text('select metadata from admin.memberships where tenant_id=:t and id=:i'),{'t':TENANT,'i':sorted(owners)[0]}).scalar_one()
    assert check(ready_local)['status']=='ready'
    after=conn.execute(text('select metadata from admin.memberships where tenant_id=:t and id=:i'),{'t':TENANT,'i':sorted(owners)[0]}).scalar_one()
    assert after==before
