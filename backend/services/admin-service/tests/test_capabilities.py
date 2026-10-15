from fastapi.testclient import TestClient
from app.main import app
from app.repositories import get_admin_repository
from erclave_common.config import get_settings, Settings
from copy import deepcopy
import pytest
from app.capabilities import capability_availability, enrich_capabilities
from app.schemas import EntitlementRead
from test_admin_api import FakeAdminRepository, TENANT_ID, USER_ID


def context():
    return FakeAdminRepository().get_session_context(TENANT_ID, USER_ID)


def test_organization_available_without_optional_modules_and_no_permission_grant():
    value = context()
    value.permissions = []
    before = value.model_dump()
    result = enrich_capabilities(value)
    assert result.capabilities['organization'].available
    assert result.permissions == []
    assert value.model_dump() == before
    assert result.cost_center_requirement == 'enabled_imputation_flows'
    assert result.capability_policy_version == 1


@pytest.mark.parametrize('code', ['costing_analytics', 'accounting'])
def test_future_capability_cannot_be_enabled_by_entitlements_or_owner_role(code):
    value = context()
    value.entitlements += [EntitlementRead(module_code=m, status='active', tenant_enabled=True)
                           for m in ['costing', 'accounting']]
    value.active_modules += ['costing', 'accounting']
    value.permissions += ['accounting.journal.read', 'costing.cost_center.read']
    item = capability_availability(value)[code]
    assert not item['available']
    assert not item['implemented']
    assert item['reason'] == 'not_implemented'


@pytest.mark.parametrize('case', ['missing', 'disabled', 'suspended', 'duplicate', 'tenant', 'user'])
def test_available_modules_list_never_bypasses_current_state(case):
    value = context()
    value.active_modules = ['admin', 'costing', 'accounting']
    if case == 'missing': value.entitlements = []
    elif case == 'duplicate': value.entitlements += deepcopy(value.entitlements)
    elif case == 'disabled': value.entitlements[0].tenant_enabled = False
    elif case == 'suspended': value.entitlements[0].status = 'suspended'
    elif case == 'tenant': value.tenant.status = 'suspended'
    else: value.user.status = 'inactive'
    assert not capability_availability(value)['organization']['available']


def test_catalog_basic_is_admin_availability_with_costing_ownership():
    result = capability_availability(context())
    assert result['cost_center_catalog']['availability_module'] == 'admin'
    assert result['cost_center_catalog']['owner_service'] == 'costing-service'
    assert result['accounting']['availability_module'] == 'accounting'
    assert result['costing_analytics']['availability_module'] == 'costing'


def test_session_response_exposes_policy_without_enabling_planned_modules():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(environment='local', auth_mode='demo')
    try:
        client = TestClient(app)
        response = client.get('/v1/session/context', headers={'X-Tenant-Id': TENANT_ID, 'X-Actor-Id': USER_ID})
        assert response.status_code == 200, response.text
        data = response.json()['data']
        assert data['capability_policy_version'] == 1
        assert data['capabilities']['organization']['available']
        assert not data['capabilities']['accounting']['available']
        assert not data['capabilities']['cost_center_catalog']['available']
        assert data['cost_center_requirement'] == 'enabled_imputation_flows'
        assert data['scope']
        assert client.get('/v1/session/context', headers={'X-Tenant-Id': TENANT_ID}).status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_basic_catalog_requires_deployed_runtime_and_admin_only():
    value = context()
    assert not capability_availability(value)['cost_center_catalog']['available']
    result = capability_availability(value, catalog_enabled=True)
    assert result['cost_center_catalog']['available']
    assert result['cost_center_catalog']['implemented']
    assert not result['accounting']['available']
    assert not result['costing_analytics']['available']
    value.entitlements = []
    assert not capability_availability(value, catalog_enabled=True)['cost_center_catalog']['available']
