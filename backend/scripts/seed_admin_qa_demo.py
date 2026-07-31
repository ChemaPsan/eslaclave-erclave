from __future__ import annotations

import argparse
import json
import os
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine, text


DEFAULT_TENANT_SLUG = "demo-qa"
DEFAULT_TENANT_NAME = "ERClave Demo QA"
DEFAULT_ADMIN_EMAIL = "admin.qa@erclave.local"
DEFAULT_ADMIN_NAME = "Admin QA ERClave"
ACTIVE_DEMO_MODULES = ("admin", "production", "inventory", "sales", "integrations")
DEFAULT_EXTRA_OWNER_EMAILS = ("eslaclavecaf@gmail.com",)


def stable_id(prefix: str, natural_key: str) -> str:
    return f"{prefix}_{uuid5(NAMESPACE_URL, f'erclave.{prefix}:{natural_key}').hex[:26]}"


def demo_ids(tenant_slug: str, admin_email: str) -> dict[str, str]:
    tenant_id = stable_id("ten", tenant_slug)
    user_id = stable_id("usr", admin_email.lower())
    role_id = stable_id("rol", f"{tenant_slug}:owner")
    membership_id = stable_id("mem", f"{tenant_slug}:{admin_email.lower()}")
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "role_id": role_id,
        "membership_id": membership_id,
    }


def default_organization_profile(tenant_name: str) -> dict:
    return {
        "corporate": {
            "commercial_name": tenant_name,
            "legal_name": tenant_name,
            "tax_id": "",
            "phone": "",
            "contact_name": "",
            "contact_email": "",
            "contact_phone": "",
            "contact_position": "",
        },
        "legal_entities": [],
        "branches": [],
    }


def apply_demo_seed(
    database_url: str,
    tenant_slug: str,
    tenant_name: str,
    admin_email: str,
    admin_name: str,
    extra_owner_emails: tuple[str, ...] = DEFAULT_EXTRA_OWNER_EMAILS,
) -> dict[str, int | str]:
    ids = demo_ids(tenant_slug, admin_email)
    engine = create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                insert into admin.tenants (
                    id,
                    slug,
                    legal_name,
                    commercial_name,
                    status,
                    plan_id,
                    timezone,
                    locale,
                    source_type,
                    source_id,
                    metadata
                )
                values (
                    :tenant_id,
                    :tenant_slug,
                    :tenant_name,
                    :tenant_name,
                    'active',
                    'qa-demo',
                    'America/Mexico_City',
                    'es-MX',
                    'seed',
                    'seed_admin_qa_demo',
                    '{"seed": "qa-demo"}'::jsonb
                )
                on conflict (slug) do update set
                    legal_name = excluded.legal_name,
                    commercial_name = excluded.commercial_name,
                    status = excluded.status,
                    plan_id = excluded.plan_id,
                    timezone = excluded.timezone,
                    locale = excluded.locale,
                    source_type = excluded.source_type,
                    source_id = excluded.source_id,
                    metadata = excluded.metadata,
                    updated_at = now()
                """
            ),
            {
                "tenant_id": ids["tenant_id"],
                "tenant_slug": tenant_slug,
                "tenant_name": tenant_name,
            },
        )

        connection.execute(
            text(
                """
                insert into admin.tenant_settings (
                    id,
                    tenant_id,
                    key,
                    module_code,
                    value
                )
                values (
                    :setting_id,
                    :tenant_id,
                    'organization.profile',
                    'admin',
                    cast(:value as jsonb)
                )
                on conflict (tenant_id, key) do update set
                    module_code = excluded.module_code,
                    value = case
                        when admin.tenant_settings.value = '{}'::jsonb then excluded.value
                        else admin.tenant_settings.value
                    end,
                    updated_at = now()
                """
            ),
            {
                "setting_id": stable_id("set", f"{ids['tenant_id']}:organization.profile"),
                "tenant_id": ids["tenant_id"],
                "value": json.dumps(default_organization_profile(tenant_name)),
            },
        )

        connection.execute(
            text(
                """
                insert into admin.users (
                    id,
                    identity_provider_id,
                    email,
                    display_name,
                    status,
                    metadata
                )
                values (
                    :user_id,
                    null,
                    :admin_email,
                    :admin_name,
                    'active',
                    '{"seed": "qa-demo"}'::jsonb
                )
                on conflict (email) do update set
                    display_name = excluded.display_name,
                    status = excluded.status,
                    metadata = excluded.metadata,
                    updated_at = now()
                """
            ),
            {
                "user_id": ids["user_id"],
                "admin_email": admin_email.lower(),
                "admin_name": admin_name,
            },
        )

        connection.execute(
            text(
                """
                insert into admin.roles (
                    id,
                    tenant_id,
                    code,
                    name,
                    description,
                    status,
                    system_role
                )
                values (
                    :role_id,
                    :tenant_id,
                    'owner',
                    'Owner',
                    'Rol owner seed QA con permisos MVP.',
                    'active',
                    true
                )
                on conflict (tenant_id, code) do update set
                    name = excluded.name,
                    description = excluded.description,
                    status = excluded.status,
                    system_role = excluded.system_role,
                    updated_at = now()
                """
            ),
            ids,
        )

        connection.execute(
            text(
                """
                insert into admin.memberships (
                    id,
                    tenant_id,
                    user_id,
                    status,
                    invited_at,
                    activated_at,
                    metadata
                )
                values (
                    :membership_id,
                    :tenant_id,
                    :user_id,
                    'active',
                    now(),
                    now(),
                    '{"seed": "qa-demo"}'::jsonb
                )
                on conflict (tenant_id, user_id) do update set
                    status = excluded.status,
                    activated_at = coalesce(admin.memberships.activated_at, excluded.activated_at),
                    metadata = excluded.metadata,
                    updated_at = now()
                """
            ),
            ids,
        )

        module_rows = [
            {
                "tenant_module_id": stable_id("tmo", f"{ids['tenant_id']}:{module_code}"),
                "tenant_id": ids["tenant_id"],
                "module_code": module_code,
            }
            for module_code in ACTIVE_DEMO_MODULES
        ]
        connection.execute(
            text(
                """
                insert into admin.tenant_modules (
                    id,
                    tenant_id,
                    module_code,
                    status,
                    source,
                    starts_at,
                    limits
                )
                values (
                    :tenant_module_id,
                    :tenant_id,
                    :module_code,
                    'active',
                    'seed',
                    now(),
                    '{"seed": "qa-demo"}'::jsonb
                )
                on conflict (tenant_id, module_code) do update set
                    status = excluded.status,
                    source = excluded.source,
                    starts_at = coalesce(admin.tenant_modules.starts_at, excluded.starts_at),
                    limits = excluded.limits,
                    updated_at = now()
                """
            ),
            module_rows,
        )

        role_permission_count = connection.execute(
            text(
                """
                insert into admin.role_permissions (
                    id,
                    tenant_id,
                    role_id,
                    permission_id,
                    scope
                )
                select
                    concat('rpe_', left(md5(:tenant_id || ':' || :role_id || ':' || permissions.id), 26)),
                    :tenant_id,
                    :role_id,
                    permissions.id,
                    '{"seed": "qa-demo"}'::jsonb
                from admin.permissions permissions
                where permissions.status = 'active'
                    and permissions.classification = 'tenant'
                    and permissions.assignable_to_tenant_role = true
                    and (
                        permissions.module_code = 'admin'
                        or exists (
                            select 1
                            from admin.tenant_modules tenant_modules
                            where tenant_modules.tenant_id = :tenant_id
                                and tenant_modules.module_code = permissions.module_code
                                and tenant_modules.status = 'active'
                        )
                    )
                on conflict (tenant_id, role_id, permission_id) do nothing
                """
            ),
            ids,
        ).rowcount

        membership_role_count = connection.execute(
            text(
                """
                insert into admin.membership_roles (
                    id,
                    tenant_id,
                    membership_id,
                    role_id
                )
                values (
                    :membership_role_id,
                    :tenant_id,
                    :membership_id,
                    :role_id
                )
                on conflict (tenant_id, membership_id, role_id) do nothing
                """
            ),
            {
                **ids,
                "membership_role_id": stable_id("mro", f"{ids['membership_id']}:{ids['role_id']}"),
            },
        ).rowcount

        for owner_email in extra_owner_emails:
            owner_email = owner_email.lower().strip()
            if not owner_email or owner_email == admin_email.lower():
                continue
            owner_user_id = stable_id("usr", owner_email)
            owner_membership_id = stable_id("mem", f"{tenant_slug}:{owner_email}")
            connection.execute(
                text(
                    """
                    insert into admin.users (id, identity_provider_id, email, display_name, status, metadata)
                    values (:user_id, null, :email, :display_name, 'active', '{"seed": "qa-demo-firebase"}'::jsonb)
                    on conflict (email) do update set
                        display_name = excluded.display_name,
                        status = excluded.status,
                        metadata = excluded.metadata,
                        updated_at = now()
                    """
                ),
                {"user_id": owner_user_id, "email": owner_email, "display_name": "ERClave QA"},
            )
            connection.execute(
                text(
                    """
                    insert into admin.memberships (id, tenant_id, user_id, status, invited_at, activated_at, metadata)
                    values (:membership_id, :tenant_id, :user_id, 'active', now(), now(), '{"seed": "qa-demo-firebase"}'::jsonb)
                    on conflict (tenant_id, user_id) do update set
                        status = excluded.status,
                        activated_at = coalesce(admin.memberships.activated_at, excluded.activated_at),
                        metadata = excluded.metadata,
                        updated_at = now()
                    """
                ),
                {"membership_id": owner_membership_id, "tenant_id": ids["tenant_id"], "user_id": owner_user_id},
            )
            connection.execute(
                text(
                    """
                    insert into admin.membership_roles (id, tenant_id, membership_id, role_id)
                    values (:membership_role_id, :tenant_id, :membership_id, :role_id)
                    on conflict (tenant_id, membership_id, role_id) do nothing
                    """
                ),
                {
                    "membership_role_id": stable_id("mro", f"{owner_membership_id}:{ids['role_id']}"),
                    "tenant_id": ids["tenant_id"],
                    "membership_id": owner_membership_id,
                    "role_id": ids["role_id"],
                },
            )

        permission_count = connection.execute(text("select count(*) from admin.permissions")).scalar_one()

    return {
        **ids,
        "tenant_slug": tenant_slug,
        "admin_email": admin_email.lower(),
        "active_modules": len(ACTIVE_DEMO_MODULES),
        "available_permissions": permission_count,
        "role_permissions_inserted": role_permission_count,
        "membership_roles_inserted": membership_role_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply idempotent QA demo tenant seed.")
    parser.add_argument("--tenant-slug", default=DEFAULT_TENANT_SLUG)
    parser.add_argument("--tenant-name", default=DEFAULT_TENANT_NAME)
    parser.add_argument("--admin-email", default=DEFAULT_ADMIN_EMAIL)
    parser.add_argument("--admin-name", default=DEFAULT_ADMIN_NAME)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the deterministic records without writing to PostgreSQL.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ids = demo_ids(args.tenant_slug, args.admin_email)

    if args.dry_run:
        print(f"Tenant {args.tenant_slug}: {ids['tenant_id']}")
        print(f"Admin user {args.admin_email.lower()}: {ids['user_id']}")
        print(f"Owner role: {ids['role_id']}")
        print(f"Active modules: {', '.join(ACTIVE_DEMO_MODULES)}")
        return 0

    database_url = os.getenv("ERCLAVE_DATABASE_URL")
    if not database_url:
        raise RuntimeError("ERCLAVE_DATABASE_URL is required to apply QA demo seeds.")

    result = apply_demo_seed(
        database_url=database_url,
        tenant_slug=args.tenant_slug,
        tenant_name=args.tenant_name,
        admin_email=args.admin_email,
        admin_name=args.admin_name,
    )
    print(
        "Applied QA demo seed: "
        f"tenant={result['tenant_slug']} "
        f"admin={result['admin_email']} "
        f"modules={result['active_modules']} "
        f"permissions={result['available_permissions']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
