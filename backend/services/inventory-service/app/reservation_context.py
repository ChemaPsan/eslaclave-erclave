"""Inventory validates source context over HTTP and owns reservation snapshots."""
from urllib.parse import quote, urlencode, urlparse
from urllib import request, error
from decimal import Decimal, InvalidOperation
import json
from erclave_common.transport import open_dependency
from sqlalchemy import text
from pydantic import ValidationError
from fastapi import Depends
from erclave_common.config import Settings, get_settings
from erclave_common.organization_client import OrganizationClient, resolve_organization_access, deny
from erclave_common.operational_context import OperationalContext, society_currency

class ReservationContextClient:
    def __init__(self, settings):
        self.client = OrganizationClient(settings)
        self.sales = settings.sales_service_url.rstrip("/")
        self.production = settings.production_service_url.rstrip("/")
        self.maintenance = settings.maintenance_service_url.rstrip("/")
        self.purchasing = settings.purchasing_service_url.rstrip("/")
        self.environment = settings.environment

    def sales_context(self, tenant, source, authorization, actor, payload=None):
        if self.environment != "local":
            url=urlparse(self.sales)
            if url.scheme!="https" or not url.hostname or url.hostname.lower() in ("localhost","127.0.0.1","::1") or url.username or url.password or url.query or url.fragment:
                deny("assignment_authority_unavailable",503)
        value = self.client.get(self.sales, "/v1/sales/orders/" + quote(source.id, safe="") + "/execution-context?" + urlencode({"line_id": source.line_id or ""}), tenant, authorization, actor)
        if "organization_context" not in value or value.get("order_id") != source.id or value.get("order_line_id") != source.line_id:
            deny("assignment_authority_unavailable", 503)
        allocation=value.get("allocation")
        if allocation is not None:
            try:
                valid=payload is not None and allocation.get("line_id")==source.line_id and allocation.get("inventory_item_id")==payload.inventory_item_id and allocation.get("warehouse_id")==payload.warehouse_id and allocation.get("unit")==payload.unit and Decimal(str(allocation["quantity"]))==Decimal(str(payload.quantity))
            except (KeyError,TypeError,ValueError,InvalidOperation):valid=False
            if not valid:deny("operational_context_mismatch",422)
        context = value["organization_context"]
        try:
            return OperationalContext.model_validate(context) if context is not None else None
        except ValidationError:
            deny("assignment_authority_unavailable",503)

    def production_context(self, tenant, payload, authorization, actor):
        """Resolve the durable preparation, never trust context supplied by a caller."""
        if self.environment != "local":
            url = urlparse(self.production)
            if url.scheme != "https" or not url.hostname or url.hostname.lower() in ("localhost", "127.0.0.1", "::1") or url.username or url.password or url.query or url.fragment:
                deny("assignment_authority_unavailable", 503)
        if not payload.source.line_id:
            deny("operational_context_mismatch", 422)
        path = "/v1/production/orders/" + quote(payload.source.id, safe="") + "/reservation-context?" + urlencode({"line_id": payload.source.line_id})
        req = request.Request(self.production + path, headers={"X-Tenant-Id": tenant, "Authorization": authorization or "", "X-Actor-Id": actor or ""})
        try:
            with open_dependency(req, timeout=self.client.timeout, opener=request.urlopen) as response:
                proof = json.loads(response.read())["data"]
        except error.HTTPError as exc:
            deny("assignment_authority_denied" if exc.code in (401, 403) else "production_creation_attempt_failed" if exc.code == 409 else "assignment_authority_unavailable", 403 if exc.code in (401, 403) else 409 if exc.code == 409 else 503)
        except (OSError, ValueError, KeyError, TypeError):
            deny("assignment_authority_unavailable", 503)
        return validate_production_proof(proof, payload)

    def division_context(self, tenant, division_id, permission, authorization, actor):
        access = self.access(tenant, permission, authorization, actor)
        division = access.division(division_id)
        return OperationalContext(division_ref_id=division_id, society_ref_id=division["society_id"], division_code=division["code"], division_name=division["name"], cost_currency=society_currency(access, division["society_id"]))

    def warehouse_context(self, repository, tenant, warehouse_id, permission, authorization, actor):
        division_id=repository.warehouse_dimension(tenant,warehouse_id)
        if not division_id:return None
        access=self.access(tenant,permission,authorization,actor)
        division=access.division(division_id)
        return OperationalContext(division_ref_id=division_id,society_ref_id=division['society_id'],division_code=division['code'],division_name=division['name'],cost_currency=society_currency(access,division['society_id']))

    def access(self, tenant, permission, authorization, actor):
        return resolve_organization_access(self.client.session(tenant, authorization, actor), tenant, "inventory", permission, authorization)


def get_reservation_context_client(settings: Settings = Depends(get_settings)):
    return ReservationContextClient(settings)


def validate_local_context(connection, tenant, payload, context):
    """Use the same master -> assignment lock order as assignment writes."""
    warehouse = connection.execute(text("select division_ref_id from inventory.warehouses where tenant_id=:t and id=:id for share"), {"t": tenant, "id": payload.warehouse_id}).mappings().first()
    if not warehouse:
        return
    division = warehouse["division_ref_id"]
    if context is None:
        if division:
            deny("operational_context_required", 409)
        return
    if division != context.division_ref_id:
        deny("operational_context_mismatch", 422, "warehouse_id")
    item = connection.execute(text("select status from inventory.items where tenant_id=:t and id=:id for share"), {"t": tenant, "id": payload.inventory_item_id}).mappings().first()
    assignment = connection.execute(text("select status from inventory.item_division_assignments where tenant_id=:t and item_id=:id and division_ref_id=:d for share"), {"t": tenant, "id": payload.inventory_item_id, "d": division}).mappings().first()
    if not item or item["status"] != "active" or not assignment or assignment["status"] != "active":
        deny("operational_context_resource_unavailable", 422, "inventory_item_id")

def read_divisions(repository, client, tenant, permission, authorization, actor=None):
    if not hasattr(repository, "has_scoped_warehouses") or not repository.has_scoped_warehouses(tenant):
        return None
    access = client.access(tenant, permission, authorization, actor)
    return None if access.all_divisions else [row["id"] for row in access.divisions]


def validate_cost_currency(connection, tenant, item, warehouse, context):
    if not context or not context.cost_currency:return
    incompatible=connection.execute(text("select 1 from inventory.movements where tenant_id=:t and inventory_item_id=:item and warehouse_id=:wh and (organization_context->>'cost_currency') is distinct from :currency limit 1"),{'t':tenant,'item':item,'wh':warehouse,'currency':context.cost_currency}).first()
    if incompatible:deny('operational_cost_history_review_required',409)


def validate_production_proof(proof, payload):
    # Explicit null is the legacy contract, not a dependency failure.
    if proof is None:
        return None
    if not isinstance(proof, dict) or not isinstance(proof.get("allocation"), dict):
        deny("assignment_authority_unavailable", 503)
    allocation = proof["allocation"]
    try:
        context = OperationalContext.model_validate(proof["organization_context"])
        quantity = Decimal(str(allocation["quantity"]))
    except (ValidationError, KeyError, ValueError, TypeError, InvalidOperation):
        deny("assignment_authority_unavailable", 503)
    if not context.cost_currency:
        deny("operational_cost_currency_unavailable", 409)
    if (proof.get("order_id") != payload.source.id or allocation.get("line_id") != payload.source.line_id
        or allocation.get("inventory_item_id") != payload.inventory_item_id
        or allocation.get("warehouse_id") != payload.warehouse_id or allocation.get("unit") != payload.unit
        or not quantity.is_finite() or quantity <= 0 or quantity != Decimal(str(payload.quantity))):
        deny("operational_context_mismatch", 422)
    return context
