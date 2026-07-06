from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:26]}"


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            "status in ('provisioning', 'active', 'suspended', 'cancelled')",
            name="ck_tenants_status",
        ),
        Index("ix_tenants_status", "status"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("ten"))
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    legal_name: Mapped[str | None] = mapped_column(String(240))
    commercial_name: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="provisioning")
    plan_id: Mapped[str | None] = mapped_column(String(40))
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="America/Mexico_City")
    locale: Mapped[str] = mapped_column(String(20), nullable=False, default="es-MX")
    source_type: Mapped[str | None] = mapped_column(String(40))
    source_id: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )

    roles: Mapped[list["Role"]] = relationship(back_populates="tenant")
    memberships: Mapped[list["Membership"]] = relationship(back_populates="tenant")
    tenant_modules: Mapped[list["TenantModule"]] = relationship(back_populates="tenant")
    tenant_settings: Mapped[list["TenantSetting"]] = relationship(back_populates="tenant")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("status in ('invited', 'active', 'disabled')", name="ck_users_status"),
        Index("ix_users_status", "status"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("usr"))
    identity_provider_id: Mapped[str | None] = mapped_column(String(160), unique=True)
    email: Mapped[str] = mapped_column(String(240), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="invited")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_code"),
        CheckConstraint("status in ('active', 'inactive')", name="ck_roles_status"),
        Index("ix_roles_tenant_status", "tenant_id", "status"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("rol"))
    tenant_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    tenant: Mapped[Tenant] = relationship(back_populates="roles")
    permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role")
    membership_roles: Mapped[list["MembershipRole"]] = relationship(back_populates="role")


class Permission(TimestampMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = (
        CheckConstraint("status in ('active', 'inactive')", name="ck_permissions_status"),
        Index("ix_permissions_module_resource_action", "module_code", "resource", "action"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("per"))
    code: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    module_code: Mapped[str] = mapped_column(String(80), nullable=False)
    resource: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")

    roles: Mapped[list["RolePermission"]] = relationship(back_populates="permission")


class TenantModule(TimestampMixin, Base):
    __tablename__ = "tenant_modules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "module_code", name="uq_tenant_modules_tenant_module"),
        CheckConstraint("status in ('active', 'inactive', 'suspended')", name="ck_tenant_modules_status"),
        Index("ix_tenant_modules_tenant_status", "tenant_id", "status"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("tmo"))
    tenant_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    module_code: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="inactive")
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    limits_json: Mapped[dict] = mapped_column(
        "limits",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="tenant_modules")


class TenantSetting(TimestampMixin, Base):
    __tablename__ = "tenant_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_tenant_settings_tenant_key"),
        Index("ix_tenant_settings_tenant_module", "tenant_id", "module_code"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("set"))
    tenant_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(160), nullable=False)
    module_code: Mapped[str | None] = mapped_column(String(80))
    value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="tenant_settings")


class Membership(TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_user"),
        CheckConstraint("status in ('invited', 'active', 'disabled')", name="ck_memberships_status"),
        Index("ix_memberships_tenant_status", "tenant_id", "status"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("mem"))
    tenant_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="invited")
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")
    roles: Mapped[list["MembershipRole"]] = relationship(back_populates="membership")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "role_id", "permission_id", name="uq_role_permissions_role_permission"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("rpe"))
    tenant_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.permissions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scope: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    role: Mapped[Role] = relationship(back_populates="permissions")
    permission: Mapped[Permission] = relationship(back_populates="roles")


class MembershipRole(Base):
    __tablename__ = "membership_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "membership_id", "role_id", name="uq_membership_roles_membership_role"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("mro"))
    tenant_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    membership_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.memberships.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("admin.roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    membership: Mapped[Membership] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship(back_populates="membership_roles")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_tenant_occurred", "tenant_id", "occurred_at"),
        Index("ix_audit_events_resource", "resource_type", "resource_id"),
        Index("ix_audit_events_correlation", "correlation_id"),
        {"schema": "admin"},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("aud"))
    tenant_id: Mapped[str | None] = mapped_column(
        String(40),
        ForeignKey("admin.tenants.id", ondelete="RESTRICT"),
    )
    actor_user_id: Mapped[str | None] = mapped_column(
        String(40),
        ForeignKey("admin.users.id", ondelete="RESTRICT"),
    )
    actor_type: Mapped[str] = mapped_column(String(40), nullable=False)
    action: Mapped[str] = mapped_column(String(160), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(120))
    source_service: Mapped[str] = mapped_column(String(80), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(160))
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    before_state: Mapped[dict | None] = mapped_column(JSONB)
    after_state: Mapped[dict | None] = mapped_column(JSONB)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
