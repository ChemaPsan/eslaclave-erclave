"""Transport-only organizational snapshot shared by operational owners."""
from pydantic import BaseModel, ConfigDict, Field
from erclave_common.organization_client import deny

class OperationalContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cost_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    division_ref_id: str = Field(min_length=1, max_length=40)
    society_ref_id: str = Field(min_length=1, max_length=40)
    division_code: str = Field(min_length=1, max_length=120)
    division_name: str = Field(min_length=1, max_length=240)

    def authorize(self, access, *, active=True):
        division = access.division(self.division_ref_id, active=active)
        if active and division["society_id"] != self.society_ref_id:
            deny("operational_context_mismatch", 409)
        return self


def society_currency(access, society_id):
    society=next((row for row in access.societies if row.get("id")==society_id),None)
    currency=society.get("base_currency") if society else None
    if not isinstance(currency,str) or len(currency)!=3 or not currency.isascii() or not currency.isalpha() or currency!=currency.upper():
        deny("operational_cost_currency_unavailable",409)
    return currency
