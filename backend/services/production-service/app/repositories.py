import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from erclave_common.db import create_database_engine
from erclave_common.errors import ErclaveError

from .schemas import RecipeRead, RecipeVersionRead, ProductServiceRead


class ProductionRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def list_product_services(
        self,
        tenant_id: str,
        limit: int = 50,
        status: str | None = None,
        q: str | None = None,
        type_: str | None = None,
    ) -> list[ProductServiceRead]:
        filters = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id, "limit": limit}
        if status:
            filters.append("status = :status")
            params["status"] = status
        if type_:
            filters.append("type = :type")
            params["type"] = type_
        if q:
            filters.append("(code ilike :q or name ilike :q)")
            params["q"] = f"%{q}%"

        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    f"""
                    select id, code, name, type, category, base_unit, status, target_price, standard_cost, responsible_area
                    from production.product_services
                    where {" and ".join(filters)}
                    order by code
                    limit :limit
                    """
                ),
                params,
            ).mappings().all()

        return [ProductServiceRead.model_validate(dict(row)) for row in rows]

    def get_product_service(self, tenant_id: str, product_service_id: str) -> ProductServiceRead | None:
        with self.engine.connect() as connection:
            row = self._get_product_service(connection, tenant_id, product_service_id)

        return ProductServiceRead.model_validate(dict(row)) if row else None

    def create_product_service(
        self,
        tenant_id: str,
        code: str,
        name: str,
        type_: str,
        category: str | None,
        base_unit: str,
        target_price: float | None,
        responsible_area: str | None,
        idempotency_key: str,
        request_hash: str,
        actor_id: str,
    ) -> ProductServiceRead | None:
        product_service_id = f"prs_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "product_service.create", idempotency_key, request_hash, actor_id)
            if replay is not None:
                return ProductServiceRead.model_validate(replay)
            row = connection.execute(
                text(
                    """
                    insert into production.product_services (
                        id, tenant_id, code, name, type, category, base_unit, status, target_price, responsible_area
                    )
                    values (
                        :id, :tenant_id, lower(:code), :name, :type, :category, :base_unit, 'active', :target_price, :responsible_area
                    )
                    on conflict (tenant_id, code) do nothing
                    returning id
                    """
                ),
                {
                    "id": product_service_id,
                    "tenant_id": tenant_id,
                    "code": code,
                    "name": name,
                    "type": type_,
                    "category": category,
                    "base_unit": base_unit,
                    "target_price": target_price,
                    "responsible_area": responsible_area,
                },
            ).mappings().first()
            if row is None:
                self._release_idempotency(connection, tenant_id, "product_service.create", idempotency_key)
                return None
            product_service = self._get_product_service(connection, tenant_id, row["id"])
            self._complete_idempotency(connection, tenant_id, "product_service.create", idempotency_key, ProductServiceRead.model_validate(dict(product_service)).model_dump(mode="json"), 201)

        return ProductServiceRead.model_validate(dict(product_service))

    def update_product_service(
        self,
        tenant_id: str,
        product_service_id: str,
        name: str | None,
        category: str | None,
        base_unit: str | None,
        target_price: float | None,
        responsible_area: str | None,
    ) -> ProductServiceRead | None:
        with self.engine.begin() as connection:
            if self._get_product_service(connection, tenant_id, product_service_id) is None:
                return None
            connection.execute(
                text(
                    """
                    update production.product_services
                    set
                        name = coalesce(:name, name),
                        category = coalesce(:category, category),
                        base_unit = coalesce(:base_unit, base_unit),
                        target_price = coalesce(:target_price, target_price),
                        responsible_area = coalesce(:responsible_area, responsible_area),
                        updated_at = now()
                    where tenant_id = :tenant_id and id = :id
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "id": product_service_id,
                    "name": name,
                    "category": category,
                    "base_unit": base_unit,
                    "target_price": target_price,
                    "responsible_area": responsible_area,
                },
            )
            product_service = self._get_product_service(connection, tenant_id, product_service_id)

        return ProductServiceRead.model_validate(dict(product_service)) if product_service else None

    def update_product_service_status(
        self,
        tenant_id: str,
        product_service_id: str,
        status: str,
        idempotency_key: str,
        request_hash: str,
        actor_id: str,
    ) -> ProductServiceRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "product_service.status", idempotency_key, request_hash, actor_id)
            if replay is not None:
                return ProductServiceRead.model_validate(replay)
            row = connection.execute(
                text(
                    """
                    update production.product_services
                    set status = :status, updated_at = now()
                    where tenant_id = :tenant_id and id = :id
                    returning id
                    """
                ),
                {"tenant_id": tenant_id, "id": product_service_id, "status": status},
            ).mappings().first()
            if row is None:
                self._release_idempotency(connection, tenant_id, "product_service.status", idempotency_key)
                return None
            product_service = self._get_product_service(connection, tenant_id, product_service_id)
            self._complete_idempotency(connection, tenant_id, "product_service.status", idempotency_key, ProductServiceRead.model_validate(dict(product_service)).model_dump(mode="json"), 200)

        return ProductServiceRead.model_validate(dict(product_service)) if product_service else None

    def _get_product_service(self, connection, tenant_id: str, product_service_id: str):
        return connection.execute(
            text(
                """
                select id, code, name, type, category, base_unit, status, target_price, standard_cost, responsible_area
                from production.product_services
                where tenant_id = :tenant_id and id = :id
                """
            ),
            {"tenant_id": tenant_id, "id": product_service_id},
        ).mappings().first()

    def list_recipes(self, tenant_id: str, limit: int = 50) -> list[RecipeRead]:
        with self.engine.connect() as connection:
            ids = connection.execute(
                text("select id from production.recipes where tenant_id = :tenant_id order by code limit :limit"),
                {"tenant_id": tenant_id, "limit": limit},
            ).scalars().all()
            return [self._read_recipe(connection, tenant_id, recipe_id) for recipe_id in ids]

    def get_recipe(self, tenant_id: str, recipe_id: str) -> RecipeRead | None:
        with self.engine.connect() as connection:
            return self._read_recipe(connection, tenant_id, recipe_id)

    def create_recipe(self, tenant_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str) -> RecipeRead | None:
        recipe_id = f"rec_{uuid4().hex[:26]}"
        version_id = f"rcv_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "recipe.create", idempotency_key, request_hash, actor_id)
            if replay is not None:
                return RecipeRead.model_validate(replay)
            product = self._get_product_service(connection, tenant_id, payload.product_service_id)
            if product is None:
                self._release_idempotency(connection, tenant_id, "recipe.create", idempotency_key)
                return None
            row = connection.execute(
                text("""
                    insert into production.recipes (id, tenant_id, product_service_id, code, name)
                    values (:id, :tenant_id, :product_service_id, lower(:code), :name)
                    on conflict (tenant_id, code) do nothing returning id
                """),
                {"id": recipe_id, "tenant_id": tenant_id, "product_service_id": payload.product_service_id, "code": payload.code, "name": payload.name},
            ).first()
            if row is None:
                self._release_idempotency(connection, tenant_id, "recipe.create", idempotency_key)
                return None
            self._insert_version(connection, tenant_id, recipe_id, version_id, 1, payload)
            recipe = self._read_recipe(connection, tenant_id, recipe_id)
            self._complete_idempotency(connection, tenant_id, "recipe.create", idempotency_key, recipe.model_dump(mode="json"), 201)
            return recipe

    def create_recipe_version(self, tenant_id: str, recipe_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str) -> RecipeVersionRead | None:
        version_id = f"rcv_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "recipe_version.create", idempotency_key, request_hash, actor_id)
            if replay is not None:
                return RecipeVersionRead.model_validate(replay)
            recipe = connection.execute(text("select id from production.recipes where tenant_id=:tenant_id and id=:id for update"), {"tenant_id": tenant_id, "id": recipe_id}).first()
            if recipe is None:
                self._release_idempotency(connection, tenant_id, "recipe_version.create", idempotency_key)
                return None
            version_number = connection.execute(text("select coalesce(max(version_number), 0) + 1 from production.recipe_versions where tenant_id=:tenant_id and recipe_id=:recipe_id"), {"tenant_id": tenant_id, "recipe_id": recipe_id}).scalar_one()
            self._insert_version(connection, tenant_id, recipe_id, version_id, version_number, payload)
            version = self._read_version(connection, tenant_id, version_id)
            self._complete_idempotency(connection, tenant_id, "recipe_version.create", idempotency_key, version.model_dump(mode="json"), 201)
            return version

    def update_recipe_version(self, tenant_id: str, version_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str) -> RecipeVersionRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "recipe_version.update", idempotency_key, request_hash, actor_id)
            if replay is not None:
                return RecipeVersionRead.model_validate(replay)
            row = connection.execute(text("select id from production.recipe_versions where tenant_id=:tenant_id and id=:id and status='draft'"), {"tenant_id": tenant_id, "id": version_id}).first()
            if row is None:
                self._release_idempotency(connection, tenant_id, "recipe_version.update", idempotency_key)
                return None
            connection.execute(text("""
                update production.recipe_versions set base_quantity=:base_quantity, base_unit=:base_unit,
                change_reason=:change_reason, standard_cost=:standard_cost, updated_at=now()
                where tenant_id=:tenant_id and id=:id
            """), {"tenant_id": tenant_id, "id": version_id, "base_quantity": payload.base_quantity, "base_unit": payload.base_unit, "change_reason": payload.change_reason, "standard_cost": sum(item.quantity * item.unit_cost for item in payload.resources)})
            connection.execute(text("delete from production.recipe_resources where tenant_id=:tenant_id and recipe_version_id=:id"), {"tenant_id": tenant_id, "id": version_id})
            connection.execute(text("delete from production.recipe_stages where tenant_id=:tenant_id and recipe_version_id=:id"), {"tenant_id": tenant_id, "id": version_id})
            self._insert_children(connection, tenant_id, version_id, payload)
            version = self._read_version(connection, tenant_id, version_id)
            self._complete_idempotency(connection, tenant_id, "recipe_version.update", idempotency_key, version.model_dump(mode="json"), 200)
            return version

    def transition_recipe_version(self, tenant_id: str, version_id: str, action: str, approved_by: str, approval_notes: str | None, effective_from: str | None, idempotency_key: str, request_hash: str) -> RecipeVersionRead | None:
        allowed = {"submit": ("draft", "pending_approval"), "approve": ("pending_approval", "approved"), "obsolete": ("approved", "obsolete")}
        from_status, to_status = allowed[action]
        with self.engine.begin() as connection:
            operation = f"recipe_version.{action}"
            replay = self._claim_idempotency(connection, tenant_id, operation, idempotency_key, request_hash, approved_by)
            if replay is not None:
                return RecipeVersionRead.model_validate(replay)
            version = self._read_version(connection, tenant_id, version_id)
            if version is None or version.status != from_status:
                self._release_idempotency(connection, tenant_id, operation, idempotency_key)
                return None
            if action == "approve" and (not version.resources or not any(stage.status == "active" for stage in version.stages)):
                raise ValueError("recipe_version_incomplete")
            snapshot = json.dumps({
                **version.model_dump(mode="json"),
                "approval_notes": approval_notes,
                "effective_from": effective_from,
            }) if action == "approve" else None
            timestamps = "approved_at=now(), approved_by=:approved_by, snapshot=cast(:snapshot as jsonb)" if action == "approve" else "obsolete_at=now()" if action == "obsolete" else "status=:status"
            status_assignment = "" if action == "submit" else "status=:status, "
            connection.execute(text(f"update production.recipe_versions set {status_assignment}{timestamps}, updated_at=now() where tenant_id=:tenant_id and id=:id"), {"status": to_status, "approved_by": approved_by, "snapshot": snapshot, "tenant_id": tenant_id, "id": version_id})
            if action == "approve":
                connection.execute(text("update production.recipe_versions set status='obsolete', obsolete_at=now(), updated_at=now() where tenant_id=:tenant_id and recipe_id=:recipe_id and status='approved' and id<>:id"), {"tenant_id": tenant_id, "recipe_id": version.recipe_id, "id": version_id})
                connection.execute(text("update production.recipes set status='active', current_version_id=:id, updated_at=now() where tenant_id=:tenant_id and id=:recipe_id"), {"tenant_id": tenant_id, "recipe_id": version.recipe_id, "id": version_id})
                connection.execute(text("update production.product_services set current_recipe_version_id=:id, standard_cost=:cost, updated_at=now() where tenant_id = :tenant_id and id=(select product_service_id from production.recipes where tenant_id=:tenant_id and id=:recipe_id)"), {"tenant_id": tenant_id, "recipe_id": version.recipe_id, "id": version_id, "cost": version.standard_cost})
            result = self._read_version(connection, tenant_id, version_id)
            self._complete_idempotency(connection, tenant_id, operation, idempotency_key, result.model_dump(mode="json"), 200)
            return result

    def _claim_idempotency(self, connection, tenant_id: str, operation: str, key: str, request_hash: str, actor_id: str) -> dict | None:
        claimed = connection.execute(text("""
            insert into production.idempotency_records (id, tenant_id, operation, idempotency_key, request_hash, actor_id)
            values (:id, :tenant_id, :operation, :key, :request_hash, :actor_id)
            on conflict (tenant_id, operation, idempotency_key) do nothing
            returning id
        """), {"id": f"idem_{uuid4().hex[:25]}", "tenant_id": tenant_id, "operation": operation, "key": key, "request_hash": request_hash, "actor_id": actor_id}).first()
        if claimed is not None:
            return None
        record = connection.execute(text("""
            select request_hash, actor_id, state, response_payload
            from production.idempotency_records
            where tenant_id=:tenant_id and operation=:operation and idempotency_key=:key
        """), {"tenant_id": tenant_id, "operation": operation, "key": key}).mappings().one()
        if record["request_hash"] != request_hash:
            raise ErclaveError("idempotency_key_reused", "Idempotency-Key was already used with a different request.", status_code=409)
        if record["actor_id"] != actor_id:
            raise ErclaveError("idempotency_actor_mismatch", "Idempotency-Key belongs to a different actor.", status_code=403)
        if record["state"] != "completed" or record["response_payload"] is None:
            raise ErclaveError("idempotency_request_in_progress", "An identical command is still processing.", status_code=409)
        return record["response_payload"]

    def _complete_idempotency(self, connection, tenant_id: str, operation: str, key: str, payload: dict, status_code: int) -> None:
        connection.execute(text("""
            update production.idempotency_records
            set state='completed', response_payload=cast(:payload as jsonb), status_code=:status_code,
                completed_at=now(), updated_at=now()
            where tenant_id=:tenant_id and operation=:operation and idempotency_key=:key
        """), {"tenant_id": tenant_id, "operation": operation, "key": key, "payload": json.dumps(payload), "status_code": status_code})

    def _release_idempotency(self, connection, tenant_id: str, operation: str, key: str) -> None:
        connection.execute(text("delete from production.idempotency_records where tenant_id=:tenant_id and operation=:operation and idempotency_key=:key and state='processing'"), {"tenant_id": tenant_id, "operation": operation, "key": key})

    def _insert_version(self, connection, tenant_id: str, recipe_id: str, version_id: str, version_number: int, payload) -> None:
        standard_cost = sum(item.quantity * item.unit_cost for item in payload.resources)
        connection.execute(text("""
            insert into production.recipe_versions (id, tenant_id, recipe_id, version_number, base_quantity, base_unit, standard_cost, change_reason)
            values (:id, :tenant_id, :recipe_id, :version_number, :base_quantity, :base_unit, :standard_cost, :change_reason)
        """), {"id": version_id, "tenant_id": tenant_id, "recipe_id": recipe_id, "version_number": version_number, "base_quantity": payload.base_quantity, "base_unit": payload.base_unit, "standard_cost": standard_cost, "change_reason": payload.change_reason})
        self._insert_children(connection, tenant_id, version_id, payload)

    def _insert_children(self, connection, tenant_id: str, version_id: str, payload) -> None:
        for item in payload.resources:
            connection.execute(text("""
                insert into production.recipe_resources (id, tenant_id, recipe_version_id, resource_type, resource_ref_id, resource_code, resource_name, quantity, unit, unit_cost, total_cost, sort_order)
                values (:id, :tenant_id, :version_id, :resource_type, :resource_ref_id, :resource_code, :resource_name, :quantity, :unit, :unit_cost, :total_cost, :sort_order)
            """), {"id": f"rrs_{uuid4().hex[:26]}", "tenant_id": tenant_id, "version_id": version_id, "total_cost": item.quantity * item.unit_cost, **item.model_dump()})
        for item in payload.stages:
            connection.execute(text("""
                insert into production.recipe_stages (id, tenant_id, recipe_version_id, name, description, expected_minutes, sort_order, status)
                values (:id, :tenant_id, :version_id, :name, :description, :expected_minutes, :sort_order, :status)
            """), {"id": f"rst_{uuid4().hex[:26]}", "tenant_id": tenant_id, "version_id": version_id, **item.model_dump()})

    def _read_recipe(self, connection, tenant_id: str, recipe_id: str) -> RecipeRead | None:
        row = connection.execute(text("select id, product_service_id, code, name, status, current_version_id from production.recipes where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": recipe_id}).mappings().first()
        if row is None:
            return None
        version_ids = connection.execute(text("select id from production.recipe_versions where tenant_id=:tenant_id and recipe_id=:recipe_id order by version_number"), {"tenant_id": tenant_id, "recipe_id": recipe_id}).scalars().all()
        return RecipeRead(**dict(row), versions=[self._read_version(connection, tenant_id, item) for item in version_ids])

    def _read_version(self, connection, tenant_id: str, version_id: str) -> RecipeVersionRead | None:
        row = connection.execute(text("select id, recipe_id, version_number, status, base_quantity, base_unit, standard_cost, change_reason, approved_at, approved_by from production.recipe_versions where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": version_id}).mappings().first()
        if row is None:
            return None
        resources = connection.execute(text("select id, resource_type, resource_ref_id, resource_code, resource_name, quantity, unit, unit_cost, total_cost, sort_order from production.recipe_resources where tenant_id=:tenant_id and recipe_version_id=:id order by sort_order"), {"tenant_id": tenant_id, "id": version_id}).mappings().all()
        stages = connection.execute(text("select id, name, description, expected_minutes, sort_order, status from production.recipe_stages where tenant_id=:tenant_id and recipe_version_id=:id order by sort_order"), {"tenant_id": tenant_id, "id": version_id}).mappings().all()
        return RecipeVersionRead(**dict(row), resources=[dict(item) for item in resources], stages=[dict(item) for item in stages])


_repository: ProductionRepository | None = None


def get_production_repository() -> ProductionRepository:
    global _repository
    if _repository is None:
        _repository = ProductionRepository(create_database_engine())
    return _repository
