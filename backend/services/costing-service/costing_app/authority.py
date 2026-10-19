from dataclasses import dataclass
import json
from urllib import error, request
from fastapi import Depends, Header
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError
from erclave_common.transport import open_dependency

def fail(code, status=403, field=None):
    raise ErclaveError(code, 'Cost center request could not be completed.', status_code=status, details={'field': field} if field else {})

class AdminClient:

    def __init__(self, settings):
        self.base = settings.admin_service_url.rstrip('/')
        self.timeout = settings.authorization_timeout_seconds

    def call(self, path, tenant, authorization, actor, payload=None, key=None):
        headers = {'X-Tenant-Id': tenant, 'Authorization': authorization or '', 'X-Actor-Id': actor or '', 'Content-Type': 'application/json'}
        if key:
            headers.update({'Idempotency-Key': key, 'X-Correlation-Id': key})
        req = request.Request(self.base + path, headers=headers, data=json.dumps(payload).encode() if payload is not None else None, method='POST' if payload is not None else 'GET')
        try:
            with open_dependency(req, timeout=self.timeout, opener=request.urlopen) as response:
                return json.loads(response.read())['data']
        except error.HTTPError as exc:
            if exc.code >= 500 or exc.code == 429:
                fail('cost_center_authority_unavailable', 503)
            fail('cost_center_authority_denied', 401 if exc.code == 401 else 403)
        except (OSError, KeyError, ValueError, TypeError):
            fail('cost_center_authority_unavailable', 503)

    def session(self, tenant, authorization, actor):
        return self.call('/v1/session/context', tenant, authorization, actor)

    def code(self, tenant, authorization, actor, key):
        result = self.call('/v1/cost-center-codes/next', tenant, authorization, actor, {}, key)
        if not isinstance(result, dict) or result.get('mode') != 'managed' or (not isinstance(result.get('code'), str)) or (not result['code'].strip()):
            fail('cost_center_code_unavailable', 503)
        return result['code']

def get_admin_client(settings: Settings=Depends(get_settings)):
    return AdminClient(settings)

@dataclass(frozen=True)
class Access:
    tenant_id: str
    actor_id: str
    division_ids: tuple[str, ...]
    all_divisions: bool
    active_divisions: tuple[str, ...]
    authorization: str | None = None

    def require_division(self, id_, active=False):
        if not self.all_divisions and id_ not in self.division_ids or (active and id_ not in self.active_divisions):
            fail('cost_center_division_denied', 403, 'division_ref_id')

def resolve_access(context, tenant, permission, authorization=None):
    if not isinstance(context, dict):
        fail('cost_center_authority_unavailable', 503)
    for field in ('tenant', 'user', 'scope', 'capabilities'):
        if not isinstance(context.get(field), dict):
            fail('cost_center_authority_unavailable', 503)
    for field in ('active_modules', 'permissions'):
        if not isinstance(context.get(field), list) or not all((isinstance(item, str) for item in context[field])):
            fail('cost_center_authority_unavailable', 503)
    if not isinstance(context['capabilities'].get('cost_center_catalog'), dict):
        fail('cost_center_authority_unavailable', 503)
    identity = context.get('tenant') or {}
    user = context.get('user') or {}
    scope = context.get('scope') or {}
    if identity.get('id') != tenant or identity.get('status') != 'active' or user.get('status') != 'active' or (not user.get('id')):
        fail('tenant_access_denied')
    if 'admin' not in context.get('active_modules', []) or (context.get('capabilities', {}).get('cost_center_catalog') or {}).get('available') is not True:
        fail('module_not_enabled')
    if permission not in context.get('permissions', []):
        fail('permission_denied')
    if scope.get('version') != 2:
        fail('organization_scope_review_required', 409)
    ids = scope.get('division_ids', [])
    rows = scope.get('divisions', [])
    if not isinstance(ids, list) or not all((isinstance(id_, str) for id_ in ids)) or (not isinstance(rows, list)):
        fail('cost_center_authority_unavailable', 503)
    active = tuple((row['id'] for row in rows if isinstance(row, dict) and isinstance(row.get('id'), str)))
    return Access(tenant, user['id'], tuple(ids), scope.get('all_divisions') is True, active, authorization)

def require_cost_center_access(permission):

    def dependency(x_tenant_id: str | None=Header(None, alias='X-Tenant-Id'), authorization: str | None=Header(None, alias='Authorization'), x_actor_id: str | None=Header(None, alias='X-Actor-Id'), settings: Settings=Depends(get_settings), client: AdminClient=Depends(get_admin_client)):
        if not x_tenant_id:
            fail('tenant_required', 400)
        if not settings.cost_center_catalog_enabled:
            fail('module_not_enabled')
        if settings.auth_mode == 'firebase' and (not authorization or not authorization.lower().startswith('bearer ')):
            fail('auth_required', 401)
        return resolve_access(client.session(x_tenant_id, authorization, x_actor_id), x_tenant_id, permission, authorization)
    return dependency
