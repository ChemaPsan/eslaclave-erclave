from sqlalchemy import text


class ProductionCreationRecovery:
    def failed_creation(self,t,id,actor):
        with self.engine.connect() as c:
            row=c.execute(text("""select order_id id,code,actor_id,status,error_code,created_at from production.failed_order_creations f
                where tenant_id=:t and order_id=:id and actor_id=:actor
                and not exists(select 1 from production.production_orders o where o.tenant_id=f.tenant_id and o.id=f.order_id)"""),{'t':t,'id':id,'actor':actor}).mappings().first()
            return dict(row) if row else None

    def list_failed_creations(self,t,actor,limit=25,offset=0):
        with self.engine.connect() as c:
            return [dict(row) for row in c.execute(text("select order_id id,code,status,error_code,created_at from production.failed_order_creations where tenant_id=:t and actor_id=:actor and status='pending' order by created_at,order_id limit :limit offset :offset"),{'t':t,'actor':actor,'limit':limit,'offset':offset}).mappings()]

    def require_new_creation_attempt(self,t,id):
        with self.engine.connect() as c:
            if c.execute(text('select 1 from production.failed_order_creations where tenant_id=:t and order_id=:id'),{'t':t,'id':id}).first():raise ValueError('production_creation_attempt_failed')

    def record_failed_creation(self,t,id,code,actor,error_code):
        with self.engine.begin() as c:
            if c.execute(text('select 1 from production.production_orders where tenant_id=:t and id=:id'),{'t':t,'id':id}).first():return False
            c.execute(text("insert into production.failed_order_creations(tenant_id,order_id,code,actor_id,error_code) values(:t,:id,:code,:actor,:error) on conflict(tenant_id,order_id) do nothing"),{'t':t,'id':id,'code':code or id,'actor':actor,'error':error_code})
            return True

    def recover_failed_creation(self,t,id,actor):
        with self.engine.begin() as c:
            c.execute(text("update production.failed_order_creations set status='recovered',recovered_at=now() where tenant_id=:t and order_id=:id and actor_id=:actor"),{'t':t,'id':id,'actor':actor})
            self._audit(c,t,actor,'order.creation_recovery','production_order',id,None,{'status':'recovered'},'recover-'+id)
        return {'id':id,'status':'recovered'}
