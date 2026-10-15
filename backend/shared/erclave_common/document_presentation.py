"""Transport contract for a document's immutable presentation snapshot."""
from pydantic import BaseModel, ConfigDict, Field
from urllib.parse import quote
from typing import Literal
from erclave_common.config import get_settings
from erclave_common.organization_client import OrganizationClient, deny


class DocumentTemplateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    logo_data_url: str | None = None
    primary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    text_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    footer_text: str | None = None
    show_page_number: bool


class DocumentPresentationSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
    template: DocumentTemplateSnapshot


def resolve_document_presentation(tenant_id, division_id, society_id, authorization, actor_id):
    client = OrganizationClient(get_settings())
    value = client.get(client.admin, "/v1/configuration/document-presentation/division/" + quote(division_id, safe=""),
                       tenant_id, authorization, actor_id)
    try:
        snapshot = DocumentPresentationSnapshot.model_validate(value)
    except ValueError:
        deny("assignment_authority_unavailable", 503)
    if snapshot.division_ref_id != division_id or snapshot.society_ref_id != society_id:
        deny("operational_context_mismatch", 409)
    return snapshot
