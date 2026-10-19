"""Governed SELECT-only baseline, compatible with pre-organization QA schemas.

No activation, migration, scope grant or currency inference is performed. Legacy
JSON is hashed in memory and only allowlisted structural fields leave the job.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

EXPECTED_QA_CONNECTION = 'erclave:us-central1:erclave-qa-postgres'


class InspectionError(ValueError):
    pass


def validate_database_target(value, expected_connection):
    """Fail closed before connecting: this inspector only uses the QA socket."""
    if expected_connection != EXPECTED_QA_CONNECTION:
        raise InspectionError('qa_expected_connection_invalid')
    try:
        url = make_url(value)
    except Exception:
        raise InspectionError('qa_database_target_invalid') from None
    if url.get_backend_name() != 'postgresql' or url.drivername not in ('postgresql', 'postgresql+psycopg', 'postgresql+psycopg2'):
        raise InspectionError('qa_database_target_invalid')
    # Never accept TCP, a host list, alternate socket, fallback port or libpq
    # service configuration that could redirect a correct-looking secret.
    if url.host or url.port is not None or not url.database or url.query.get('host') != '/cloudsql/' + expected_connection:
        raise InspectionError('qa_database_target_invalid')
    if any(key in url.query for key in ('hostaddr', 'port', 'service', 'servicefile')):
        raise InspectionError('qa_database_target_invalid')
    return url


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def safe(value):
    """No arbitrary free text, email addresses, multiline data or SQL diagnostics."""
    return value if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.:/ -]{1,120}', value) else None


TABLE_FIELDS = {
    'tenants': ('id', 'status'),
    'tenant_settings': ('key', 'value'),
    'organization_authorities': ('source_hash', 'projection_hash', 'source_profile'),
    'fiscal_issuers': ('id', 'code', 'status'),
    'societies': ('id', 'code', 'status', 'issuer_id', 'base_currency'),
    'divisions': ('id', 'code', 'status', 'society_id'),
    'organization_legacy_mappings': ('collection', 'legacy_id', 'division_id', 'society_id', 'issuer_id'),
    'memberships': ('id', 'user_id', 'status', 'metadata'),
    'roles': ('id', 'code', 'status', 'system_role'),
    'membership_roles': ('membership_id', 'role_id'),
    'code_sequences': ('id', 'document_type', 'mode', 'prefix', 'separator', 'padding', 'next_number', 'status'),
}


def schema_columns(connection):
    rows = connection.execute(text("""select table_name,column_name from information_schema.columns
        where table_schema='admin'""")).all()
    output = {}
    for table, column in rows:
        output.setdefault(table, set()).add(column)
    return output


def tenant_rows(connection, columns, table, tenant):
    # SQL identifiers come exclusively from the fixed allowlist, never inputs.
    if table not in TABLE_FIELDS:
        raise InspectionError('qa_inspection_table_not_allowed')
    if table not in columns:
        return []
    wanted = TABLE_FIELDS[table]
    if not set(wanted).issubset(columns[table]) or 'tenant_id' not in columns[table] and table != 'tenants':
        raise InspectionError('qa_inspection_schema_incompatible')
    where = 'id' if table == 'tenants' else 'tenant_id'
    sql = f"select {','.join(wanted)} from admin.{table} where {where}=:tenant"
    if table == 'tenant_settings':
        sql += " and key='organization.profile'"
    return sorted([dict(row) for row in connection.execute(text(sql), {'tenant': tenant}).mappings()],
        key=lambda row: (str(row.get('id', '')), str(row.get('membership_id', '')), str(row.get('role_id', ''))))


def public_records(rows, fields):
    return [{field: safe(row.get(field)) for field in fields} for row in rows]


def summarize_scope(metadata):
    """Opaque scope fingerprint and configured counts, not an authorization gate."""
    metadata = metadata if isinstance(metadata, dict) else {}
    raw = metadata.get('scope', metadata)
    result = {'scope_hash': digest(raw), 'mode': 'invalid' if not isinstance(raw, dict)
        else 'v2' if 'version' in raw else 'legacy'}
    legacy = raw.get('branch_ids', raw.get('branches')) if isinstance(raw, dict) else None
    result['legacy_unrestricted_semantics'] = isinstance(raw, dict) and 'version' not in raw and (legacy is None or legacy == [] or legacy == ['*'])
    for field in ('branch_ids', 'branches', 'society_ids', 'division_ids'):
        values = raw.get(field) if isinstance(raw, dict) else None
        result[field + '_count'] = len(values) if isinstance(values, list) else None
        result[field + '_wildcard_count'] = values.count('*') if isinstance(values, list) else 0
    return result


def inspect_baseline(connection, tenant):
    columns = schema_columns(connection)
    if not {'tenants', 'tenant_settings', 'memberships', 'roles', 'membership_roles', 'users'}.issubset(columns):
        raise InspectionError('qa_inspection_schema_incompatible')
    targets = tenant_rows(connection, columns, 'tenants', tenant)
    if not targets:
        raise InspectionError('qa_target_tenant_not_found')
    if targets[0]['status'] != 'active':
        raise InspectionError('qa_target_tenant_not_active')
    heads = list(connection.execute(text('select version_num from alembic_version order by version_num')).scalars())
    profile_rows = tenant_rows(connection, columns, 'tenant_settings', tenant)
    profile = profile_rows[0]['value'] if profile_rows else None
    if profile is not None and not isinstance(profile, dict):
        raise InspectionError('qa_legacy_profile_invalid')
    authorities = tenant_rows(connection, columns, 'organization_authorities', tenant)
    active = authorities[0] if authorities else None
    structural = {key: tenant_rows(connection, columns, table, tenant) for key, table in (
        ('issuers', 'fiscal_issuers'), ('societies', 'societies'), ('divisions', 'divisions'), ('mappings', 'organization_legacy_mappings'))}
    members = tenant_rows(connection, columns, 'memberships', tenant)
    roles = tenant_rows(connection, columns, 'roles', tenant)
    bindings = tenant_rows(connection, columns, 'membership_roles', tenant)
    # Join by both identity and tenant membership; never select names/emails.
    users = dict(connection.execute(text('''select m.user_id,u.status from admin.memberships m
        join admin.users u on u.id=m.user_id where m.tenant_id=:tenant'''), {'tenant': tenant}).all())
    scopes = []
    for member in sorted(members, key=lambda r: r['id']):
        scopes.append({'membership_id': safe(member['id']), 'membership_status': safe(member['status']),
            'user_status': safe(users.get(member['user_id'])),
            'role_ids': [safe(v) for v in sorted(r['role_id'] for r in bindings if r['membership_id'] == member['id'])],
            **summarize_scope(member['metadata'])})
    legacy = {}
    for collection in ('legal_entities', 'branches'):
        entries = (profile or {}).get(collection, [])
        valid = isinstance(entries, list) and all(isinstance(r, dict) for r in entries)
        legacy[collection] = {'valid_array': valid, 'count': len(entries) if isinstance(entries, list) else None,
            'records': public_records(entries, ('id', 'code', 'status', 'legal_entity_id', 'base_currency')) if valid else []}
    projection = digest({key: (profile or {}).get(key, []) for key in ('legal_entities', 'branches')}) if profile is not None else None
    normalized = {key: {'table_present': table in columns, 'count': len(structural[key]), 'records': public_records(structural[key], TABLE_FIELDS[table])}
        for key, table in (('issuers', 'fiscal_issuers'), ('societies', 'societies'), ('divisions', 'divisions'))}
    return {'inspection': 'qa_release_baseline', 'format_version': 1,
        'tenant': {'id': tenant, 'status': 'active'}, 'alembic_heads': [safe(v) for v in heads],
        'organization': {'legacy_profile_present': profile is not None,
            'legacy_profile_nonempty': any((profile or {}).get(k) for k in ('legal_entities', 'branches')),
            'legacy_profile_hash': digest(profile) if profile is not None else None,
            'current_projection_hash': projection, 'legacy_collections': legacy,
            'authority_present': bool(active), 'authority_source_hash': safe(active['source_hash']) if active else None,
            'authority_source_profile_hash': digest(active['source_profile']) if active else None,
            'authority_projection_hash': safe(active['projection_hash']) if active else None,
            'authority_projection_matches': active['projection_hash'] == projection if active else None,
            'normalized': normalized, 'legacy_mapping_count': len(structural['mappings'])},
        'roles': [{**public_records([r], ('id', 'code', 'status'))[0], 'system_role': bool(r['system_role']),
            'active_membership_count': sum(m['membership_status'] == 'active' and m['user_status'] == 'active' and r['id'] in m['role_ids'] for m in scopes)} for r in roles],
        'membership_count': len(members), 'scopes': scopes,
        'sequences': {'table_present': 'code_sequences' in columns,
            'records': [{'id': safe(row['id']), 'document_type': safe(row['document_type']),
                'mode': row['mode'] if row['mode'] in ('managed', 'manual') else None,
                'status': row['status'] if row['status'] in ('active', 'inactive') else None,
                'next_number': row['next_number'], 'configuration_hash': digest(row)}
                for row in tenant_rows(connection, columns, 'code_sequences', tenant)]},
        'limitations': ['inspection_only_no_activation_or_readiness_certification',
            'legacy_currency_not_inferred_or_confirmed', 'nonempty_legacy_profile_requires_review_before_activation',
            'snapshot_read_only_repeatable_read_no_business_writes',
            'scope_fingerprints_are_not_effective_authorization_or_operability_checks']}


def main():
    engine = None
    try:
        if os.getenv('ERCLAVE_ENVIRONMENT') != 'qa' or os.getenv('ERCLAVE_QA_INSPECTION_CONFIRMATION') != 'INSPECT_ERCLAVE_QA':
            raise InspectionError('qa_inspection_confirmation_required')
        tenant = os.getenv('ERCLAVE_QA_CONFIGURATION_TENANT_ID', '')
        if not re.fullmatch(r'ten_[A-Za-z0-9]{1,36}', tenant):
            raise InspectionError('qa_target_tenant_required')
        url = os.getenv('ERCLAVE_DATABASE_URL', '')
        if not url:
            raise InspectionError('qa_database_url_required')
        validate_database_target(url, os.getenv('ERCLAVE_QA_EXPECTED_CLOUD_SQL_CONNECTION_NAME'))
        engine = create_engine(url, hide_parameters=True)
        with engine.connect() as connection, connection.begin():
            connection.exec_driver_sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            result = inspect_baseline(connection, tenant)
        print(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, InspectionError) else 'qa_inspection_failed'
        print(json.dumps({'error': {'code': code}}))
        return 2
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
