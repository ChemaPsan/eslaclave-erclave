from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from erclave_common.config import Settings, get_settings
from app.auth import AuthenticatedActor, get_authenticated_actor
from app.main import app
from app.repositories import get_admin_repository
from app.organization_scope import ScopeStore, effective_scope, MembershipScope
from app.schemas import SessionScopeRead
from test_admin_api import FakeAdminRepository, TENANT_ID, USER_ID
from test_organization_scope import catalog


@pytest.fixture
def scope_api(monkeypatch):
    repo = FakeAdminRepository()
    original = repo.get_session_context
    def context(tenant, user):
        result = original(tenant, user)
        if result:
            result.scope = SessionScopeRead.model_validate(effective_scope(MembershipScope(society_ids=["soc"], division_ids=["div-a"]), catalog()))
        return result
    repo.get_session_context = context
    repo.session_permissions = ["admin.user.read", "admin.user.update"]
    app.dependency_overrides[get_admin_repository] = lambda: repo
    app.dependency_overrides[get_settings] = lambda: Settings(environment="local", auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(uid="test", email="admin.qa@erclave.local")
    calls = []
    monkeypatch.setattr(ScopeStore, "read", lambda *args: {"version": 2, "revision": 2, "society_ids": ["soc"], "division_ids": ["div-a"]})
    def update(self, tenant, user, payload, key, correlation, actor):
        calls.append(payload)
        return {key_: value for key_, value in payload.items() if key_ != "expected_revision"} | {"revision": 3}
    monkeypatch.setattr(ScopeStore, "update", update)
    try:
        yield TestClient(app), repo, calls
    finally:
        app.dependency_overrides.clear()


def test_session_validates_selected_division_and_derives_ancestors(scope_api):
    client, _, _ = scope_api
    response = client.get('/v1/session/context?division_id=div-a', headers={'X-Tenant-Id': TENANT_ID})
    assert response.status_code == 200, response.text
    assert response.json()['data']['scope']['active_society_id'] == 'soc'
    assert response.json()['data']['scope']['active_issuer_id'] == 'emi'
    assert client.get('/v1/session/context?division_id=div-b', headers={'X-Tenant-Id': TENANT_ID}).status_code == 403


@pytest.mark.parametrize('method,permission', [('GET', 'admin.user.read'), ('PUT', 'admin.user.update')])
def test_scope_requires_permission_and_authentication(scope_api, method, permission):
    client, repo, calls = scope_api
    repo.session_permissions = []
    response = client.request(method, f'/v1/users/{USER_ID}/organization-scope', headers={'X-Tenant-Id': TENANT_ID}, json={})
    assert response.status_code == 403
    assert calls == []
    app.dependency_overrides[get_authenticated_actor] = lambda: None
    assert client.get(f'/v1/users/{USER_ID}/organization-scope', headers={'X-Tenant-Id': TENANT_ID}).status_code == 401


def test_scope_put_requires_revision_key_and_strict_payload(scope_api):
    client, _, calls = scope_api
    path = f'/v1/users/{USER_ID}/organization-scope'
    payload = {'version': 2, 'expected_revision': 2, 'society_ids': [], 'division_ids': []}
    headers = {'X-Tenant-Id': TENANT_ID}
    assert client.put(path, headers=headers, json=payload).status_code == 400
    headers['Idempotency-Key'] = 'test-scope-api'
    assert client.put(path, headers=headers, json={**payload, 'tenant_id': 'other'}).status_code == 422
    assert client.put(path, headers=headers, json={**payload, 'division_ids': ['*']}).status_code == 422
    assert client.put(path, headers=headers, json=payload).status_code == 200
    assert len(calls) == 1
