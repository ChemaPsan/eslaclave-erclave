import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy import text

from erclave_common.db import create_database_engine

from .schemas import CustomerRead, DeliveryRead, QuoteRead, ResolvedQuoteLine, SalesOrderRead


MONEY = Decimal("0.01")


class SalesRepository:
    def __init__(self, engine):
        self.engine = engine

    def _claim(self, connection, tenant_id, operation, key, fingerprint):
        inserted = connection.execute(
            text("""insert into sales.idempotency_records(id,tenant_id,operation,idempotency_key,request_hash)
                values(:id,:tenant,:operation,:key,:fingerprint)
                on conflict(tenant_id,operation,idempotency_key) do nothing returning id"""),
            {"id": f"sid_{uuid4().hex[:26]}", "tenant": tenant_id, "operation": operation, "key": key, "fingerprint": fingerprint},
        ).scalar_one_or_none()
        if inserted:
            return None
        row = connection.execute(
            text("select request_hash,response_payload from sales.idempotency_records where tenant_id=:tenant and operation=:operation and idempotency_key=:key for update"),
            {"tenant": tenant_id, "operation": operation, "key": key},
        ).mappings().one()
        if row["request_hash"] != fingerprint:
            raise ValueError("idempotency_key_reused")
        return row["response_payload"]

    def _finish(self, connection, tenant_id, operation, key, value):
        connection.execute(text("update sales.idempotency_records set response_payload=cast(:payload as jsonb) where tenant_id=:tenant and operation=:operation and idempotency_key=:key"), {"payload": json.dumps(value.model_dump(mode="json"), ensure_ascii=False), "tenant": tenant_id, "operation": operation, "key": key})

    def _release(self, connection, tenant_id, operation, key):
        connection.execute(text("delete from sales.idempotency_records where tenant_id=:tenant and operation=:operation and idempotency_key=:key and response_payload is null"), {"tenant": tenant_id, "operation": operation, "key": key})

    def _audit(self, connection, tenant_id, actor_id, action, entity_type, entity_id, payload):
        connection.execute(text("insert into sales.audit_events(id,tenant_id,actor_id,action,entity_type,entity_id,payload) values(:id,:tenant,:actor,:action,:type,:entity,cast(:payload as jsonb))"), {"id": f"sae_{uuid4().hex[:26]}", "tenant": tenant_id, "actor": actor_id, "action": action, "type": entity_type, "entity": entity_id, "payload": json.dumps(payload, ensure_ascii=False, default=str)})

    def _customer(self, connection, tenant_id, customer_id):
        row = connection.execute(text("""select id,code,commercial_name,customer_type,status,responsible_worker_ref_id responsible_worker_id,
            responsible_worker_name,payment_terms,currency,credit_limit,legal_name,tax_id,tax_regime,cfdi_use,billing_email,billing_phone,
            billing_address,notes,created_at,updated_at from sales.customers where tenant_id=:tenant and id=:id"""), {"tenant": tenant_id, "id": customer_id}).mappings().first()
        if not row:
            return None
        contacts = connection.execute(text("select id,name,email,phone,role,is_primary,status from sales.customer_contacts where tenant_id=:tenant and customer_id=:id order by is_primary desc,created_at"), {"tenant": tenant_id, "id": customer_id}).mappings().all()
        return CustomerRead.model_validate({**dict(row), "contacts": [dict(item) for item in contacts]})

    def list_customers(self, tenant_id, status=None, q=None):
        where = ["tenant_id=:tenant"]
        params = {"tenant": tenant_id}
        if status:
            where.append("status=:status"); params["status"] = status
        if q:
            where.append("""(code ilike :q or commercial_name ilike :q or legal_name ilike :q or tax_id ilike :q
                or responsible_worker_name ilike :q or billing_email ilike :q or billing_phone ilike :q
                or exists (select 1 from sales.customer_contacts contacts where contacts.tenant_id=sales.customers.tenant_id
                    and contacts.customer_id=sales.customers.id and contacts.status='active'
                    and (contacts.name ilike :q or contacts.email ilike :q or contacts.phone ilike :q)))"""); params["q"] = f"%{q}%"
        with self.engine.connect() as connection:
            ids = connection.execute(text(f"select id from sales.customers where {' and '.join(where)} order by commercial_name limit 200"), params).scalars().all()
            return [self._customer(connection, tenant_id, item) for item in ids]

    def get_customer(self, tenant_id, customer_id):
        with self.engine.connect() as connection:
            return self._customer(connection, tenant_id, customer_id)

    def create_customer(self, tenant_id, payload, worker, key, fingerprint, actor_id):
        operation = "customer.create"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, fingerprint)
            if replay:
                return CustomerRead.model_validate(replay)
            customer_id = f"cus_{uuid4().hex[:26]}"
            data = payload.model_dump(mode="json", exclude={"primary_contact"})
            data["billing_address"] = json.dumps(data["billing_address"], ensure_ascii=False) if data.get("billing_address") else None
            inserted = connection.execute(text("""insert into sales.customers(id,tenant_id,code,commercial_name,customer_type,status,responsible_worker_ref_id,responsible_worker_name,
                payment_terms,currency,credit_limit,legal_name,tax_id,tax_regime,cfdi_use,billing_email,billing_phone,billing_address,notes)
                values(:id,:tenant,:code,:commercial_name,:customer_type,:status,:worker_id,:worker_name,:payment_terms,:currency,:credit_limit,
                :legal_name,:tax_id,:tax_regime,:cfdi_use,:billing_email,:billing_phone,cast(:billing_address as jsonb),:notes)
                on conflict do nothing returning id"""), {"id": customer_id, "tenant": tenant_id, "worker_id": worker.id, "worker_name": worker.full_name, **data}).first()
            if not inserted:
                self._release(connection, tenant_id, operation, key)
                return None
            contact = payload.primary_contact
            connection.execute(text("insert into sales.customer_contacts(id,tenant_id,customer_id,name,email,phone,role,is_primary,status) values(:id,:tenant,:customer,:name,:email,:phone,:role,true,'active')"), {"id": f"sco_{uuid4().hex[:26]}", "tenant": tenant_id, "customer": customer_id, **contact.model_dump()})
            value = self._customer(connection, tenant_id, customer_id)
            self._audit(connection, tenant_id, actor_id, operation, "customer", customer_id, {"code": value.code, "responsible_worker_id": worker.id})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def update_customer(self, tenant_id, customer_id, payload, worker, key, fingerprint, actor_id):
        operation = "customer.update"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, fingerprint)
            if replay:
                return CustomerRead.model_validate(replay)
            before = self._customer(connection, tenant_id, customer_id)
            if not before:
                self._release(connection, tenant_id, operation, key); return None
            data = payload.model_dump(mode="json", exclude_unset=True, exclude={"primary_contact", "responsible_worker_id"})
            if "billing_address" in data:
                data["billing_address"] = json.dumps(data["billing_address"], ensure_ascii=False) if data["billing_address"] else None
            if worker:
                data["responsible_worker_ref_id"] = worker.id; data["responsible_worker_name"] = worker.full_name
            if data:
                assignments = [f"{name}=cast(:{name} as jsonb)" if name == "billing_address" else f"{name}=:{name}" for name in data]
                connection.execute(text(f"update sales.customers set {','.join(assignments)},updated_at=now() where tenant_id=:tenant and id=:id"), {"tenant": tenant_id, "id": customer_id, **data})
            if "primary_contact" in payload.model_fields_set and payload.primary_contact:
                connection.execute(text("update sales.customer_contacts set is_primary=false,updated_at=now() where tenant_id=:tenant and customer_id=:customer and status='active'"), {"tenant": tenant_id, "customer": customer_id})
                contact = payload.primary_contact
                connection.execute(text("insert into sales.customer_contacts(id,tenant_id,customer_id,name,email,phone,role,is_primary,status) values(:id,:tenant,:customer,:name,:email,:phone,:role,true,'active')"), {"id": f"sco_{uuid4().hex[:26]}", "tenant": tenant_id, "customer": customer_id, **contact.model_dump()})
            value = self._customer(connection, tenant_id, customer_id)
            self._audit(connection, tenant_id, actor_id, operation, "customer", customer_id, {"before_status": before.status, "after_status": value.status})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def _quote(self, connection, tenant_id, quote_id):
        row = connection.execute(text("""select id,code,customer_id,customer_code_snapshot customer_code,customer_name_snapshot customer_name,
            responsible_worker_ref_id responsible_worker_id,responsible_worker_name,status,currency,payment_terms,valid_until,promised_delivery_date,
            subtotal,discount_total,total,estimated_cost,estimated_margin,notes,submitted_at,approved_at,created_at,updated_at
            from sales.quotes where tenant_id=:tenant and id=:id"""), {"tenant": tenant_id, "id": quote_id}).mappings().first()
        if not row:
            return None
        lines = connection.execute(text("""select id,line_number,product_service_ref_id product_service_id,product_service_code,product_service_name,
            product_service_type,unit,quantity,unit_price,discount_percentage,subtotal,discount_amount,total,standard_unit_cost_snapshot,estimated_cost
            from sales.quote_lines where tenant_id=:tenant and quote_id=:id order by line_number"""), {"tenant": tenant_id, "id": quote_id}).mappings().all()
        return QuoteRead.model_validate({**dict(row), "lines": [dict(item) for item in lines]})

    def list_quotes(self, tenant_id, status=None, customer_id=None):
        where = ["tenant_id=:tenant"]
        params = {"tenant": tenant_id}
        if status: where.append("status=:status"); params["status"] = status
        if customer_id: where.append("customer_id=:customer"); params["customer"] = customer_id
        with self.engine.connect() as connection:
            ids = connection.execute(text(f"select id from sales.quotes where {' and '.join(where)} order by created_at desc limit 200"), params).scalars().all()
            return [self._quote(connection, tenant_id, item) for item in ids]

    def get_quote(self, tenant_id, quote_id):
        with self.engine.connect() as connection:
            return self._quote(connection, tenant_id, quote_id)

    def _write_lines(self, connection, tenant_id, quote_id, lines: list[ResolvedQuoteLine]):
        subtotal_total = Decimal("0"); discount_total = Decimal("0"); total = Decimal("0"); estimated_cost = Decimal("0"); cost_complete = True
        for number, line in enumerate(lines, start=1):
            subtotal = (line.quantity * line.unit_price).quantize(MONEY, rounding=ROUND_HALF_UP)
            discount = (subtotal * line.discount_percentage / Decimal("100")).quantize(MONEY, rounding=ROUND_HALF_UP)
            line_total = subtotal - discount
            cost = None if line.product.standard_cost is None else (line.quantity * line.product.standard_cost).quantize(MONEY, rounding=ROUND_HALF_UP)
            cost_complete = cost_complete and cost is not None
            if cost is not None: estimated_cost += cost
            connection.execute(text("""insert into sales.quote_lines(id,tenant_id,quote_id,line_number,product_service_ref_id,product_service_code,product_service_name,
                product_service_type,unit,quantity,unit_price,discount_percentage,subtotal,discount_amount,total,standard_unit_cost_snapshot,estimated_cost)
                values(:id,:tenant,:quote,:number,:product_id,:code,:name,:type,:unit,:quantity,:unit_price,:discount_percentage,:subtotal,:discount,:total,:unit_cost,:cost)"""),
                {"id": f"sql_{uuid4().hex[:26]}", "tenant": tenant_id, "quote": quote_id, "number": number, "product_id": line.product.id, "code": line.product.code, "name": line.product.name, "type": line.product.type, "unit": line.unit, "quantity": line.quantity, "unit_price": line.unit_price, "discount_percentage": line.discount_percentage, "subtotal": subtotal, "discount": discount, "total": line_total, "unit_cost": line.product.standard_cost, "cost": cost})
            subtotal_total += subtotal; discount_total += discount; total += line_total
        margin = None if not cost_complete or total == 0 else ((total - estimated_cost) / total * Decimal("100")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        return subtotal_total, discount_total, total, estimated_cost if cost_complete else None, margin

    def create_quote(self, tenant_id, payload, customer, worker, lines, key, fingerprint, actor_id):
        operation = "quote.create"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, fingerprint)
            if replay: return QuoteRead.model_validate(replay)
            quote_id = f"quo_{uuid4().hex[:26]}"
            inserted = connection.execute(text("""insert into sales.quotes(id,tenant_id,code,customer_id,customer_code_snapshot,customer_name_snapshot,responsible_worker_ref_id,
                responsible_worker_name,status,currency,payment_terms,valid_until,promised_delivery_date,subtotal,discount_total,total,estimated_cost,estimated_margin,notes)
                values(:id,:tenant,:code,:customer_id,:customer_code,:customer_name,:worker_id,:worker_name,'draft',:currency,:payment_terms,:valid_until,
                :delivery,0,0,0,null,null,:notes) on conflict do nothing returning id"""),
                {"id": quote_id, "tenant": tenant_id, "code": payload.code, "customer_id": customer.id, "customer_code": customer.code, "customer_name": customer.commercial_name, "worker_id": worker.id, "worker_name": worker.full_name, "currency": payload.currency or customer.currency, "payment_terms": payload.payment_terms or customer.payment_terms, "valid_until": payload.valid_until, "delivery": payload.promised_delivery_date, "notes": payload.notes}).first()
            if not inserted:
                self._release(connection, tenant_id, operation, key); return None
            totals = self._write_lines(connection, tenant_id, quote_id, lines)
            connection.execute(text("update sales.quotes set subtotal=:subtotal,discount_total=:discount,total=:total,estimated_cost=:cost,estimated_margin=:margin where tenant_id=:tenant and id=:id"), {"tenant": tenant_id, "id": quote_id, "subtotal": totals[0], "discount": totals[1], "total": totals[2], "cost": totals[3], "margin": totals[4]})
            value = self._quote(connection, tenant_id, quote_id)
            self._audit(connection, tenant_id, actor_id, operation, "quote", quote_id, {"code": value.code, "total": value.total})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def update_quote(self, tenant_id, quote_id, payload, customer, worker, lines, key, fingerprint, actor_id):
        operation = "quote.update"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, fingerprint)
            if replay: return QuoteRead.model_validate(replay)
            before = self._quote(connection, tenant_id, quote_id)
            if not before:
                self._release(connection, tenant_id, operation, key); return None
            if before.status != "draft":
                self._release(connection, tenant_id, operation, key); raise ValueError("quote_not_editable")
            data = payload.model_dump(mode="json", exclude_unset=True, exclude={"lines", "customer_id", "responsible_worker_id"})
            if customer:
                data.update(customer_id=customer.id, customer_code_snapshot=customer.code, customer_name_snapshot=customer.commercial_name)
            if worker:
                data.update(responsible_worker_ref_id=worker.id, responsible_worker_name=worker.full_name)
            if lines is not None:
                connection.execute(text("delete from sales.quote_lines where tenant_id=:tenant and quote_id=:id"), {"tenant": tenant_id, "id": quote_id})
                totals = self._write_lines(connection, tenant_id, quote_id, lines)
                data.update(subtotal=totals[0], discount_total=totals[1], total=totals[2], estimated_cost=totals[3], estimated_margin=totals[4])
            if data:
                connection.execute(text("update sales.quotes set " + ",".join(f"{name}=:{name}" for name in data) + ",updated_at=now() where tenant_id=:tenant and id=:id"), {"tenant": tenant_id, "id": quote_id, **data})
            value = self._quote(connection, tenant_id, quote_id)
            self._audit(connection, tenant_id, actor_id, operation, "quote", quote_id, {"total": value.total})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def transition_quote(self, tenant_id, quote_id, target, key, fingerprint, actor_id):
        operation = f"quote.{target}"
        allowed = {"quoted": {"draft"}, "approved": {"quoted"}, "expired": {"draft", "quoted"}, "cancelled": {"draft", "quoted"}}
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, fingerprint)
            if replay: return QuoteRead.model_validate(replay)
            before = self._quote(connection, tenant_id, quote_id)
            if not before:
                self._release(connection, tenant_id, operation, key); return None
            if before.status not in allowed[target] or (target in {"quoted", "approved"} and before.valid_until < date.today()):
                self._release(connection, tenant_id, operation, key); raise ValueError("invalid_quote_transition")
            timestamp = ",submitted_at=now()" if target == "quoted" else ",approved_at=now()" if target == "approved" else ""
            connection.execute(text(f"update sales.quotes set status=:target,updated_at=now(){timestamp} where tenant_id=:tenant and id=:id"), {"target": target, "tenant": tenant_id, "id": quote_id})
            value = self._quote(connection, tenant_id, quote_id)
            self._audit(connection, tenant_id, actor_id, operation, "quote", quote_id, {"before": before.status, "after": target})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def _order(self, connection, tenant_id, order_id):
        row = connection.execute(text("""select id,code,quote_id,quote_code_snapshot quote_code,customer_id,
            customer_code_snapshot customer_code,customer_name_snapshot customer_name,
            responsible_worker_ref_id responsible_worker_id,responsible_worker_name,status,currency,payment_terms,
            promised_delivery_date,subtotal,discount_total,total,estimated_cost,estimated_margin,actual_cost,actual_margin,
            notes,fulfillment_state,cancellation_state,created_at,updated_at from sales.orders where tenant_id=:tenant and id=:id"""), {"tenant": tenant_id, "id": order_id}).mappings().first()
        if not row:
            return None
        lines = connection.execute(text("""select id,quote_line_id,line_number,product_service_ref_id product_service_id,
            product_service_code,product_service_name,product_service_type,unit,ordered_quantity,delivered_quantity,
            unit_price,discount_percentage,total,standard_unit_cost_snapshot,estimated_cost,fulfillment_mode,
            fulfillment_status,inventory_item_ref_id inventory_item_id,inventory_item_code_snapshot inventory_item_code,
            inventory_item_name_snapshot inventory_item_name,production_request_ref_id production_request_id
            from sales.order_lines where tenant_id=:tenant and order_id=:id order by line_number"""), {"tenant": tenant_id, "id": order_id}).mappings().all()
        line_values = []
        for line in lines:
            reservations = connection.execute(text("""select id,reservation_ref_id,warehouse_ref_id,reserved_quantity,
                consumed_quantity,unit_cost_snapshot,status from sales.order_line_reservations
                where tenant_id=:tenant and order_line_id=:line order by created_at,id"""), {"tenant": tenant_id, "line": line["id"]}).mappings().all()
            line_values.append({**dict(line), "reservations": [dict(item) for item in reservations]})
        return SalesOrderRead.model_validate({**dict(row), "lines": line_values})

    def list_orders(self, tenant_id, status=None, customer_id=None):
        filters = ["tenant_id=:tenant"]
        params = {"tenant": tenant_id}
        if status:
            filters.append("status=:status"); params["status"] = status
        if customer_id:
            filters.append("customer_id=:customer"); params["customer"] = customer_id
        with self.engine.connect() as connection:
            ids = connection.execute(text(f"select id from sales.orders where {' and '.join(filters)} order by created_at desc limit 200"), params).scalars().all()
            return [self._order(connection, tenant_id, item) for item in ids]

    def get_order(self, tenant_id, order_id):
        with self.engine.connect() as connection:
            return self._order(connection, tenant_id, order_id)

    def prepare_order_fulfillment(self, tenant_id, order_id, payload, key, request_hash):
        with self.engine.begin() as connection:
            row = connection.execute(text("""select status,fulfillment_state,fulfillment_key,fulfillment_hash,cancellation_state
                from sales.orders where tenant_id=:tenant and id=:id for update"""), {"tenant": tenant_id, "id": order_id}).mappings().first()
            if not row:
                return None
            if row["fulfillment_state"] == "completed":
                if row["fulfillment_hash"] != request_hash:
                    raise ValueError("sales_order_line_already_configured")
                return self._order(connection, tenant_id, order_id), row["fulfillment_key"] or key
            if row["status"] in {"cancelled", "delivered"} or row["cancellation_state"] in {"processing", "needs_reconciliation"}:
                raise ValueError("sales_order_not_fulfillable")
            if row["fulfillment_state"] in {"processing", "needs_reconciliation"}:
                if row["fulfillment_hash"] != request_hash:
                    raise ValueError("sales_order_fulfillment_in_progress")
                return self._order(connection, tenant_id, order_id), row["fulfillment_key"]
            line_ids = {line.order_line_id for line in payload.lines}
            locked = connection.execute(text("""select id,fulfillment_mode,delivered_quantity from sales.order_lines
                where tenant_id=:tenant and order_id=:order and id=any(:ids) for update"""),
                {"tenant": tenant_id, "order": order_id, "ids": list(line_ids)}).mappings().all()
            if len(locked) != len(line_ids):
                raise ValueError("sales_order_line_not_found")
            if any(item["fulfillment_mode"] != "pending" or item["delivered_quantity"] > 0 for item in locked):
                raise ValueError("sales_order_line_already_configured")
            connection.execute(text("""update sales.orders set fulfillment_state='processing',fulfillment_key=:key,
                fulfillment_hash=:hash,updated_at=now() where tenant_id=:tenant and id=:id"""),
                {"key": key, "hash": request_hash, "tenant": tenant_id, "id": order_id})
            return self._order(connection, tenant_id, order_id), key

    def mark_fulfillment_reconciliation(self, tenant_id, order_id):
        with self.engine.begin() as connection:
            connection.execute(text("""update sales.orders set fulfillment_state='needs_reconciliation',updated_at=now()
                where tenant_id=:tenant and id=:id and fulfillment_state='processing'"""), {"tenant": tenant_id, "id": order_id})

    def create_order(self, tenant_id, payload, quote, key, request_hash, actor_id):
        operation = "order.create"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, request_hash)
            if replay:
                return SalesOrderRead.model_validate(replay)
            order_id = f"sor_{uuid4().hex[:26]}"
            inserted = connection.execute(text("""insert into sales.orders(id,tenant_id,code,quote_id,quote_code_snapshot,
                customer_id,customer_code_snapshot,customer_name_snapshot,responsible_worker_ref_id,responsible_worker_name,
                status,currency,payment_terms,promised_delivery_date,subtotal,discount_total,total,estimated_cost,estimated_margin,notes)
                values(:id,:tenant,:code,:quote_id,:quote_code,:customer_id,:customer_code,:customer_name,:worker_id,:worker_name,
                'confirmed',:currency,:payment_terms,:promise,:subtotal,:discount,:total,:cost,:margin,:notes)
                on conflict do nothing returning id"""), {"id": order_id, "tenant": tenant_id, "code": payload.code, "quote_id": quote.id, "quote_code": quote.code,
                "customer_id": quote.customer_id, "customer_code": quote.customer_code, "customer_name": quote.customer_name,
                "worker_id": quote.responsible_worker_id, "worker_name": quote.responsible_worker_name, "currency": quote.currency,
                "payment_terms": quote.payment_terms, "promise": payload.promised_delivery_date or quote.promised_delivery_date,
                "subtotal": quote.subtotal, "discount": quote.discount_total, "total": quote.total, "cost": quote.estimated_cost,
                "margin": quote.estimated_margin, "notes": payload.notes}).first()
            if not inserted:
                self._release(connection, tenant_id, operation, key)
                return None
            for line in quote.lines:
                mode = "service" if line.product_service_type == "service" else "pending"
                line_status = "ready" if mode == "service" else "pending"
                connection.execute(text("""insert into sales.order_lines(id,tenant_id,order_id,quote_line_id,line_number,
                    product_service_ref_id,product_service_code,product_service_name,product_service_type,unit,ordered_quantity,
                    delivered_quantity,unit_price,discount_percentage,total,standard_unit_cost_snapshot,estimated_cost,
                    fulfillment_mode,fulfillment_status)
                    values(:id,:tenant,:order_id,:quote_line_id,:number,:product_id,:code,:name,:type,:unit,:quantity,0,
                    :unit_price,:discount,:total,:unit_cost,:estimated_cost,:mode,:status)"""), {"id": f"sol_{uuid4().hex[:26]}", "tenant": tenant_id,
                    "order_id": order_id, "quote_line_id": line.id, "number": line.line_number, "product_id": line.product_service_id,
                    "code": line.product_service_code, "name": line.product_service_name, "type": line.product_service_type,
                    "unit": line.unit, "quantity": line.quantity, "unit_price": line.unit_price, "discount": line.discount_percentage,
                    "total": line.total, "unit_cost": line.standard_unit_cost_snapshot, "estimated_cost": line.estimated_cost,
                    "mode": mode, "status": line_status})
            value = self._order(connection, tenant_id, order_id)
            self._audit(connection, tenant_id, actor_id, operation, "sales_order", order_id, {"quote_id": quote.id, "code": value.code, "total": value.total})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def configure_order_fulfillment(self, tenant_id, order_id, resolved_lines, key, request_hash, actor_id):
        operation = f"order.fulfillment:{order_id}"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, request_hash)
            if replay:
                return SalesOrderRead.model_validate(replay)
            connection.execute(text("select id from sales.orders where tenant_id=:tenant and id=:id for update"), {"tenant": tenant_id, "id": order_id})
            before = self._order(connection, tenant_id, order_id)
            if not before:
                self._release(connection, tenant_id, operation, key); return None
            if before.status in {"cancelled", "delivered"}:
                self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_not_fulfillable")
            by_id = {line.id: line for line in before.lines}
            for resolved in resolved_lines:
                current = by_id.get(resolved["order_line_id"])
                if not current:
                    self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_line_not_found")
                if current.delivered_quantity > 0 or current.fulfillment_status == "delivered":
                    self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_line_already_delivered")
                if current.fulfillment_mode != "pending" or current.delivered_quantity > 0:
                    self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_line_already_configured")
                mode = resolved["mode"]
                status = "reserved" if mode == "stock" else "production_requested" if mode == "production" else "ready"
                connection.execute(text("""update sales.order_lines set fulfillment_mode=:mode,fulfillment_status=:status,
                    inventory_item_ref_id=:inventory,inventory_item_code_snapshot=:inventory_code,
                    inventory_item_name_snapshot=:inventory_name,production_request_ref_id=:production,updated_at=now()
                    where tenant_id=:tenant and id=:line"""), {"mode": mode, "status": status, "inventory": resolved.get("inventory_item_id"),
                    "inventory_code": resolved.get("inventory_item_code"), "inventory_name": resolved.get("inventory_item_name"),
                    "production": resolved.get("production_request_id"), "tenant": tenant_id, "line": current.id})
                for reservation in resolved.get("reservations", []):
                    connection.execute(text("""insert into sales.order_line_reservations(id,tenant_id,order_line_id,reservation_ref_id,
                        warehouse_ref_id,reserved_quantity,consumed_quantity,unit_cost_snapshot,status)
                        values(:id,:tenant,:line,:reservation,:warehouse,:quantity,0,:cost,'active')
                        on conflict(tenant_id,reservation_ref_id) do nothing"""), {"id": f"slr_{uuid4().hex[:26]}", "tenant": tenant_id,
                        "line": current.id, "reservation": reservation["id"], "warehouse": reservation["warehouse_id"],
                        "quantity": reservation["quantity"], "cost": reservation.get("unit_cost_snapshot", 0)})
            statuses = connection.execute(text("select fulfillment_status from sales.order_lines where tenant_id=:tenant and order_id=:order"), {"tenant": tenant_id, "order": order_id}).scalars().all()
            target = "ready" if all(item in {"reserved", "ready"} for item in statuses) else "fulfillment_pending"
            connection.execute(text("""update sales.orders set status=:status,fulfillment_state='completed',updated_at=now()
                where tenant_id=:tenant and id=:id"""), {"status": target, "tenant": tenant_id, "id": order_id})
            value = self._order(connection, tenant_id, order_id)
            self._audit(connection, tenant_id, actor_id, operation, "sales_order", order_id, {"before": before.status, "after": value.status, "lines": resolved_lines})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def prepare_cancel_order(self, tenant_id, order_id, key, request_hash):
        with self.engine.begin() as connection:
            row = connection.execute(text("""select status,cancellation_state,cancellation_key,cancellation_hash,fulfillment_state
                from sales.orders where tenant_id=:tenant and id=:id for update"""), {"tenant": tenant_id, "id": order_id}).mappings().first()
            if not row:
                return None
            if row["status"] == "cancelled" and row["cancellation_state"] == "completed":
                if row["cancellation_hash"] != request_hash:
                    raise ValueError("sales_order_not_cancellable")
                return self._order(connection, tenant_id, order_id), row["cancellation_key"] or key
            if row["status"] in {"partially_delivered", "delivered", "cancelled"}:
                raise ValueError("sales_order_not_cancellable")
            if row["fulfillment_state"] in {"processing", "needs_reconciliation"}:
                raise ValueError("sales_order_fulfillment_in_progress")
            delivery_in_progress = connection.execute(text("""select 1 from sales.deliveries where tenant_id=:tenant
                and order_id=:id and confirmation_state in ('processing','needs_reconciliation') limit 1"""),
                {"tenant": tenant_id, "id": order_id}).first()
            if delivery_in_progress:
                raise ValueError("delivery_confirmation_in_progress")
            if row["cancellation_state"] in {"processing", "needs_reconciliation"}:
                if row["cancellation_hash"] != request_hash:
                    raise ValueError("sales_order_cancellation_in_progress")
                return self._order(connection, tenant_id, order_id), row["cancellation_key"]
            connection.execute(text("""update sales.orders set cancellation_state='processing',cancellation_key=:key,
                cancellation_hash=:hash,updated_at=now() where tenant_id=:tenant and id=:id"""),
                {"key": key, "hash": request_hash, "tenant": tenant_id, "id": order_id})
            return self._order(connection, tenant_id, order_id), key

    def mark_cancellation_reconciliation(self, tenant_id, order_id):
        with self.engine.begin() as connection:
            connection.execute(text("""update sales.orders set cancellation_state='needs_reconciliation',updated_at=now()
                where tenant_id=:tenant and id=:id and cancellation_state='processing'"""), {"tenant": tenant_id, "id": order_id})

    def cancel_order(self, tenant_id, order_id, reason, key, request_hash, actor_id):
        operation = "order.cancel"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, request_hash)
            if replay:
                return SalesOrderRead.model_validate(replay)
            connection.execute(text("select id from sales.orders where tenant_id=:tenant and id=:id for update"), {"tenant": tenant_id, "id": order_id})
            before = self._order(connection, tenant_id, order_id)
            if not before:
                self._release(connection, tenant_id, operation, key); return None
            if before.status in {"partially_delivered", "delivered", "cancelled"}:
                self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_not_cancellable")
            connection.execute(text("""update sales.orders set status='cancelled',cancellation_state='completed',cancelled_at=now(),updated_at=now()
                where tenant_id=:tenant and id=:id"""), {"tenant": tenant_id, "id": order_id})
            connection.execute(text("update sales.order_lines set fulfillment_status='cancelled',updated_at=now() where tenant_id=:tenant and order_id=:id"), {"tenant": tenant_id, "id": order_id})
            connection.execute(text("update sales.order_line_reservations set status='released',updated_at=now() where tenant_id=:tenant and order_line_id in (select id from sales.order_lines where tenant_id=:tenant and order_id=:id) and status='active'"), {"tenant": tenant_id, "id": order_id})
            connection.execute(text("update sales.deliveries set status='cancelled',updated_at=now() where tenant_id=:tenant and order_id=:id and status='draft'"), {"tenant": tenant_id, "id": order_id})
            value = self._order(connection, tenant_id, order_id)
            self._audit(connection, tenant_id, actor_id, operation, "sales_order", order_id, {"before": before.status, "after": value.status, "reason": reason})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def _delivery(self, connection, tenant_id, delivery_id):
        row = connection.execute(text("""select id,code,order_id,order_code_snapshot order_code,customer_id,
            customer_name_snapshot customer_name,status,scheduled_date,delivered_at,recipient_name,evidence_reference,
            notes,confirmation_state,created_at,updated_at from sales.deliveries where tenant_id=:tenant and id=:id"""), {"tenant": tenant_id, "id": delivery_id}).mappings().first()
        if not row:
            return None
        lines = connection.execute(text("""select id,order_line_id,line_number,product_service_ref_id product_service_id,
            product_service_code,product_service_name,unit,quantity,actual_cost,actual_cost_source from sales.delivery_lines
            where tenant_id=:tenant and delivery_id=:id order by line_number"""), {"tenant": tenant_id, "id": delivery_id}).mappings().all()
        return DeliveryRead.model_validate({**dict(row), "lines": [dict(item) for item in lines]})

    def list_deliveries(self, tenant_id, status=None, order_id=None):
        filters = ["tenant_id=:tenant"]
        params = {"tenant": tenant_id}
        if status:
            filters.append("status=:status"); params["status"] = status
        if order_id:
            filters.append("order_id=:order"); params["order"] = order_id
        with self.engine.connect() as connection:
            ids = connection.execute(text(f"select id from sales.deliveries where {' and '.join(filters)} order by created_at desc limit 200"), params).scalars().all()
            return [self._delivery(connection, tenant_id, item) for item in ids]

    def get_delivery(self, tenant_id, delivery_id):
        with self.engine.connect() as connection:
            return self._delivery(connection, tenant_id, delivery_id)

    def create_delivery(self, tenant_id, payload, key, request_hash, actor_id):
        operation = "delivery.create"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, request_hash)
            if replay:
                return DeliveryRead.model_validate(replay)
            connection.execute(text("select id from sales.orders where tenant_id=:tenant and id=:id for update"), {"tenant": tenant_id, "id": payload.order_id})
            order = self._order(connection, tenant_id, payload.order_id)
            if not order:
                self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_not_found")
            if order.status in {"cancelled", "delivered"} or order.cancellation_state in {"processing", "needs_reconciliation"}:
                self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_not_deliverable")
            by_id = {line.id: line for line in order.lines}
            for line in payload.lines:
                source = by_id.get(line.order_line_id)
                if not source:
                    self._release(connection, tenant_id, operation, key); raise ValueError("sales_order_line_not_found")
                connection.execute(text("select id from sales.order_lines where tenant_id=:tenant and id=:id for update"), {"tenant": tenant_id, "id": source.id})
                committed = connection.execute(text("""select coalesce(sum(dl.quantity),0) from sales.delivery_lines dl
                    join sales.deliveries d on d.tenant_id=dl.tenant_id and d.id=dl.delivery_id
                    where dl.tenant_id=:tenant and dl.order_line_id=:line and d.status='draft'"""),
                    {"tenant": tenant_id, "line": source.id}).scalar_one()
                remaining = source.ordered_quantity - source.delivered_quantity - Decimal(str(committed or 0))
                if line.quantity > remaining:
                    self._release(connection, tenant_id, operation, key); raise ValueError("delivery_quantity_exceeds_uncommitted")
                if source.fulfillment_mode == "pending" or source.fulfillment_status in {"pending", "production_requested", "cancelled"}:
                    self._release(connection, tenant_id, operation, key); raise ValueError("order_line_not_ready_for_delivery")
                if source.fulfillment_mode == "stock":
                    available_reserved = sum(item.reserved_quantity - item.consumed_quantity for item in source.reservations if item.status == "active")
                    if line.quantity > available_reserved:
                        self._release(connection, tenant_id, operation, key); raise ValueError("delivery_exceeds_reserved_quantity")
                    if line.actual_unit_cost is not None:
                        self._release(connection, tenant_id, operation, key); raise ValueError("stock_cost_is_authoritative")
                if source.fulfillment_mode == "service" and line.actual_unit_cost is None:
                    self._release(connection, tenant_id, operation, key); raise ValueError("service_actual_cost_required")
            delivery_id = f"del_{uuid4().hex[:26]}"
            inserted = connection.execute(text("""insert into sales.deliveries(id,tenant_id,code,order_id,order_code_snapshot,customer_id,
                customer_name_snapshot,status,scheduled_date,recipient_name,evidence_reference,notes)
                values(:id,:tenant,:code,:order,:order_code,:customer,:customer_name,'draft',:date,:recipient,:evidence,:notes)
                on conflict do nothing returning id"""), {"id": delivery_id, "tenant": tenant_id, "code": payload.code, "order": order.id,
                "order_code": order.code, "customer": order.customer_id, "customer_name": order.customer_name,
                "date": payload.scheduled_date, "recipient": payload.recipient_name, "evidence": payload.evidence_reference, "notes": payload.notes}).first()
            if not inserted:
                self._release(connection, tenant_id, operation, key); return None
            for number, requested in enumerate(payload.lines, start=1):
                source = by_id[requested.order_line_id]
                actual_cost = requested.quantity * requested.actual_unit_cost if source.fulfillment_mode == "service" else None
                cost_source = "service_capture" if source.fulfillment_mode == "service" else None
                connection.execute(text("""insert into sales.delivery_lines(id,tenant_id,delivery_id,order_line_id,line_number,
                    product_service_ref_id,product_service_code,product_service_name,unit,quantity,actual_cost,actual_cost_source)
                    values(:id,:tenant,:delivery,:order_line,:number,:product,:code,:name,:unit,:quantity,:actual_cost,:cost_source)"""), {"id": f"dll_{uuid4().hex[:26]}",
                    "tenant": tenant_id, "delivery": delivery_id, "order_line": source.id, "number": number,
                    "product": source.product_service_id, "code": source.product_service_code, "name": source.product_service_name,
                    "unit": source.unit, "quantity": requested.quantity, "actual_cost": actual_cost, "cost_source": cost_source})
            value = self._delivery(connection, tenant_id, delivery_id)
            self._audit(connection, tenant_id, actor_id, operation, "delivery", delivery_id, {"order_id": order.id, "code": value.code})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def prepare_delivery_confirmation(self, tenant_id, delivery_id, key, request_hash):
        with self.engine.begin() as connection:
            state = connection.execute(text("""select status,confirmation_state,confirmation_key,confirmation_hash,order_id
                from sales.deliveries where tenant_id=:tenant and id=:id for update"""), {"tenant": tenant_id, "id": delivery_id}).mappings().first()
            if not state:
                return None
            if state["status"] == "confirmed":
                if state["confirmation_hash"] and state["confirmation_hash"] != request_hash:
                    raise ValueError("delivery_not_confirmable")
                return self._delivery(connection, tenant_id, delivery_id), [], state["confirmation_key"] or key
            if state["status"] != "draft":
                raise ValueError("delivery_not_confirmable")
            order_state = connection.execute(text("select status,cancellation_state from sales.orders where tenant_id=:tenant and id=:id for update"), {"tenant": tenant_id, "id": state["order_id"]}).mappings().one()
            if order_state["status"] == "cancelled" or order_state["cancellation_state"] in {"processing", "needs_reconciliation"}:
                raise ValueError("sales_order_not_deliverable")
            effective_key = key
            if state["confirmation_state"] in {"processing", "needs_reconciliation"}:
                if state["confirmation_hash"] != request_hash:
                    raise ValueError("delivery_confirmation_in_progress")
                effective_key = state["confirmation_key"]
            else:
                connection.execute(text("""update sales.deliveries set confirmation_state='processing',confirmation_key=:key,
                    confirmation_hash=:hash,updated_at=now() where tenant_id=:tenant and id=:id"""),
                    {"key": key, "hash": request_hash, "tenant": tenant_id, "id": delivery_id})
            delivery = self._delivery(connection, tenant_id, delivery_id)
            plan = []
            order = self._order(connection, tenant_id, delivery.order_id)
            by_id = {line.id: line for line in order.lines}
            for delivery_line in delivery.lines:
                order_line = by_id[delivery_line.order_line_id]
                if order_line.fulfillment_mode != "stock":
                    continue
                pending = delivery_line.quantity
                for reservation in order_line.reservations:
                    available = reservation.reserved_quantity - reservation.consumed_quantity if reservation.status == "active" else Decimal("0")
                    if available <= 0:
                        continue
                    quantity = min(pending, available)
                    plan.append({"delivery_line_id": delivery_line.id, "order_line_id": order_line.id, "reservation_ref_id": reservation.reservation_ref_id, "quantity": quantity, "unit_cost": reservation.unit_cost_snapshot})
                    pending -= quantity
                    if pending <= 0:
                        break
                if pending > 0:
                    raise ValueError("delivery_exceeds_reserved_quantity")
            return delivery, plan, effective_key

    def delivery_consumption_plan(self, tenant_id, delivery_id):
        prepared = self.prepare_delivery_confirmation(tenant_id, delivery_id, "legacy-confirmation", "legacy-confirmation")
        return None if prepared is None else prepared[:2]

    def mark_delivery_reconciliation(self, tenant_id, delivery_id):
        with self.engine.begin() as connection:
            connection.execute(text("""update sales.deliveries set confirmation_state='needs_reconciliation',updated_at=now()
                where tenant_id=:tenant and id=:id and confirmation_state='processing'"""), {"tenant": tenant_id, "id": delivery_id})

    def confirm_delivery(self, tenant_id, delivery_id, consumptions, key, request_hash, actor_id):
        operation = "delivery.confirm"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, request_hash)
            if replay:
                return DeliveryRead.model_validate(replay)
            connection.execute(text("select id from sales.deliveries where tenant_id=:tenant and id=:id for update"), {"tenant": tenant_id, "id": delivery_id})
            delivery = self._delivery(connection, tenant_id, delivery_id)
            if not delivery:
                self._release(connection, tenant_id, operation, key); return None
            if delivery.status != "draft":
                self._release(connection, tenant_id, operation, key); raise ValueError("delivery_not_confirmable")
            costs_by_line = {line.id: line.actual_cost for line in delivery.lines if line.actual_cost is not None}
            for item in consumptions:
                cost = Decimal(str(item["quantity"])) * Decimal(str(item["unit_cost"]))
                costs_by_line[item["delivery_line_id"]] = costs_by_line.get(item["delivery_line_id"], Decimal("0")) + cost
                connection.execute(text("""update sales.order_line_reservations set consumed_quantity=consumed_quantity+:quantity,
                    status=case when consumed_quantity+:quantity>=reserved_quantity then 'consumed' else 'active' end,updated_at=now()
                    where tenant_id=:tenant and reservation_ref_id=:reservation"""), {"quantity": item["quantity"], "tenant": tenant_id, "reservation": item["reservation_ref_id"]})
            for line in delivery.lines:
                cost = costs_by_line.get(line.id)
                source = "inventory_consumption" if any(item["delivery_line_id"] == line.id for item in consumptions) else line.actual_cost_source
                connection.execute(text("update sales.delivery_lines set actual_cost=:cost,actual_cost_source=:source where tenant_id=:tenant and id=:id"), {"cost": cost, "source": source, "tenant": tenant_id, "id": line.id})
                updated = connection.execute(text("""update sales.order_lines set delivered_quantity=delivered_quantity+:quantity,
                    fulfillment_status=case when delivered_quantity+:quantity>=ordered_quantity then 'delivered' else 'partially_delivered' end,
                    updated_at=now() where tenant_id=:tenant and id=:id and delivered_quantity+:quantity<=ordered_quantity"""), {"quantity": line.quantity, "tenant": tenant_id, "id": line.order_line_id})
                if updated.rowcount != 1:
                    self._release(connection, tenant_id, operation, key); raise ValueError("delivery_quantity_exceeds_remaining")
            statuses = connection.execute(text("select fulfillment_status from sales.order_lines where tenant_id=:tenant and order_id=:order"), {"tenant": tenant_id, "order": delivery.order_id}).scalars().all()
            order_status = "delivered" if all(item == "delivered" for item in statuses) else "partially_delivered"
            actual_cost = connection.execute(text("select coalesce(sum(actual_cost),0) from sales.delivery_lines where tenant_id=:tenant and delivery_id in (select id from sales.deliveries where tenant_id=:tenant and order_id=:order and status='confirmed')"), {"tenant": tenant_id, "order": delivery.order_id}).scalar_one() or Decimal("0")
            actual_cost += sum(costs_by_line.values())
            total = connection.execute(text("select total from sales.orders where tenant_id=:tenant and id=:order"), {"tenant": tenant_id, "order": delivery.order_id}).scalar_one()
            margin = None if not total else ((Decimal(str(total)) - Decimal(str(actual_cost))) / Decimal(str(total)) * Decimal("100")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            connection.execute(text("""update sales.orders set status=:status,actual_cost=:cost,actual_margin=:margin,
                completed_at=case when :completed then now() else completed_at end,updated_at=now()
                where tenant_id=:tenant and id=:order"""), {"status": order_status, "completed": order_status == "delivered", "cost": actual_cost, "margin": margin, "tenant": tenant_id, "order": delivery.order_id})
            connection.execute(text("""update sales.deliveries set status='confirmed',confirmation_state='completed',
                delivered_at=now(),updated_at=now() where tenant_id=:tenant and id=:id"""), {"tenant": tenant_id, "id": delivery_id})
            value = self._delivery(connection, tenant_id, delivery_id)
            self._audit(connection, tenant_id, actor_id, operation, "delivery", delivery_id, {"order_id": delivery.order_id, "consumptions": consumptions})
            self._finish(connection, tenant_id, operation, key, value)
            return value

    def cancel_delivery(self, tenant_id, delivery_id, reason, key, request_hash, actor_id):
        operation = "delivery.cancel"
        with self.engine.begin() as connection:
            replay = self._claim(connection, tenant_id, operation, key, request_hash)
            if replay:
                return DeliveryRead.model_validate(replay)
            before = self._delivery(connection, tenant_id, delivery_id)
            if not before:
                self._release(connection, tenant_id, operation, key); return None
            if before.status != "draft":
                self._release(connection, tenant_id, operation, key); raise ValueError("delivery_not_cancellable")
            connection.execute(text("update sales.deliveries set status='cancelled',updated_at=now() where tenant_id=:tenant and id=:id"), {"tenant": tenant_id, "id": delivery_id})
            value = self._delivery(connection, tenant_id, delivery_id)
            self._audit(connection, tenant_id, actor_id, operation, "delivery", delivery_id, {"before": before.status, "after": value.status, "reason": reason})
            self._finish(connection, tenant_id, operation, key, value)
            return value


_repository = None


def get_sales_repository() -> SalesRepository:
    global _repository
    if _repository is None:
        _repository = SalesRepository(create_database_engine())
    return _repository
