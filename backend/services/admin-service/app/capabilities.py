"""Server-owned capability availability. This is not an authorization token.

Catalog preparation does not enable analytical Costing or Accounting. Future
services must validate current tenant state, action permission and scope again.
"""
from .seeds.catalog import get_module_seed

# Capability implementation is independent from a module's commercial status.
# Do not flip a planned capability until its complete vertical cut is delivered.
CAPABILITIES = {
    "organization": ("admin-service", "admin", True),
    "cost_center_catalog": ("costing-service", "admin", True),
    "costing_analytics": ("costing-service", "costing", False),
    "accounting": ("accounting-service", "accounting", False),
}


def capability_availability(context, *, catalog_enabled=False):
    result = {}
    for code, (owner, module_code, implemented) in CAPABILITIES.items():
        module = get_module_seed(module_code)
        implemented = implemented and module is not None and module.implementation_status == "implemented"
        entitlements = [item for item in context.entitlements if item.module_code == module_code]
        # Conflicting duplicate records fail closed. Never trust active_modules
        # alone, or a role name, to establish entitlement availability.
        enabled = len(entitlements) == 1 and entitlements[0].status == "active" and entitlements[0].tenant_enabled
        if code == "cost_center_catalog":
            enabled = enabled and catalog_enabled
        active_identity = context.tenant.status == "active" and context.user.status == "active"
        reason = ("not_implemented" if not implemented else "identity_inactive" if not active_identity
                  else "module_inactive" if not enabled else "available")
        result[code] = {"owner_service": owner, "availability_module": module_code,
                        "implemented": bool(implemented), "available": reason == "available", "reason": reason}
    return result


def enrich_capabilities(context, *, catalog_enabled=False):
    # Recompute on each session response; client input cannot enable a feature.
    return type(context).model_validate({**context.model_dump(),
        "capability_policy_version": 1,
        "capabilities": capability_availability(context, catalog_enabled=catalog_enabled),
        "cost_center_requirement": "enabled_imputation_flows",
    })
