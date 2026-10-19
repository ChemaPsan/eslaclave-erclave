import hashlib
import json
from sqlalchemy import text
from erclave_common.organization_client import deny
from .organization_schemas import AssignmentRead
class OrganizationStore:
    def __init__(self, repository):
        self.repository = repository
    def assignments(self, access, id_, limit, offset, division=None):
        if division: access.division(division, active=False)
        params={'t':access.tenant_id,'i':id_,'limit':limit,'offset':offset,'divisions':[row['id'] for row in access.divisions]}
        where='tenant_id=:t and supplier_id=:i'
        if not access.all_divisions: where+=' and division_ref_id=any(:divisions)'
        if division: where+=' and division_ref_id=:d';params['d']=division
        with self.repository.engine.connect() as conn:
            if not conn.execute(text('select id from purchasing.suppliers where tenant_id=:t and id=:i'),params).first(): deny('assignment_resource_not_found',404)
            total=conn.execute(text('select count(*) from purchasing.supplier_division_assignments where '+where),params).scalar_one()
            rows=conn.execute(text('select * from purchasing.supplier_division_assignments where '+where+' order by division_ref_id limit :limit offset :offset'),params).mappings().all()
        return {'data':[AssignmentRead.model_validate(dict(row)).model_dump() for row in rows],'meta':{'total':total,'limit':limit,'offset':offset}}
    def eligible(self,access,division,q,limit,offset):
        organization=access.division(division)
        query=q.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        join=" from purchasing.supplier_division_assignments a join purchasing.suppliers r on r.tenant_id=a.tenant_id and r.id=a.supplier_id where a.tenant_id=:t and a.division_ref_id=:d and a.society_ref_id=:s and a.status='active' and r.status='active' and (r.code ilike :q or r.commercial_name ilike :q)"
        params={'t':access.tenant_id,'d':division,'s':organization['society_id'],'q':'%'+query+'%','limit':limit,'offset':offset}
        with self.repository.engine.connect() as conn:
            total=conn.execute(text('select count(*)'+join),params).scalar_one()
            rows=conn.execute(text('select r.id,r.code,r.commercial_name name,a.division_ref_id,a.society_ref_id'+join+' order by r.code,r.id limit :limit offset :offset'),params).mappings().all()
        return {'data':[dict(row) for row in rows],'meta':{'total':total,'limit':limit,'offset':offset}}
    def save(self,access,id_,division,payload,key,correlation):
        organization=access.division(division,active=payload.status=='active')
        operation=f'org_assignment.supplier:{id_}:{division}'
        digest=hashlib.sha256(json.dumps({'actor':access.actor_id,'payload':payload.model_dump()},sort_keys=True).encode()).hexdigest()
        params={'t':access.tenant_id,'i':id_,'d':division}
        with self.repository.engine.begin() as conn:
            resource=conn.execute(text('select id,status from purchasing.suppliers where tenant_id=:t and id=:i for update'),params).mappings().first()
            if not resource: deny('assignment_resource_not_found',404)
            before=conn.execute(text('select * from purchasing.supplier_division_assignments where tenant_id=:t and supplier_id=:i and division_ref_id=:d'),params).mappings().first()
            before=AssignmentRead.model_validate(dict(before)) if before else None
            try: replay=self.repository._claim(conn,access.tenant_id,operation,key,digest)
            except ValueError as exc: deny(str(exc),409)
            if replay:return replay
            if payload.expected_revision!=(before.revision if before else 0):deny('assignment_revision_conflict',409)
            if payload.status=='active':
                if resource['status']!='active':deny('assignment_resource_inactive',409)
                society=organization['society_id']
            else:
                if not before:deny('assignment_resource_not_found',404)
                society=before.society_ref_id
            value=AssignmentRead(supplier_id=id_,division_ref_id=division,society_ref_id=society,status=payload.status,revision=(before.revision if before else 0)+1)
            conn.execute(text('insert into purchasing.supplier_division_assignments(tenant_id,supplier_id,division_ref_id,society_ref_id,status,revision) values(:t,:supplier_id,:division_ref_id,:society_ref_id,:status,:revision) on conflict(tenant_id,supplier_id,division_ref_id) do update set society_ref_id=excluded.society_ref_id,status=excluded.status,revision=excluded.revision,updated_at=now()'),{'t':access.tenant_id,**value.model_dump()})
            self.repository._audit(conn,access.tenant_id,access.actor_id,'organization_assignment.supplier','supplier',id_,{'before':before.model_dump() if before else None,'after':value.model_dump(),'correlation_id':correlation,'idempotency_key':key})
            self.repository._finish(conn,access.tenant_id,operation,key,value.model_dump())
            return value.model_dump()
