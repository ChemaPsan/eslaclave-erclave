"""CONT-04 pilot: entire-template override; null restores inheritance."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from erclave_common.errors import ErclaveError
from .models import ScopedSetting, TenantSetting, Society, Division, FiscalIssuer
from .organization_store import lock_organization, authority
from .schemas import DocumentTemplateRead

ScopeKind = Literal["society", "division"]
KEY = "document.template"


class ScopedTemplateValue(DocumentTemplateRead):
    model_config = ConfigDict(extra="forbid")


class ScopedTemplateCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    value: ScopedTemplateValue | None


class ScopedTemplateRead(BaseModel):
    scope_type: ScopeKind
    scope_id: str
    revision: int
    override: bool
    resolved_from_scope: Literal["corporate", "society", "division"]
    resolved_from_id: str
    value: DocumentTemplateRead


class ScopedTemplateResponse(BaseModel):
    data: ScopedTemplateRead


class DocumentPresentationRead(BaseModel):
    division_ref_id: str
    division_code: str
    division_name: str
    society_ref_id: str
    society_code: str
    society_name: str
    issuer_ref_id: str
    issuer_code: str
    issuer_legal_name: str
    issuer_tax_id: str | None = None
    issuer_fiscal_address: str | None = None
    issuer_postal_code: str | None = None
    issuer_country_code: str | None = None
    template_origin: Literal["corporate", "society", "division"]
    template_origin_id: str
    template: DocumentTemplateRead


class DocumentPresentationResponse(BaseModel):
    data: DocumentPresentationRead


def fail(code, status=409):
    raise ErclaveError(code, "Scoped configuration could not be resolved.", status)


def authorize_scope(context, kind, scope_id):
    if context is None or context.tenant.status != "active" or context.user.status != "active":
        fail("organization_scope_denied", 403)
    if context.scope.version != 2:
        fail("organization_scope_review_required", 409)
    # Society overrides affect all its divisions; restricted users cannot change
    # configuration for divisions outside their grant through the parent.
    if context.scope.all_divisions:
        return
    if kind != "division" or scope_id not in context.scope.division_ids:
        fail("organization_scope_denied", 403)


class ScopedConfigurationStore:
    def __init__(self, repository):
        self.repository = repository

    def target(self, connection, tenant, kind, scope_id):
        if not authority(connection, tenant):
            fail("organization_scope_review_required")
        model = Society if kind == "society" else Division
        target = connection.execute(select(model.__table__).where(model.tenant_id == tenant, model.id == scope_id)).mappings().first()
        if not target:
            fail("organization_scope_reference_invalid", 404)
        society = target if kind == "society" else connection.execute(select(Society.__table__).where(
            Society.tenant_id == tenant, Society.id == target["society_id"])).mappings().first()
        issuer = connection.execute(select(FiscalIssuer.__table__).where(FiscalIssuer.tenant_id == tenant,
            FiscalIssuer.id == society["issuer_id"])).mappings().first() if society else None
        if any(row is None or row["status"] != "active" for row in (target, society, issuer)):
            fail("organization_scope_reference_invalid", 422)
        return society["id"]

    def read_in(self, connection, tenant, kind, scope_id):
        society_id = self.target(connection, tenant, kind, scope_id)
        corporate = connection.execute(select(TenantSetting.value).where(
            TenantSetting.tenant_id == tenant, TenantSetting.key == KEY)).scalar_one_or_none() or {}
        value = DocumentTemplateRead.model_validate(corporate).model_dump(mode="json")
        origin, origin_id, revision, override = "corporate", tenant, 0, False
        levels = [("society", society_id)] + ([("division", scope_id)] if kind == "division" else [])
        for level, reference in levels:
            row = connection.execute(select(ScopedSetting.__table__).where(ScopedSetting.tenant_id == tenant,
                ScopedSetting.key == KEY, ScopedSetting.scope_type == level, ScopedSetting.scope_ref_id == reference)).mappings().first()
            if row and row["value"] is not None:
                value = DocumentTemplateRead.model_validate(row["value"]).model_dump(mode="json")
                origin, origin_id = level, reference
            if level == kind and row:
                revision, override = row["revision"], row["value"] is not None
        return dict(scope_type=kind, scope_id=scope_id, revision=revision, override=override,
                    resolved_from_scope=origin, resolved_from_id=origin_id, value=value)

    def read(self, tenant, kind, scope_id):
        with self.repository.engine.begin() as connection:
            lock_organization(connection, tenant)
            return self.read_in(connection, tenant, kind, scope_id)

    def presentation(self, tenant, division_id):
        with self.repository.engine.begin() as connection:
            lock_organization(connection, tenant)
            resolved = self.read_in(connection, tenant, "division", division_id)
            division = connection.execute(select(Division.__table__).where(
                Division.tenant_id == tenant, Division.id == division_id)).mappings().one()
            society = connection.execute(select(Society.__table__).where(
                Society.tenant_id == tenant, Society.id == division["society_id"])).mappings().one()
            issuer = connection.execute(select(FiscalIssuer.__table__).where(
                FiscalIssuer.tenant_id == tenant, FiscalIssuer.id == society["issuer_id"])).mappings().one()
            return DocumentPresentationRead(
                division_ref_id=division["id"], division_code=division["code"], division_name=division["name"],
                society_ref_id=society["id"], society_code=society["code"], society_name=society["name"],
                issuer_ref_id=issuer["id"], issuer_code=issuer["code"], issuer_legal_name=issuer["legal_name"],
                issuer_tax_id=issuer["tax_id"], issuer_fiscal_address=issuer["fiscal_address"],
                issuer_postal_code=issuer["postal_code"], issuer_country_code=issuer["country_code"],
                template_origin=resolved["resolved_from_scope"], template_origin_id=resolved["resolved_from_id"],
                template=resolved["value"])

    def update(self, tenant, kind, scope_id, payload, key, correlation, actor_email):
        operation = "admin.configuration.document_template.update"
        with self.repository.engine.begin() as connection:
            lock_organization(connection, tenant)
            if actor_email:
                authorize_scope(self.repository.get_session_context_by_email(tenant, actor_email), kind, scope_id)
            self.target(connection, tenant, kind, scope_id)
            cached = self.repository._begin_idempotent_command(connection, tenant, operation, key,
                self.repository._command_request_hash({"scope_type": kind, "scope_id": scope_id, **payload}))
            if cached is not None:
                return cached
            before = self.read_in(connection, tenant, kind, scope_id)
            if payload["expected_revision"] != before["revision"]:
                fail("configuration_revision_conflict")
            value = DocumentTemplateRead.model_validate(payload["value"]).model_dump(mode="json") if payload["value"] is not None else None
            table = ScopedSetting.__table__
            conditions = (ScopedSetting.tenant_id == tenant, ScopedSetting.key == KEY,
                          ScopedSetting.scope_type == kind, ScopedSetting.scope_ref_id == scope_id)
            values = dict(value=value, revision=before["revision"] + 1)
            if before["revision"]:
                connection.execute(table.update().where(*conditions).values(**values))
            else:
                connection.execute(table.insert().values(tenant_id=tenant, key=KEY, scope_type=kind, scope_ref_id=scope_id, **values))
            result = self.read_in(connection, tenant, kind, scope_id)
            self.repository._record_audit_event(connection, tenant_id=tenant, action=operation, resource_type="scoped_setting",
                resource_id=scope_id, before_state=before, after_state=result, idempotency_key=key, correlation_id=correlation,
                metadata={"scope_type": kind}, actor_user_id=self.repository._actor_user_id(connection, actor_email))
            self.repository._complete_idempotent_command(connection, tenant, operation, key, result, 200)
            return result
