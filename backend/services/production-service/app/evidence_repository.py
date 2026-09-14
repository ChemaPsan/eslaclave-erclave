import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from erclave_common.errors import ErclaveError
from .evidence_files import PrivateEvidenceStore, normalize_file


class ServiceEvidenceRepository:
    def _is_service_order(self,c,t,o):
        return bool(c.scalar(text("""select p.type='service' from production.production_orders o
            join production.recipes r on r.tenant_id=o.tenant_id and r.id=o.recipe_id
            join production.product_services p on p.tenant_id=r.tenant_id and p.id=r.product_service_id
            where o.tenant_id=:t and o.id=:o"""),{"t":t,"o":o}))

    def _require_service_evidence(self,c,t,o,phase):
        if self._is_service_order(c,t,o) and not c.scalar(text("select 1 from production.service_evidence where tenant_id=:t and order_id=:o and phase=:p"),{"t":t,"o":o,"p":phase}):
            raise ValueError("service_evidence_"+phase+"_required")

    def _service_evidence(self,c,t,o):
        rows=c.execute(text("select id,phase,description,actor_id,created_at from production.service_evidence where tenant_id=:t and order_id=:o order by created_at"),{"t":t,"o":o}).mappings().all()
        return [{**dict(row),"files":[dict(file) for file in c.execute(text("select id,filename,media_type,size_bytes,expires_at,(deleted_at is not null or expires_at<=now()) expired from production.service_evidence_files where tenant_id=:t and evidence_id=:e order by id"),{"t":t,"e":row["id"]}).mappings()]} for row in rows]

    def save_service_evidence(self,t,o,phase,payload,actor):
        fingerprint=hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
        # No storage or image work until authorization and order ownership are checked by API.
        files=[normalize_file(item) for item in payload.files]
        store=PrivateEvidenceStore() if files else None
        written=[]
        try:
            with self.engine.begin() as c:
                order=c.execute(text("select status from production.production_orders where tenant_id=:t and id=:o for update"),{"t":t,"o":o}).mappings().first()
                if not order:raise ErclaveError("production_order_not_found","Order not found.",status_code=404)
                if not self._is_service_order(c,t,o):raise ErclaveError("service_evidence_service_only","Evidence is only for service recipes.",status_code=409)
                previous=c.execute(text("select request_hash from production.service_evidence where tenant_id=:t and order_id=:o and phase=:p"),{"t":t,"o":o,"p":phase}).mappings().first()
                if previous:
                    if previous["request_hash"] != fingerprint:raise ErclaveError("service_evidence_already_recorded","Evidence is immutable.",status_code=409)
                    return self._service_evidence(c,t,o)
                if order["status"] in {"completed","cancelled"}:raise ErclaveError("service_evidence_order_locked","Order is closed.",status_code=409)
                if phase=="finish":self._require_service_evidence(c,t,o,"start")
                eid="sev_"+uuid4().hex[:26]
                c.execute(text("insert into production.service_evidence(id,tenant_id,order_id,phase,description,request_hash,actor_id) values(:i,:t,:o,:p,:d,:h,:a)"),{"i":eid,"t":t,"o":o,"p":phase,"d":payload.description,"h":fingerprint,"a":actor})
                expires=datetime.now(timezone.utc)+timedelta(days=365)
                for file in files:
                    key=hashlib.sha256(t.encode()).hexdigest()+"/"+uuid4().hex
                    store.put(key,file["data"],file["media_type"]);written.append(key)
                    c.execute(text("insert into production.service_evidence_files(id,tenant_id,evidence_id,filename,media_type,size_bytes,sha256,object_key,expires_at) values(:i,:t,:e,:n,:m,:s,:h,:k,:x)"),{"i":"sef_"+uuid4().hex[:26],"t":t,"e":eid,"n":file["filename"],"m":file["media_type"],"s":len(file["data"]),"h":hashlib.sha256(file["data"]).hexdigest(),"k":key,"x":expires})
                result=self._service_evidence(c,t,o)
                self._audit(c,t,actor,"service_evidence.create","production_order",o,{}, {"evidence_id":eid,"phase":phase,"file_count":len(files)},fingerprint)
            return result
        except Exception:
            # Verify references after rollback, including an ambiguous commit failure.
            for key in written:
                try:
                    with self.engine.connect() as c:
                        exists=c.scalar(text("select 1 from production.service_evidence_files where tenant_id=:t and object_key=:k"),{"t":t,"k":key})
                    if not exists:store.delete(key)
                except Exception:pass  # Daily/lifecycle retention remains a backstop.
            raise

    def evidence_file(self,t,o,file_id):
        with self.engine.connect() as c:
            row=c.execute(text("""select f.* from production.service_evidence_files f join production.service_evidence e on e.tenant_id=f.tenant_id and e.id=f.evidence_id
                where f.tenant_id=:t and e.order_id=:o and f.id=:i"""),{"t":t,"o":o,"i":file_id}).mappings().first()
            if not row:raise ErclaveError("service_evidence_file_not_found","Attachment not found.",status_code=404)
            if row["deleted_at"] or row["expires_at"]<=datetime.now(timezone.utc):raise ErclaveError("service_evidence_expired","Attachment retention expired.",status_code=410)
            try:data=PrivateEvidenceStore().read(row["object_key"])
            except FileNotFoundError:raise ErclaveError("service_evidence_file_not_found","Attachment unavailable.",status_code=404)
            return dict(row),data

    def purge_service_evidence(self):
        with self.engine.begin() as c:
            rows=c.execute(text("select id,tenant_id,object_key from production.service_evidence_files where expires_at<=now() and deleted_at is null order by expires_at limit 100 for update skip locked")).mappings().all()
            if not rows:
                from erclave_common.config import get_settings
                if get_settings().environment=="local":PrivateEvidenceStore().purge_local_expired_objects()
                return 0
            store=PrivateEvidenceStore()
            for row in rows:
                store.delete(row["object_key"])
                c.execute(text("update production.service_evidence_files set object_key=null,deleted_at=now() where tenant_id=:t and id=:i"),{"t":row["tenant_id"],"i":row["id"]})
            return len(rows)
