import hashlib, json
from uuid import uuid4
from fastapi import Depends
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.exc import IntegrityError
from erclave_common.config import Settings, get_settings
from .models import centers, receipts, audit
from .authority import fail
PUBLIC = ('id', 'code', 'name', 'division_ref_id', 'status', 'revision')

def public(row):
    return {key: row[key] for key in PUBLIC}

class Repository:

    def __init__(self, engine):
        self.engine = engine

    def list(self, access, division_id=None, q='', status=None, limit=25, offset=0):
        if division_id:
            access.require_division(division_id)
        conditions = [centers.c.tenant_id == access.tenant_id]
        if not access.all_divisions:
            conditions.append(centers.c.division_ref_id.in_(access.division_ids))
        if division_id:
            conditions.append(centers.c.division_ref_id == division_id)
        if status:
            conditions.append(centers.c.status == status)
        if q.strip():
            query = q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            conditions.append(centers.c.code.ilike('%' + query + '%', escape='\\') | centers.c.name.ilike('%' + query + '%', escape='\\'))
        with self.engine.connect() as conn:
            total = conn.execute(select(func.count()).select_from(centers).where(*conditions)).scalar_one()
            rows = conn.execute(select(centers).where(*conditions).order_by(centers.c.code).limit(limit).offset(offset)).mappings().all()
        return {'data': [public(row) for row in rows], 'meta': {'total': total, 'limit': limit, 'offset': offset}}

    def read_in(self, conn, access, id_):
        row = conn.execute(select(centers).where(centers.c.tenant_id == access.tenant_id, centers.c.id == id_)).mappings().first()
        if not row:
            fail('cost_center_not_found', 404)
        access.require_division(row['division_ref_id'])
        return public(row)

    def read(self, access, id_):
        with self.engine.connect() as conn:
            return self.read_in(conn, access, id_)

    def command(self, access, action, payload, key, correlation, client, id_=None):
        fingerprint = hashlib.sha256(json.dumps({'action': action, 'id': id_, 'payload': payload, 'actor': access.actor_id}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with self.engine.begin() as conn:
            conn.execute(text('select pg_advisory_xact_lock(hashtextextended(:scope,0))'), {'scope': access.tenant_id + ':cost-centers'})
            before = self.read_in(conn, access, id_) if id_ else None
            division = before['division_ref_id'] if before else payload['division_ref_id']
            access.require_division(division, active=action in ('create', 'activate'))
            previous = conn.execute(select(receipts).where(receipts.c.tenant_id == access.tenant_id, receipts.c.key == key)).mappings().first()
            if previous:
                if previous['request_hash'] != fingerprint:
                    fail('idempotency_key_reused', 409)
                return previous['response']
            if before and before['revision'] != payload['expected_revision']:
                fail('cost_center_revision_conflict', 409)
            if action == 'create':
                code = client.code(access.tenant_id, access.authorization, access.actor_id, 'cc-' + hashlib.sha256((access.tenant_id + key + fingerprint).encode()).hexdigest())
                values = {'id': 'cc_' + uuid4().hex[:26], 'tenant_id': access.tenant_id, 'code': code, 'name': payload['name'], 'division_ref_id': division, 'status': 'active', 'revision': 1}
                try:
                    with conn.begin_nested():
                        conn.execute(centers.insert().values(**values))
                except IntegrityError:
                    fail('cost_center_code_conflict', 409)
                result = public(values)
            else:
                values = {'revision': before['revision'] + 1, 'updated_at': func.now()}
                if action == 'update':
                    values['name'] = payload['name']
                else:
                    values['status'] = 'active' if action == 'activate' else 'inactive'
                conn.execute(centers.update().where(centers.c.tenant_id == access.tenant_id, centers.c.id == id_).values(**values))
                result = self.read_in(conn, access, id_)
            conn.execute(audit.insert().values(tenant_id=access.tenant_id, id='aud_' + uuid4().hex[:26], actor_id=access.actor_id, action='costing.cost_center.' + action, entity_id=result['id'], before_state=before, after_state=result, correlation_id=correlation, idempotency_key=key))
            conn.execute(receipts.insert().values(tenant_id=access.tenant_id, key=key, request_hash=fingerprint, response=result))
            return result
_engine = None
_engine_url = None

def get_repository(settings: Settings=Depends(get_settings)):
    global _engine, _engine_url
    url = settings.costing_database_url
    if not url:
        fail('cost_center_storage_unavailable', 503)
    if _engine is None or _engine_url != url:
        _engine = create_engine(url, pool_pre_ping=True)
        _engine_url = url
    return Repository(_engine)
