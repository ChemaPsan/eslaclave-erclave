"""Read-only release gate for an explicitly selected, existing QA tenant.

This gate never imports/activates organization data, grants scope, confirms a
currency, seeds masters or reinterprets historical operational documents.
"""
from __future__ import annotations

import json
import importlib
import importlib.util
import os
from pathlib import Path
import re
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

APP_ROOT = Path(__file__).resolve().parents[1]
ADMIN_PACKAGE = '_erclave_admin_qa_readiness'
if ADMIN_PACKAGE not in sys.modules:
    package_dir = APP_ROOT / 'services' / 'admin-service' / 'app'
    spec = importlib.util.spec_from_file_location(ADMIN_PACKAGE, package_dir / '__init__.py', submodule_search_locations=[str(package_dir)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[ADMIN_PACKAGE] = package
    spec.loader.exec_module(package)
organization_migration = importlib.import_module(ADMIN_PACKAGE + '.organization_migration')
organization_scope = importlib.import_module(ADMIN_PACKAGE + '.organization_scope')
organization_store = importlib.import_module(ADMIN_PACKAGE + '.organization_store')
digest, read_profile = organization_migration.digest, organization_migration.read_profile
catalog, configured_scope, effective_scope = organization_scope.catalog, organization_scope.configured_scope, organization_scope.effective_scope
authority, structure_hash, FISCAL_FIELDS = organization_store.authority, organization_store.structure_hash, organization_store.FISCAL_FIELDS

COST_CENTER_PERMISSIONS = frozenset('costing.cost_center.' + action for action in ('read', 'create', 'update', 'status'))


class ReadinessError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def fail(code):
    raise ReadinessError(code)


def parse_currency_confirmations(value: str) -> dict[str, str]:
    if not isinstance(value, str) or not value.strip():
        fail('qa_currency_confirmation_required')
    def unique(pairs):
        output = {}
        for key, currency in pairs:
            if key in output:
                fail('qa_currency_confirmation_invalid')
            output[key] = currency
        return output
    try:
        result = json.loads(value, object_pairs_hook=unique)
    except (ValueError, TypeError):
        fail('qa_currency_confirmation_invalid')
    if not isinstance(result, dict) or not result:
        fail('qa_currency_confirmation_required')
    if any(not isinstance(key, str) or not re.fullmatch(r'soc_[A-Za-z0-9]{1,36}', key)
           or not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency)
           for key, currency in result.items()):
        fail('qa_currency_confirmation_invalid')
    return result


def _projection_matches(profile, data):
    """Check normalized identity/parent/status/currency projection without writing it."""
    entities = profile.get('legal_entities')
    branches = profile.get('branches')
    if not isinstance(entities, list) or not isinstance(branches, list):
        return False
    society_rows = {row.get('society_id'): row for row in entities if isinstance(row, dict)}
    division_rows = {row.get('division_id'): row for row in branches if isinstance(row, dict)}
    if len(society_rows) != len(entities) or len(division_rows) != len(branches):
        return False
    if set(society_rows) != {row['id'] for row in data['societies']} or set(division_rows) != {row['id'] for row in data['divisions']}:
        return False
    issuer_rows = {row['id']: row for row in data['issuers']}
    for society in data['societies']:
        projected = society_rows[society['id']]
        if any(projected.get(key) != society[key] for key in ('code', 'name', 'status', 'issuer_id', 'base_currency')):
            return False
        issuer = issuer_rows[society['issuer_id']]
        if any(projected.get(key) != issuer.get(key) for key in FISCAL_FIELDS):
            return False
        if any(projected.get(key) != value for key, value in issuer['contact'].items()):
            return False
    for division in data['divisions']:
        projected = division_rows[division['id']]
        if any(projected.get(key) != division[key] for key in ('code', 'name', 'status', 'society_id')):
            return False
        if projected.get('legal_entity_id') != society_rows[division['society_id']].get('id'):
            return False
    return True


def check_operational_readiness(connection, tenant_id: str, confirmed_currencies: dict[str, str], *, catalog_enabled: bool) -> dict:
    """SELECT-only checker; caller owns a read-only transaction in the QA job.

    Local tests may call this on their own rollback-only fixture transaction.
    Membership interpretation intentionally uses the application's existing
    legacy/wildcard semantics; this gate never invents or rewrites a grant.
    """
    if not isinstance(tenant_id, str) or not re.fullmatch(r'ten_[A-Za-z0-9]{1,36}', tenant_id):
        fail('qa_target_tenant_required')
    tenant = connection.execute(text('select status from admin.tenants where id=:t'), {'t': tenant_id}).scalar_one_or_none()
    if tenant != 'active':
        fail('qa_target_tenant_not_active')
    active = authority(connection, tenant_id)
    if not active:
        fail('qa_organization_authority_required')
    try:
        profile = read_profile(connection, tenant_id)
        if digest(active['source_profile']) != active['source_hash'] or structure_hash(profile) != active['projection_hash']:
            fail('qa_organization_authority_incoherent')
        data = catalog(connection, tenant_id)
        if not _projection_matches(profile, data):
            fail('qa_organization_projection_incoherent')
    except ReadinessError:
        raise
    except (KeyError, TypeError, ValueError):
        fail('qa_organization_authority_incoherent')

    issuers = {row['id'] for row in data['issuers'] if row['status'] == 'active'}
    societies = {row['id']: row for row in data['societies'] if row['status'] == 'active' and row['issuer_id'] in issuers}
    divisions = [row for row in data['divisions'] if row['status'] == 'active' and row['society_id'] in societies]
    if not divisions:
        fail('qa_active_organization_chain_required')
    # Confirmation comes from the reviewed release plan, never from the importer's
    # historical MXN default or an operational document's currency.
    if not isinstance(confirmed_currencies, dict) or not confirmed_currencies:
        fail('qa_currency_confirmation_required')
    if set(confirmed_currencies) != set(societies):
        fail('qa_currency_confirmation_incomplete')
    available_currencies = set(connection.execute(text("select code from admin.catalog_items where tenant_id=:t and catalog_code='currencies' and status='active'"), {'t': tenant_id}).scalars().all())
    for id_, society in societies.items():
        currency = confirmed_currencies[id_]
        if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
            fail('qa_currency_confirmation_invalid')
        if society['base_currency'] != currency:
            fail('qa_currency_confirmation_mismatch')
        if currency not in available_currencies:
            fail('qa_society_currency_not_active')

    owner_roles = connection.execute(text("select id from admin.roles where tenant_id=:t and code='owner' and system_role=true and status='active'"), {'t': tenant_id}).scalars().all()
    if not owner_roles:
        fail('qa_operational_owner_required')
    owners = set(connection.execute(text("""select distinct m.id from admin.memberships m
        join admin.users u on u.id=m.user_id
        join admin.membership_roles mr on mr.tenant_id=m.tenant_id and mr.membership_id=m.id
        where m.tenant_id=:t and m.status='active' and u.status='active' and mr.role_id=any(:roles)"""), {'t': tenant_id, 'roles': owner_roles}).scalars().all())
    if not owners:
        fail('qa_operational_owner_required')
    memberships = connection.execute(text("""select m.id,m.metadata from admin.memberships m
        join admin.users u on u.id=m.user_id where m.tenant_id=:t
        and m.status in ('active','invited') and u.status in ('active','invited')"""), {'t': tenant_id}).mappings().all()
    for membership in memberships:
        try:
            scope = effective_scope(configured_scope(membership['metadata'], data), data)
        except Exception:
            # Never log a user, a legacy branch value, membership metadata or PII.
            fail('qa_membership_scope_unresolvable')
        if scope['version'] != 2:
            fail('qa_membership_scope_unresolvable')
        if membership['id'] in owners and not scope['division_ids']:
            fail('qa_owner_operational_scope_required')

    if catalog_enabled:
        for role in owner_roles:
            permissions = set(connection.execute(text("""select p.code from admin.role_permissions rp
                join admin.permissions p on p.id=rp.permission_id where rp.tenant_id=:t and rp.role_id=:r
                and p.status='active' and p.classification='tenant' and p.assignable_to_tenant_role=true"""), {'t': tenant_id, 'r': role}).scalars().all())
            if not COST_CENTER_PERMISSIONS.issubset(permissions):
                fail('qa_cost_center_owner_permissions_required')
    return {'status': 'ready', 'checks': ['tenant_active', 'organization_authority_coherent', 'active_organization_chain',
            'explicit_society_currency_confirmation', 'membership_scopes_resolvable', 'operational_owner_scope',
            'cost_center_owner_permissions' if catalog_enabled else 'cost_center_catalog_disabled'],
            'counts': {'active_societies': len(societies), 'active_divisions': len(divisions),
                       'memberships_checked': len(memberships), 'operational_owners': len(owners)}}


def main() -> int:
    try:
        if os.getenv('ERCLAVE_ENVIRONMENT') != 'qa' or os.getenv('ERCLAVE_QA_READINESS_CONFIRMATION') != 'CHECK_ERCLAVE_QA':
            fail('qa_readiness_confirmation_required')
        tenant_id = os.getenv('ERCLAVE_QA_CONFIGURATION_TENANT_ID', '').strip()
        if not re.fullmatch(r'ten_[A-Za-z0-9]{1,36}', tenant_id):
            fail('qa_target_tenant_required')
        currencies = parse_currency_confirmations(os.getenv('ERCLAVE_QA_CONFIRMED_SOCIETY_CURRENCIES', ''))
        database = os.getenv('ERCLAVE_DATABASE_URL', '')
        if not database:
            fail('qa_database_configuration_required')
        catalog_flag = os.getenv('ERCLAVE_COST_CENTER_CATALOG_ENABLED', 'false').lower()
        if catalog_flag not in ('true', 'false'):
            fail('qa_catalog_flag_invalid')
        engine = create_engine(database)
        try:
            with engine.connect() as connection, connection.begin():
                connection.exec_driver_sql('SET TRANSACTION READ ONLY')
                result = check_operational_readiness(connection, tenant_id, currencies, catalog_enabled=catalog_flag == 'true')
        finally:
            engine.dispose()
        print(json.dumps(result, sort_keys=True))
        return 0
    except ReadinessError as exc:
        print(json.dumps({'error': {'code': exc.code}}))
        return 2
    except (SQLAlchemyError, OSError, ValueError, TypeError):
        print(json.dumps({'error': {'code': 'qa_operational_readiness_unavailable'}}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
