import hashlib
import json
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from erclave_common.organization_client import deny
from .commercial_terms_schemas import CommercialTerms, CommercialTermsRead

class CommercialTermsStore:
    def __init__(self, repository):
        self.repository = repository

    def _assignment(self, conn, access, resource, division, lock=False):
        params = {'t': access.tenant_id, 'i': resource, 'd': division}
        # Lock order matches assignment writes: master, then its assignment.
        master = conn.execute(text('select status from purchasing.suppliers where tenant_id=:t and id=:i' + (' for update' if lock else '')), params).mappings().first()
        if not master:
            deny('assignment_resource_not_found', 404)
        assignment = conn.execute(text('select * from purchasing.supplier_division_assignments where tenant_id=:t and supplier_id=:i and division_ref_id=:d' + (' for update' if lock else '')), params).mappings().first()
        if not assignment:
            deny('assignment_resource_not_found', 404)
        return master, assignment

    def _read(self, conn, access, resource, division, master, assignment):
        row = conn.execute(text('select * from purchasing.supplier_division_terms where tenant_id=:t and supplier_id=:i and division_ref_id=:d'), {'t': access.tenant_id, 'i': resource, 'd': division}).mappings().first()
        organization = access.division(division, active=False)
        society = organization['society_id'] if organization else None
        return CommercialTermsRead(resource_id=resource, division_ref_id=division,
            confirmed_society_ref_id=row['society_ref_id'] if row else None,
            current_society_ref_id=society, revision=row['revision'] if row else 0,
            values=CommercialTerms.model_validate({field: row[field] for field in CommercialTerms.model_fields}) if row else None,
            requires_confirmation=not row or row['society_ref_id'] != society,
            assignment_active=bool(organization and master['status']=='active' and assignment['status']=='active' and assignment['society_ref_id']==society))

    def read(self, access, resource, division):
        access.division(division, active=False)
        with self.repository.engine.connect() as conn:
            master, assignment = self._assignment(conn, access, resource, division)
            return self._read(conn, access, resource, division, master, assignment).model_dump(mode='json')

    def save(self, access, resource, division, payload, key, correlation, authority):
        organization = access.division(division)
        operation = f'commercial_terms.supplier:{resource}:{division}'
        digest = hashlib.sha256(json.dumps({'actor':access.actor_id,'payload':payload.model_dump(mode='json')}, sort_keys=True).encode()).hexdigest()
        with self.repository.engine.begin() as conn:
            master, assignment = self._assignment(conn, access, resource, division, lock=True)
            if master['status'] != 'active' or assignment['status'] != 'active':
                deny('assignment_resource_inactive', 409)
            if assignment['society_ref_id'] != organization['society_id']:
                deny('assignment_division_denied', 409, 'division_ref_id')
            try:
                replay = self.repository._claim(conn, access.tenant_id, operation, key, digest)
            except ValueError as exc:
                deny(str(exc), 409)
            if replay:
                return replay
            before = self._read(conn, access, resource, division, master, assignment)
            if payload.expected_revision != before.revision:
                deny('assignment_revision_conflict', 409)
            for field, catalog in [('currency','currencies'),('payment_terms','payment_terms')]:
                try:
                    authority.require_catalog(access.tenant_id, catalog, getattr(payload.values,field), access.authorization)
                except ErclaveError as exc:
                    if exc.status_code == 422:
                        raise ErclaveError('catalog_item_not_found', 'An active catalog code is required.', 422, {'issues':[{'loc':['body','values',field], 'code':'catalog_item_not_found'}]}) from exc
                    raise
            values = payload.values.model_dump(mode='json')
            params = {'t':access.tenant_id,'i':resource,'d':division,'s':organization['society_id'],'r':before.revision+1,**values}
            conn.execute(text('insert into purchasing.supplier_division_terms(tenant_id,supplier_id,division_ref_id,society_ref_id,revision,currency,payment_terms,lead_time_days) values(:t,:i,:d,:s,:r,:currency,:payment_terms,:lead_time_days) on conflict(tenant_id,supplier_id,division_ref_id) do update set society_ref_id=excluded.society_ref_id,revision=excluded.revision,currency=excluded.currency,payment_terms=excluded.payment_terms,lead_time_days=excluded.lead_time_days,updated_at=now()'), params)
            result = self._read(conn, access, resource, division, master, assignment)
            self.repository._audit(conn, access.tenant_id, access.actor_id, 'commercial_terms.supplier', 'supplier', resource, {'before':before.model_dump(mode='json'),'after':result.model_dump(mode='json'),'correlation_id':correlation,'idempotency_key':key})
            self.repository._finish(conn, access.tenant_id, operation, key, result.model_dump(mode='json'))
            return result.model_dump(mode='json')
