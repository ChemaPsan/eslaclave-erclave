"""QA inspection contract; all database exercises use authorized Local only."""
import importlib.util
import json
import os
from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

SCRIPT = Path(__file__).resolve().parents[3] / 'scripts/inspect_qa_release_baseline.py'
spec = importlib.util.spec_from_file_location('qa_release_baseline', SCRIPT)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)
TENANT = 'ten_739ee59d765d5e14818674800d'


@pytest.mark.parametrize('environment,confirmation,tenant,code', [
    ('local', 'INSPECT_ERCLAVE_QA', TENANT, 'qa_inspection_confirmation_required'),
    ('qa', 'wrong', TENANT, 'qa_inspection_confirmation_required'),
    ('qa', 'INSPECT_ERCLAVE_QA', '', 'qa_target_tenant_required'),
    ('qa', 'INSPECT_ERCLAVE_QA', 'ten_bad;select secret', 'qa_target_tenant_required'),
])
def test_reject_before_connection(monkeypatch, capsys, environment, confirmation, tenant, code):
    monkeypatch.setenv('ERCLAVE_ENVIRONMENT', environment)
    monkeypatch.setenv('ERCLAVE_QA_INSPECTION_CONFIRMATION', confirmation)
    monkeypatch.setenv('ERCLAVE_QA_CONFIGURATION_TENANT_ID', tenant)
    monkeypatch.setattr(inspector, 'create_engine', lambda *a, **kw: pytest.fail('DB must not be reached'))
    assert inspector.main() == 2
    assert json.loads(capsys.readouterr().out) == {'error': {'code': code}}


def cli_environment(monkeypatch):
    monkeypatch.setenv('ERCLAVE_ENVIRONMENT', 'qa')
    monkeypatch.setenv('ERCLAVE_QA_INSPECTION_CONFIRMATION', 'INSPECT_ERCLAVE_QA')
    monkeypatch.setenv('ERCLAVE_QA_CONFIGURATION_TENANT_ID', TENANT)
    monkeypatch.setenv('ERCLAVE_QA_EXPECTED_CLOUD_SQL_CONNECTION_NAME', inspector.EXPECTED_QA_CONNECTION)
    monkeypatch.setenv('ERCLAVE_DATABASE_URL', 'postgresql+psycopg://secret-user:private-password@/private?host=/cloudsql/erclave:us-central1:erclave-qa-postgres')


@pytest.mark.parametrize('url,expected', [
    ('postgresql://user:private-password@prod.invalid/db', inspector.EXPECTED_QA_CONNECTION),
    ('postgresql://user:private-password@127.0.0.1/erclave_local', inspector.EXPECTED_QA_CONNECTION),
    ('postgresql://user:private-password@/db?host=/cloudsql/other:us-central1:erclave-qa-postgres', inspector.EXPECTED_QA_CONNECTION),
    ('postgresql://user:private-password@/db?host=/cloudsql/erclave:us-central1:erclave-production-postgres', inspector.EXPECTED_QA_CONNECTION),
    ('mysql://user:private-password@/db?host=/cloudsql/erclave:us-central1:erclave-qa-postgres', inspector.EXPECTED_QA_CONNECTION),
    ('postgresql://user:private-password@/db', inspector.EXPECTED_QA_CONNECTION),
    ('postgresql://user:private-password@/db?host=/cloudsql/erclave:us-central1:erclave-qa-postgres&hostaddr=10.0.0.1', inspector.EXPECTED_QA_CONNECTION),
    ('postgresql://user:private-password@/db?host=/cloudsql/erclave:us-central1:erclave-qa-postgres', ''),
    ('postgresql://user:private-password@/db?host=/cloudsql/erclave:us-central1:erclave-qa-postgres', 'other:us-central1:prod'),
])
def test_cli_rejects_wrong_database_before_connection(monkeypatch, capsys, url, expected):
    cli_environment(monkeypatch)
    monkeypatch.setenv('ERCLAVE_DATABASE_URL', url)
    monkeypatch.setenv('ERCLAVE_QA_EXPECTED_CLOUD_SQL_CONNECTION_NAME', expected)
    monkeypatch.setattr(inspector, 'create_engine', lambda *a, **kw: pytest.fail('Wrong target must not connect'))
    assert inspector.main() == 2
    output = capsys.readouterr().out
    assert json.loads(output)['error']['code'] in ('qa_expected_connection_invalid', 'qa_database_target_invalid')
    assert 'private-password' not in output and url not in output


def test_qa_unix_socket_is_accepted_without_connecting():
    url = 'postgresql+psycopg://user:private-password@/database?host=/cloudsql/erclave:us-central1:erclave-qa-postgres'
    assert inspector.validate_database_target(url, inspector.EXPECTED_QA_CONNECTION).host is None


@pytest.mark.parametrize('fails', [False, True])
def test_cli_readonly_repeatable_before_first_read_and_sanitized_failure(monkeypatch, capsys, fails):
    calls = []
    class Connection:
        @contextmanager
        def begin(self):yield self
        def exec_driver_sql(self, sql):calls.append(sql)
    class Engine:
        @contextmanager
        def connect(self):yield Connection()
        def dispose(self):calls.append('dispose')
    cli_environment(monkeypatch)
    monkeypatch.setattr(inspector, 'create_engine', lambda *a, **kw: Engine())
    def inspect(connection, tenant):
        assert calls == ['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY']
        assert tenant == TENANT
        if fails:raise RuntimeError('private-password and customer@example.invalid and SQL diagnostics')
        return {'inspection': 'qa_release_baseline'}
    monkeypatch.setattr(inspector, 'inspect_baseline', inspect)
    assert inspector.main() == (2 if fails else 0)
    output = capsys.readouterr().out
    assert 'private-password' not in output and 'example.invalid' not in output
    assert calls[-1] == 'dispose'
    assert json.loads(output) == ({'error': {'code': 'qa_inspection_failed'}} if fails else {'inspection': 'qa_release_baseline'})


@pytest.mark.parametrize('metadata,mode,field,count,wildcards', [
    ({}, 'legacy', 'branch_ids', None, 0),
    ({'scope': {'branch_ids': ['*']}}, 'legacy', 'branch_ids', 1, 1),
    ({'scope': {'version': 2, 'division_ids': []}}, 'v2', 'division_ids', 0, 0),
    ({'scope': {'version': 2, 'division_ids': ['*']}}, 'v2', 'division_ids', 1, 1),
    ({'scope': 'private@example.invalid'}, 'invalid', 'branch_ids', None, 0),
])
def test_scope_fingerprint_counts_never_echo_raw_metadata(metadata,mode,field,count,wildcards):
    result=inspector.summarize_scope(metadata)
    assert result['mode']==mode
    assert result[field+'_count']==count and result[field+'_wildcard_count']==wildcards
    assert 'private@example.invalid' not in json.dumps(result)
    assert len(result['scope_hash'])==64


@pytest.mark.parametrize('raw,expected', [({}, True), ({'branch_ids': None}, True),
    ({'branch_ids': []}, True), ({'branches': ['*']}, True),
    ({'branch_ids': ['branch_a']}, False), ('invalid', False),
    ({'version': 2, 'division_ids': []}, False)])
def test_legacy_unrestricted_semantics_are_explicit_without_resolving_grants(raw, expected):
    assert inspector.summarize_scope({'scope': raw})['legacy_unrestricted_semantics'] is expected


class Result:
    def __init__(self, rows):self.rows = rows
    def all(self):return self.rows
    def mappings(self):return self
    def scalars(self):return self
    def __iter__(self):return iter(self.rows)


class OldSchemaConnection:
    """Model 0036 absence without modifying any real table or migration head."""
    def __init__(self, status='active'):
        self.status = status
        self.statements = []
    def execute(self, sql, params=None):
        sql = str(sql);self.statements.append((sql, params))
        if 'information_schema.columns' in sql:
            columns = {k: set(inspector.TABLE_FIELDS[k]) | ({'tenant_id'} if k != 'tenants' else set()) for k in ('tenants','tenant_settings','memberships','roles','membership_roles')}
            columns['users'] = {'id', 'status'}
            return Result([(t, c) for t, values in columns.items() for c in values])
        assert sql.lower().startswith('select ')
        if 'from alembic_version' in sql:return Result(['20260913_0036'])
        assert params == {'tenant': TENANT}
        if 'from admin.tenants' in sql:return Result([{'id': TENANT, 'status': self.status}] if self.status else [])
        if 'from admin.tenant_settings' in sql:return Result([{'key': 'organization.profile', 'value': {'corporate': {'contact_email': 'hidden@example.invalid'}, 'legal_entities': [{'id': 'old_soc', 'code': 'OLD', 'legal_name': 'Private Legal Name', 'tax_id': 'SECRET-TAX'}], 'branches': []}}])
        if 'from admin.memberships m' in sql:return Result([])
        if any(f'from admin.{t} ' in sql for t in ('memberships','roles','membership_roles')):return Result([])
        pytest.fail('Unexpected or absent-table query: ' + sql)


def test_0036_without_extension_tables_and_no_pii_or_currency_default():
    result = inspector.inspect_baseline(OldSchemaConnection(), TENANT)
    assert result['alembic_heads'] == ['20260913_0036']
    org = result['organization']
    assert org['legacy_profile_nonempty'] and not org['authority_present']
    assert not org['normalized']['societies']['table_present']
    assert org['legacy_collections']['legal_entities']['records'][0]['base_currency'] is None
    serialized = json.dumps(result)
    assert all(v not in serialized for v in ('hidden@example.invalid', 'Private Legal Name', 'SECRET-TAX', 'contact_email'))


@pytest.mark.parametrize('status,code', [(None, 'qa_target_tenant_not_found'), ('inactive', 'qa_target_tenant_not_active')])
def test_target_must_exist_and_be_active(status, code):
    with pytest.raises(inspector.InspectionError, match=code):inspector.inspect_baseline(OldSchemaConnection(status), TENANT)


def test_current_local_postgres_snapshot_is_readonly_and_repeatable():
    url = os.getenv('ERCLAVE_TEST_DATABASE_URL')
    if not url:pytest.skip('Authorized Local PostgreSQL URL not configured')
    from urllib.parse import urlparse
    parsed = urlparse(url)
    assert parsed.hostname in ('127.0.0.1', 'localhost', '::1') and parsed.path == '/erclave_local'
    engine = create_engine(url)
    try:
        with engine.connect() as connection, connection.begin():
            connection.exec_driver_sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            assert connection.execute(text('show transaction_read_only')).scalar() == 'on'
            assert connection.execute(text('show transaction_isolation')).scalar() == 'repeatable read'
            first = inspector.inspect_baseline(connection, TENANT)
            second = inspector.inspect_baseline(connection, TENANT)
            assert first == second
            assert first['tenant'] == {'id': TENANT, 'status': 'active'}
            assert first['organization']['normalized']['societies']['table_present']
            assert 'email' not in json.dumps(first)
    finally:engine.dispose()
