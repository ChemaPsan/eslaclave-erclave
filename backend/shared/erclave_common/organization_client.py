"""Organization authority over HTTP; consumers retain their own data ownership."""
from dataclasses import dataclass
import json
from urllib import request, error
from urllib.parse import quote, urlparse
from fastapi import Depends, Header
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError
from erclave_common.transport import open_dependency

def deny(code, status=403, field=None):
    raise ErclaveError(code, 'Organization assignment could not be completed.', status, {'field': field} if field else {})

@dataclass(frozen=True)
class OrganizationAccess:
    tenant_id: str
    actor_id: str
    permissions: tuple[str, ...]
    divisions: tuple[dict, ...]
    all_divisions: bool
    catalog_available: bool
    authorization: str | None = None
    societies: tuple[dict, ...] = ()

    def division(self, id_, active=True):
        row = next((row for row in self.divisions if row['id'] == id_), None)
        if row is None and (active or not self.all_divisions):
            deny('assignment_division_denied', 403, 'division_ref_id')
        return row

class OrganizationClient:

    def __init__(self, settings):
        self.environment = settings.environment
        self.admin = settings.admin_service_url.rstrip('/')
        self.costing = settings.costing_service_url.rstrip('/')
        self.timeout = settings.authorization_timeout_seconds

    def get(self, base, path, tenant, authorization, actor=None):
        req = request.Request(base + path, headers={'X-Tenant-Id': tenant, 'Authorization': authorization or '', 'X-Actor-Id': actor or ''})
        try:
            with open_dependency(req, timeout=self.timeout, opener=request.urlopen) as response:
                value = json.loads(response.read())['data']
            if not isinstance(value, dict):
                deny('assignment_authority_unavailable', 503)
            return value
        except error.HTTPError as exc:
            deny('assignment_reference_invalid' if exc.code == 404 else 'assignment_authority_denied' if exc.code in (401, 403) else 'assignment_authority_unavailable', 422 if exc.code == 404 else 403 if exc.code in (401, 403) else 503)
        except (OSError, ValueError, KeyError, TypeError):
            deny('assignment_authority_unavailable', 503)

    def session(self, tenant, authorization, actor):
        return self.get(self.admin, '/v1/session/context', tenant, authorization, actor)

    def center(self, access, id_, division_id):
        if not access.catalog_available:
            deny('module_not_enabled')
        if 'costing.cost_center.read' not in access.permissions:
            deny('permission_denied')
        if self.environment != 'local':
            parsed = urlparse(self.costing)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.hostname.lower() in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password or parsed.query or parsed.fragment:
                deny('assignment_authority_unavailable', 503)
        value = self.get(self.costing, '/v1/cost-centers/' + quote(id_, safe=''), access.tenant_id, access.authorization, access.actor_id)
        if value.get('id') != id_ or value.get('status') != 'active' or value.get('division_ref_id') != division_id:
            deny('assignment_center_invalid', 422, 'cost_center_ref_id')
        if not all((isinstance(value.get(key), str) and value[key] for key in ('code', 'name'))):
            deny('assignment_authority_unavailable', 503)
        return {key: value[key] for key in ('id', 'code', 'name')}

def get_organization_client(settings: Settings=Depends(get_settings)):
    return OrganizationClient(settings)

def resolve_organization_access(data, tenant, module, permissions, authorization=None):
    required = (permissions,) if isinstance(permissions, str) else permissions
    if not isinstance(data, dict) or not all((isinstance(data.get(k), dict) for k in ('tenant', 'user', 'scope', 'capabilities'))):
        deny('assignment_authority_unavailable', 503)
    if not all((isinstance(data.get(k), list) and all((isinstance(value, str) for value in data[k])) for k in ('active_modules', 'permissions'))):
        deny('assignment_authority_unavailable', 503)
    if data['tenant'].get('id') != tenant or data['tenant'].get('status') != 'active' or data['user'].get('status') != 'active' or (not isinstance(data['user'].get('id'), str)) or (not data['user']['id']):
        deny('tenant_access_denied')
    if 'admin' not in data['active_modules'] or module not in data['active_modules']:
        deny('module_not_enabled')
    if not any((code in data['permissions'] for code in required)):
        deny('permission_denied')
    if not any(code in data['permissions'] and code.split('.')[0] in data['active_modules'] for code in required):
        deny('module_not_enabled')
    scope = data['scope']
    if scope.get('version') != 2:
        deny('organization_scope_review_required', 409)
    divisions = scope.get('divisions')
    if not isinstance(divisions, list) or not all((isinstance(row, dict) and all((isinstance(row.get(k), str) for k in ('id', 'code', 'name', 'society_id'))) for row in divisions)):
        deny('assignment_authority_unavailable', 503)
    societies = scope.get('societies', [])
    if not isinstance(societies, list) or not all(isinstance(row, dict) for row in societies):
        deny('assignment_authority_unavailable', 503)
    capability = data['capabilities'].get('cost_center_catalog') or {}
    return OrganizationAccess(tenant, data['user']['id'], tuple(data['permissions']), tuple(divisions), scope.get('all_divisions') is True, isinstance(capability, dict) and capability.get('available') is True, authorization, tuple(societies))

def require_organization_access(module, permission):

    def dependency(x_tenant_id: str | None=Header(None, alias='X-Tenant-Id'), authorization: str | None=Header(None, alias='Authorization'), x_actor_id: str | None=Header(None, alias='X-Actor-Id'), settings: Settings=Depends(get_settings), client: OrganizationClient=Depends(get_organization_client)):
        if not x_tenant_id:
            deny('tenant_required', 400)
        if settings.auth_mode == 'firebase' and (not authorization or not authorization.lower().startswith('bearer ')):
            deny('auth_required', 401)
        return resolve_organization_access(client.session(x_tenant_id, authorization, x_actor_id), x_tenant_id, module, permission, authorization)
    return dependency
