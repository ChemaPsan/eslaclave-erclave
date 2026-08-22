import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from erclave_common.db import create_database_engine
from erclave_common.errors import ErclaveError

from .schemas import (
    MachineRead, OrderStageUpdateRequest, ProductionOrderRead, ProductionOrderResourceRead, ProductionOrderStageRead, ORDER_STATUS_TRANSITIONS,
    RecipeRead, RecipeVersionRead, ProductServiceRead, ProductionSalesRequestRead, ResourceValidationRead,
    ResourceValidationRow,
)


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
        inventory_mapping: str | None = None,
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
        if inventory_mapping == "missing": filters.append("inventory_item_ref_id is null")
        elif inventory_mapping == "linked": filters.append("inventory_item_ref_id is not null")

        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    f"""
                    select id, code, name, type, category, base_unit, status, target_price, standard_cost, responsible_area, cost_center, expected_margin, description, inventory_item_ref_id inventory_item_id
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
        cost_center: str | None,
        expected_margin: float | None,
        description: str | None,
        inventory_item_id: str | None,
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
                        id, tenant_id, code, name, type, category, base_unit, status, target_price, responsible_area, cost_center, expected_margin, description, inventory_item_ref_id
                    )
                    values (
                        :id, :tenant_id, lower(:code), :name, :type, :category, :base_unit, 'active', :target_price, :responsible_area, :cost_center, :expected_margin, :description, :inventory_item_id
                    )
                    on conflict do nothing
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
                    "cost_center": cost_center,
                    "expected_margin": expected_margin,
                    "description": description,
                    "inventory_item_id": inventory_item_id,
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
        cost_center: str | None,
        expected_margin: float | None,
        description: str | None,
        inventory_item_id: str | None,
    ) -> ProductServiceRead | None:
        try:
            with self.engine.begin() as connection:
                before=self._get_product_service(connection, tenant_id, product_service_id)
                if before is None:
                    return None
                if base_unit is not None and base_unit!=before["base_unit"]:
                    has_recipe=connection.execute(text("select 1 from production.recipes where tenant_id=:tenant_id and product_service_id=:id limit 1"),{"tenant_id":tenant_id,"id":product_service_id}).first()
                    if has_recipe:raise ValueError("product_base_unit_locked_by_recipe")
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
                        cost_center = coalesce(:cost_center, cost_center),
                        expected_margin = coalesce(:expected_margin, expected_margin),
                        description = coalesce(:description, description),
                        inventory_item_ref_id = :inventory_item_id,
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
                    "cost_center": cost_center,
                    "expected_margin": expected_margin,
                    "description": description,
                    "inventory_item_id": inventory_item_id,
                },
                )
                product_service = self._get_product_service(connection, tenant_id, product_service_id)
        except IntegrityError as exc:
            raise ValueError("product_inventory_item_already_mapped") from exc

        return ProductServiceRead.model_validate(dict(product_service)) if product_service else None

    def link_product_inventory_item(self, tenant_id: str, product_service_id: str, inventory_item_id: str) -> ProductServiceRead | None:
        try:
            with self.engine.begin() as connection:
                before = self._get_product_service(connection, tenant_id, product_service_id)
                if before is None: return None
                if before["inventory_item_id"] and before["inventory_item_id"] != inventory_item_id:
                    raise ValueError("product_inventory_item_already_linked")
                connection.execute(text("update production.product_services set inventory_item_ref_id = :item, updated_at=now() where tenant_id = :tenant_id and id = :id"), {"item":inventory_item_id,"tenant_id":tenant_id,"id":product_service_id})
                product_service = self._get_product_service(connection, tenant_id, product_service_id)
        except IntegrityError as exc:
            raise ValueError("product_inventory_item_already_mapped") from exc
        return ProductServiceRead.model_validate(dict(product_service))

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
                select id, code, name, type, category, base_unit, status, target_price, standard_cost, responsible_area, cost_center, expected_margin, description, inventory_item_ref_id inventory_item_id
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

    def get_recipe_version(self,tenant_id:str,version_id:str)->RecipeVersionRead|None:
        with self.engine.connect() as connection:return self._read_version(connection,tenant_id,version_id)

    def normalize_recipe_payload(self,tenant_id:str,payload,product_service_id:str|None=None,recipe_id:str|None=None):
        with self.engine.connect() as connection:
            if recipe_id:
                product_service_id=connection.execute(text("select product_service_id from production.recipes where tenant_id=:t and id=:i"),{"t":tenant_id,"i":recipe_id}).scalar_one_or_none()
            product=self._get_product_service(connection,tenant_id,product_service_id) if product_service_id else None
            if not product or product["status"]!="active":raise ValueError("active_product_service_required")
            if product["base_unit"]!=payload.base_unit:raise ValueError("recipe_unit_must_match_product_base_unit")
            normalized=[]
            for item in payload.resources:
                if item.resource_type=="machine":
                    machine=connection.execute(text("select id,code,name,area_ref_id,cost_per_minute,status from production.machines where tenant_id=:t and id=:i"),{"t":tenant_id,"i":item.resource_ref_id}).mappings().first()
                    if not machine or machine["status"]!="active" or not machine["area_ref_id"]:raise ValueError("machine_resource_invalid")
                    if item.unit!="MIN":raise ValueError("timed_resource_unit_must_be_minute")
                    normalized.append(item.model_copy(update={"resource_code":machine["code"],"resource_name":machine["name"],"unit_cost":float(machine["cost_per_minute"])}))
                elif item.resource_type=="other":raise ValueError("resource_type_not_authoritative")
                else:normalized.append(item)
            return payload.model_copy(update={"resources":normalized})

    def create_recipe(self, tenant_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str) -> RecipeRead | None:
        recipe_id = f"rec_{uuid4().hex[:26]}"
        version_id = f"rcv_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "recipe.create", idempotency_key, request_hash, actor_id)
            if replay is not None:
                return RecipeRead.model_validate(replay)
            product = self._get_product_service(connection, tenant_id, payload.product_service_id)
            if product is None or product["status"]!="active" or product["base_unit"]!=payload.base_unit:
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
            recipe = connection.execute(text("select r.id,p.status product_status,p.base_unit product_unit from production.recipes r join production.product_services p on p.tenant_id=r.tenant_id and p.id=r.product_service_id where r.tenant_id=:tenant_id and r.id=:id for update of r"), {"tenant_id": tenant_id, "id": recipe_id}).mappings().first()
            if recipe is None:
                self._release_idempotency(connection, tenant_id, "recipe_version.create", idempotency_key)
                return None
            if recipe["product_status"]!="active" or recipe["product_unit"]!=payload.base_unit:raise ValueError("active_product_and_matching_unit_required")
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
            row = connection.execute(text("select v.id,p.status product_status,p.base_unit product_unit from production.recipe_versions v join production.recipes r on r.tenant_id=v.tenant_id and r.id=v.recipe_id join production.product_services p on p.tenant_id=r.tenant_id and p.id=r.product_service_id where v.tenant_id=:tenant_id and v.id=:id and v.status='draft'"), {"tenant_id": tenant_id, "id": version_id}).mappings().first()
            if row is None:
                self._release_idempotency(connection, tenant_id, "recipe_version.update", idempotency_key)
                return None
            if row["product_status"]!="active" or row["product_unit"]!=payload.base_unit:raise ValueError("active_product_and_matching_unit_required")
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
            active_stages=[stage for stage in version.stages if stage.status == "active"]
            if action == "approve" and abs(sum(float(stage.weight_percent) for stage in active_stages) - 100) > 0.01:
                raise ValueError("active_recipe_stage_weight_must_total_100")
            if action=="approve":
                product=connection.execute(text("select p.status,p.base_unit from production.product_services p join production.recipes r on r.tenant_id=p.tenant_id and r.product_service_id=p.id where r.tenant_id=:t and r.id=:i"),{"t":tenant_id,"i":version.recipe_id}).mappings().one()
                if product["status"]!="active" or product["base_unit"]!=version.base_unit:raise ValueError("active_product_and_matching_unit_required")
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

    def list_machines(self, tenant_id: str, q: str | None = None, status: str | None = None) -> list[MachineRead]:
        filters = ["tenant_id=:tenant_id"]
        params = {"tenant_id": tenant_id}
        if q:
            filters.append("(code ilike :q or name ilike :q or machine_type ilike :q or area_name ilike :q)")
            params["q"] = f"%{q}%"
        if status:
            filters.append("status=:status")
            params["status"] = status
        with self.engine.connect() as connection:
            rows = connection.execute(text(f"select id,code,name,machine_type,area_ref_id,area_name,available_minutes_per_day,cost_per_minute,status from production.machines where {' and '.join(filters)} order by code"), params).mappings().all()
        return [MachineRead.model_validate(dict(row)) for row in rows]

    def create_machine(self, tenant_id: str, payload, key: str, request_hash: str, actor_id: str) -> MachineRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "machine.create", key, request_hash, actor_id)
            if replay is not None:
                return MachineRead.model_validate(replay)
            machine_id = f"maq_{uuid4().hex[:26]}"
            row = connection.execute(text("""
                insert into production.machines(id,tenant_id,code,name,machine_type,area_ref_id,area_name,available_minutes_per_day,cost_per_minute)
                values(:id,:tenant_id,lower(:code),:name,:machine_type,:area_ref_id,:area_name,:available_minutes_per_day,:cost_per_minute)
                on conflict(tenant_id,code) do nothing
                returning id,code,name,machine_type,area_ref_id,area_name,available_minutes_per_day,cost_per_minute,status
            """), {"id": machine_id, "tenant_id": tenant_id, **payload.model_dump()}).mappings().first()
            if row is None:
                self._release_idempotency(connection, tenant_id, "machine.create", key)
                return None
            value = MachineRead.model_validate(dict(row))
            self._audit(connection, tenant_id, actor_id, "machine.create", "machine", machine_id, None, value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, "machine.create", key, value.model_dump(mode="json"), 201)
            return value

    def update_machine(self, tenant_id: str, machine_id: str, payload, key: str, request_hash: str, actor_id: str) -> MachineRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "machine.update", key, request_hash, actor_id)
            if replay is not None:
                return MachineRead.model_validate(replay)
            before = connection.execute(text("select id,code,name,machine_type,area_ref_id,area_name,available_minutes_per_day,cost_per_minute,status from production.machines where tenant_id=:tenant_id and id=:id for update"), {"tenant_id": tenant_id, "id": machine_id}).mappings().first()
            if before is None:
                self._release_idempotency(connection, tenant_id, "machine.update", key)
                return None
            data = payload.model_dump(exclude_none=True)
            if data:
                sets = ",".join(f"{name}=:{name}" for name in data)
                connection.execute(text(f"update production.machines set {sets},updated_at=now() where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": machine_id, **data})
            after = connection.execute(text("select id,code,name,machine_type,area_ref_id,area_name,available_minutes_per_day,cost_per_minute,status from production.machines where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": machine_id}).mappings().one()
            value = MachineRead.model_validate(dict(after))
            self._audit(connection, tenant_id, actor_id, "machine.update", "machine", machine_id, dict(before), value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, "machine.update", key, value.model_dump(mode="json"), 200)
            return value

    def validate_resources(self, tenant_id: str, payload, observations, key: str, request_hash: str, actor_id: str) -> ResourceValidationRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "resource.validate", key, request_hash, actor_id)
            if replay is not None:
                return ResourceValidationRead.model_validate(replay)
            value = self._validate_resources(connection, tenant_id, payload,observations)
            if value is None:
                self._release_idempotency(connection, tenant_id, "resource.validate", key)
                return None
            self._complete_idempotency(connection, tenant_id, "resource.validate", key, value.model_dump(mode="json"), 200)
            return value

    def preview_resources(self,tenant_id:str,payload,observations)->ResourceValidationRead|None:
        with self.engine.connect() as connection:return self._validate_resources(connection,tenant_id,payload,observations)

    def _validate_resources(self, connection, tenant_id: str, payload,observations) -> ResourceValidationRead | None:
        from datetime import date,datetime, timezone
        version = self._read_version(connection, tenant_id, payload.recipe_version_id)
        current=connection.execute(text("""select r.current_version_id,p.status product_status from production.recipes r join production.product_services p on p.tenant_id=r.tenant_id and p.id=r.product_service_id
            where r.tenant_id=:t and r.id=:i"""),{"t":tenant_id,"i":version.recipe_id if version else ""}).mappings().first()
        if version is None or version.status != "approved" or version.base_unit != payload.unit or not current or current["current_version_id"]!=version.id or current["product_status"]!="active":
            return None
        scale = payload.quantity / version.base_quantity
        observed = {(item.resource_type, item.resource_ref_id, item.unit): item for item in observations}
        planned_date=payload.planned_for or date.today()
        rows, blockers = [], []
        for resource in version.resources:
            required = resource.quantity * scale
            observation = observed.get((resource.resource_type, resource.resource_ref_id or "", resource.unit))
            available = observation.available_quantity if observation else 0
            source = observation.source if observation else "unavailable"
            if resource.resource_type == "machine" and resource.resource_ref_id:
                machine = connection.execute(text("select available_minutes_per_day,cost_per_minute,status from production.machines where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": resource.resource_ref_id}).mappings().first()
                if machine:
                    committed=float(connection.execute(text("select coalesce(sum(quantity_minutes),0) from production.capacity_commitments where tenant_id=:t and resource_type='machine' and resource_ref_id=:i and planned_date=:d and status='active'"),{"t":tenant_id,"i":resource.resource_ref_id,"d":planned_date}).scalar_one())
                    available = max(0,float(machine["available_minutes_per_day"])-committed) if machine["status"] == "active" else 0
                    source = "production.machines"
                    unit_cost = float(machine["cost_per_minute"])
                else:
                    unit_cost = resource.unit_cost
            elif resource.resource_type=="labor" and observation:
                committed=float(connection.execute(text("select coalesce(sum(quantity_minutes),0) from production.capacity_commitments where tenant_id=:t and resource_type='labor' and resource_ref_id=:i and planned_date=:d and status='active'"),{"t":tenant_id,"i":resource.resource_ref_id,"d":planned_date}).scalar_one())
                available=max(0,float(observation.available_quantity)-committed);unit_cost=observation.unit_cost if observation.unit_cost is not None else resource.unit_cost
            else:
                unit_cost = observation.unit_cost if observation and observation.unit_cost is not None else resource.unit_cost
            ok = available >= required
            blocker = None if ok else (f"invalid_{resource.resource_type}:{resource.resource_code}" if not observation and resource.resource_type!="machine" else f"insufficient_{resource.resource_type}:{resource.resource_code}")
            if blocker:
                blockers.append(blocker)
            rows.append(ResourceValidationRow(resource_type=resource.resource_type,resource_ref_id=resource.resource_ref_id,resource_code=resource.resource_code,resource_name=resource.resource_name,unit=resource.unit,required_quantity=required,available_quantity=available,unit_cost=unit_cost,total_cost=required*unit_cost,source=source,ok=ok,blocker_code=blocker,allocations=observation.allocations if observation else []))
        return ResourceValidationRead(recipe_version_id=version.id,quantity=payload.quantity,unit=payload.unit,can_release=not blockers,planned_cost=sum(row.total_cost for row in rows),validated_at=datetime.now(timezone.utc),rows=rows,blockers=blockers)

    def list_orders(self, tenant_id: str, limit: int = 50, status: str | None = None) -> list[ProductionOrderRead]:
        filters = ["tenant_id=:tenant_id"]
        params = {"tenant_id": tenant_id, "limit": limit}
        if status:
            filters.append("status=:status")
            params["status"] = status
        with self.engine.connect() as connection:
            ids = connection.execute(text(f"select id from production.production_orders where {' and '.join(filters)} order by created_at desc limit :limit"), params).scalars().all()
            return [self._read_order(connection, tenant_id, order_id) for order_id in ids]

    def get_order(self, tenant_id: str, order_id: str) -> ProductionOrderRead | None:
        with self.engine.connect() as connection:
            return self._read_order(connection, tenant_id, order_id)

    def preflight_order_status(self, tenant_id: str, order_id: str, target_status: str) -> ProductionOrderRead | None:
        with self.engine.connect() as connection:
            before = self._read_order(connection, tenant_id, order_id)
            if before is None:
                return None
            if target_status not in ORDER_STATUS_TRANSITIONS[before.status]:
                raise ValueError("invalid_order_transition")
            if target_status == "in_progress":
                self._require_material_reservations(connection, tenant_id, order_id)
            if target_status == "in_validation":
                self._require_stages_complete(connection, tenant_id, order_id)
            if target_status == "completed":
                self._require_completion_preconditions(connection, tenant_id, order_id)
            return before

    def _require_material_reservations(self, connection, tenant_id: str, order_id: str) -> None:
        unreserved_material=connection.execute(text("""select 1 from production.production_order_resources r
            where r.tenant_id=:tenant_id and r.production_order_id=:order_id and r.resource_type='material'
            and not exists (select 1 from production.production_order_resource_reservations rr
              where rr.tenant_id=r.tenant_id and rr.production_order_resource_id=r.id) limit 1"""),{"tenant_id":tenant_id,"order_id":order_id}).first()
        if unreserved_material:
            raise ValueError("material_reservation_required")

    def _require_completion_preconditions(self, connection, tenant_id: str, order_id: str) -> None:
        self._require_material_reservations(connection, tenant_id, order_id)
        unconsumed_material=connection.execute(text("""select 1 from production.production_order_resources
            where tenant_id=:tenant_id and production_order_id=:order_id and resource_type='material'
            and (actual_quantity is null or actual_cost is null) limit 1"""),{"tenant_id":tenant_id,"order_id":order_id}).first()
        if unconsumed_material:
            raise ValueError("material_consumption_required")
        self._require_stages_complete(connection, tenant_id, order_id)
    def _require_stages_complete(self, connection, tenant_id: str, order_id: str) -> None:
        incomplete_stage=connection.execute(text("""select 1 from production.production_order_stages
            where tenant_id=:tenant_id and production_order_id=:order_id
            and (status not in ('completed','skipped') or progress_percent<>100) limit 1"""),{"tenant_id":tenant_id,"order_id":order_id}).first()
        if incomplete_stage:
            raise ValueError("production_stages_incomplete")

    def create_order(self, tenant_id: str, payload, observations,order_id:str,reservation_refs:dict[tuple[str,str],list[str]], key: str, request_hash: str, actor_id: str) -> ProductionOrderRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "order.create", key, request_hash, actor_id)
            if replay is not None:
                return ProductionOrderRead.model_validate(replay)
            from datetime import date
            for item in observations:
                if item.resource_type in {"labor","machine"}:connection.execute(text("select pg_advisory_xact_lock(hashtextextended(:k,0))"),{"k":f"production:{tenant_id}:{item.resource_type}:{item.resource_ref_id}:{payload.planned_for or date.today()}"})
            validation = self._validate_resources(connection, tenant_id, payload,observations)
            if validation is None or not validation.can_release:
                self._release_idempotency(connection, tenant_id, "order.create", key)
                raise ValueError("resources_unavailable" if validation else "approved_recipe_required")
            version = self._read_version(connection, tenant_id, payload.recipe_version_id)
            recipe = self._read_recipe(connection, tenant_id, version.recipe_id)
            active_stage_ids={stage.id for stage in version.stages if stage.status=="active"}
            assignments = {item.recipe_stage_id: item for item in payload.stage_assignments}
            if set(assignments)!=active_stage_ids:raise ValueError("all_active_stages_require_one_assignment")
            code = payload.code or f"OP-{uuid4().hex[:10].upper()}"
            if connection.execute(text("select 1 from production.production_orders where tenant_id=:tenant_id and lower(code)=lower(:code)"), {"tenant_id":tenant_id,"code":code}).first():
                self._release_idempotency(connection, tenant_id, "order.create", key)
                raise ValueError("production_order_code_already_exists")
            recipe_snapshot = recipe.model_dump(mode="json")
            connection.execute(text("""
                insert into production.production_orders(id,tenant_id,code,product_service_id,recipe_id,recipe_version_id,quantity,unit,status,priority,required_at,responsible_worker_ref_id,responsible_name_snapshot,planned_start_at,source_type,source_id,source_line_id,planned_cost,recipe_snapshot,resource_validation_snapshot,validated_at,created_by)
                values(:id,:tenant_id,:code,:product_service_id,:recipe_id,:recipe_version_id,:quantity,:unit,'released',:priority,:required_at,:responsible_worker_id,:responsible,:planned_start_at,:source_type,:source_id,:source_line_id,:planned_cost,cast(:recipe_snapshot as jsonb),cast(:validation as jsonb),:validated_at,:actor_id)
            """), {"id":order_id,"tenant_id":tenant_id,"code":code,"product_service_id":recipe.product_service_id,"recipe_id":recipe.id,"recipe_version_id":version.id,"quantity":payload.quantity,"unit":payload.unit,"priority":payload.priority,"required_at":payload.required_at,"responsible_worker_id":payload.responsible_worker_id,"responsible":payload.responsible_name,"planned_start_at":payload.planned_start_at,"source_type":payload.source_type,"source_id":payload.source_id,"source_line_id":payload.source_line_id,"planned_cost":validation.planned_cost,"recipe_snapshot":json.dumps(recipe_snapshot),"validation":json.dumps(validation.model_dump(mode="json")),"validated_at":validation.validated_at,"actor_id":actor_id})
            planned_date=payload.planned_for or (payload.planned_start_at.date() if payload.planned_start_at else payload.required_at.date() if payload.required_at else date.today())
            for row in validation.rows:
                resource_row_id=f"por_{uuid4().hex[:26]}";resource_reservations=reservation_refs.get((row.resource_ref_id or "",row.unit),[]);reservation_ref=resource_reservations[0] if resource_reservations else None
                connection.execute(text("""insert into production.production_order_resources(id,tenant_id,production_order_id,resource_type,resource_ref_id,resource_code,resource_name_snapshot,unit,planned_quantity,unit_cost_snapshot,planned_cost,reservation_ref_id)
                    values(:id,:t,:order_id,:type,:ref,:code,:name,:unit,:quantity,:cost,:total,:reservation)"""),{"id":resource_row_id,"t":tenant_id,"order_id":order_id,"type":row.resource_type,"ref":row.resource_ref_id,"code":row.resource_code,"name":row.resource_name,"unit":row.unit,"quantity":row.required_quantity,"cost":row.unit_cost,"total":row.total_cost,"reservation":reservation_ref})
                for reservation_id in resource_reservations:
                    connection.execute(text("""insert into production.production_order_resource_reservations(id,tenant_id,production_order_resource_id,reservation_ref_id)
                        values(:id,:tenant_id,:resource_id,:reservation_id)"""),{"id":f"prr_{uuid4().hex[:26]}","tenant_id":tenant_id,"resource_id":resource_row_id,"reservation_id":reservation_id})
                if row.resource_type in {"labor","machine"}:connection.execute(text("""insert into production.capacity_commitments(id,tenant_id,production_order_id,resource_type,resource_ref_id,planned_date,quantity_minutes)
                    values(:id,:t,:order_id,:type,:ref,:planned_date,:quantity)"""),{"id":f"cap_{uuid4().hex[:26]}","t":tenant_id,"order_id":order_id,"type":row.resource_type,"ref":row.resource_ref_id,"planned_date":planned_date,"quantity":row.required_quantity})
            for stage in version.stages:
                if stage.status != "active": continue
                connection.execute(text("""
                    insert into production.production_order_stages(id,tenant_id,production_order_id,recipe_stage_id,labor_area_ref_id,labor_area_name_snapshot,weight_percent,name,description_snapshot,sort_order,status,planned_minutes,responsible_worker_ref_id,responsible_name_snapshot)
                    values(:id,:tenant_id,:order_id,:recipe_stage_id,:labor_area_ref_id,:labor_area_name,:weight_percent,:name,:description,:sort_order,'pending',:planned_minutes,:responsible_worker_id,:responsible)
                """), {"id":f"ost_{uuid4().hex[:26]}","tenant_id":tenant_id,"order_id":order_id,"recipe_stage_id":stage.id,"labor_area_ref_id":stage.labor_area_ref_id,"labor_area_name":stage.labor_area_name,"weight_percent":stage.weight_percent,"name":stage.name,"description":stage.description,"sort_order":stage.sort_order,"planned_minutes":stage.expected_minutes*(payload.quantity/version.base_quantity) if stage.expected_minutes is not None else None,"responsible_worker_id":assignments.get(stage.id).responsible_worker_id if assignments.get(stage.id) else None,"responsible":assignments.get(stage.id).responsible_name if assignments.get(stage.id) else None})
            value = self._read_order(connection, tenant_id, order_id)
            self._audit(connection, tenant_id, actor_id, "order.create", "production_order", order_id, None, value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, "order.create", key, value.model_dump(mode="json"), 201)
            return value

    def update_order_status(self, tenant_id: str, order_id: str, payload, key: str, request_hash: str, actor_id: str, material_actuals:dict[str,dict]|None=None) -> ProductionOrderRead | None:
        allowed = ORDER_STATUS_TRANSITIONS
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "order.status", key, request_hash, actor_id)
            if replay is not None: return ProductionOrderRead.model_validate(replay)
            before = self._read_order(connection, tenant_id, order_id)
            if before is None:
                self._release_idempotency(connection, tenant_id, "order.status", key); return None
            if payload.status not in allowed[before.status]:
                self._release_idempotency(connection, tenant_id, "order.status", key); raise ValueError("invalid_order_transition")
            if payload.status == "in_progress":
                try:self._require_material_reservations(connection,tenant_id,order_id)
                except ValueError:
                    self._release_idempotency(connection, tenant_id, "order.status", key);raise
            if payload.status == "completed":
                try:self._require_completion_preconditions(connection,tenant_id,order_id)
                except ValueError:
                    self._release_idempotency(connection, tenant_id, "order.status", key);raise
            if payload.status == "in_progress" and before.status in {"released","waiting_resources"}:
                material_actuals=material_actuals or {}
                material_rows=connection.execute(text("""select r.id,rr.reservation_ref_id from production.production_order_resources r
                    left join production.production_order_resource_reservations rr on rr.tenant_id=r.tenant_id and rr.production_order_resource_id=r.id
                    where r.tenant_id=:tenant_id and r.production_order_id=:order_id and r.resource_type='material' order by r.id"""),{"tenant_id":tenant_id,"order_id":order_id}).mappings().all()
                grouped={}
                for row in material_rows: grouped.setdefault(row["id"],[]).append(row["reservation_ref_id"])
                for resource_id,reservations in grouped.items():
                    values=[material_actuals.get(item) for item in reservations if item]
                    if not values or any(item is None for item in values):
                        self._release_idempotency(connection, tenant_id, "order.status", key);raise ValueError("material_consumption_required")
                    quantity=sum(float(item["quantity"]) for item in values);cost=sum(float(item["cost"]) for item in values)
                    connection.execute(text("update production.production_order_resources set actual_quantity=:quantity,actual_cost=:cost,updated_at=now() where tenant_id=:tenant_id and id=:id"),{"quantity":quantity,"cost":cost,"tenant_id":tenant_id,"id":resource_id})
            if payload.status in {"in_progress","completed"}:
                actual_cost=float(connection.execute(text("select coalesce(sum(actual_cost),0) from production.production_order_resources where tenant_id=:tenant_id and production_order_id=:order_id"),{"tenant_id":tenant_id,"order_id":order_id}).scalar_one())
            else: actual_cost=None
            timestamps = ",actual_start_at=coalesce(actual_start_at,now())" if payload.status == "in_progress" else ",actual_end_at=now()" if payload.status in {"completed","cancelled"} else ""
            connection.execute(text(f"update production.production_orders set status=:status,actual_cost=coalesce(:actual_cost,actual_cost),updated_at=now(){timestamps} where tenant_id=:tenant_id and id=:id"), {"status":payload.status,"actual_cost":actual_cost,"tenant_id":tenant_id,"id":order_id})
            if payload.status in {"completed","cancelled"}:
                commitment_status="completed" if payload.status=="completed" else "released"
                connection.execute(text("update production.capacity_commitments set status=:status,updated_at=now() where tenant_id=:tenant_id and production_order_id=:order_id and status='active'"),{"status":commitment_status,"tenant_id":tenant_id,"order_id":order_id})
            value = self._read_order(connection, tenant_id, order_id)
            self._audit(connection, tenant_id, actor_id, "order.status", "production_order", order_id, before.model_dump(mode="json"), {**value.model_dump(mode="json"),"reason":payload.reason}, key)
            self._complete_idempotency(connection, tenant_id, "order.status", key, value.model_dump(mode="json"), 200)
            return value

    def update_order_resource_actual(self, tenant_id:str, order_id:str, resource_id:str, payload, key:str, request_hash:str, actor_id:str) -> ProductionOrderResourceRead | None:
        with self.engine.begin() as connection:
            replay=self._claim_idempotency(connection,tenant_id,"order_resource.actual",key,request_hash,actor_id)
            if replay is not None:return ProductionOrderResourceRead.model_validate(replay)
            order_status=connection.execute(text("select status from production.production_orders where tenant_id=:tenant_id and id=:order_id for update"),{"tenant_id":tenant_id,"order_id":order_id}).scalar_one_or_none()
            if order_status is None:self._release_idempotency(connection,tenant_id,"order_resource.actual",key);return None
            if order_status in {"completed","cancelled"}:self._release_idempotency(connection,tenant_id,"order_resource.actual",key);raise ValueError("terminal_order_resource_locked")
            before=self._read_order_resource(connection,tenant_id,resource_id,order_id)
            if before is None:self._release_idempotency(connection,tenant_id,"order_resource.actual",key);return None
            if before.resource_type=="material":self._release_idempotency(connection,tenant_id,"order_resource.actual",key);raise ValueError("material_actual_is_inventory_owned")
            actual_cost=float(payload.actual_quantity)*float(before.unit_cost)
            connection.execute(text("update production.production_order_resources set actual_quantity=:quantity,actual_cost=:cost,updated_at=now() where tenant_id=:tenant_id and production_order_id=:order_id and id=:id"),{"quantity":payload.actual_quantity,"cost":actual_cost,"tenant_id":tenant_id,"order_id":order_id,"id":resource_id})
            value=self._read_order_resource(connection,tenant_id,resource_id,order_id)
            self._audit(connection,tenant_id,actor_id,"order_resource.actual","production_order_resource",resource_id,before.model_dump(mode="json"),value.model_dump(mode="json"),key)
            self._complete_idempotency(connection,tenant_id,"order_resource.actual",key,value.model_dump(mode="json"),200)
            return value

    def update_order_stage(self, tenant_id: str, stage_id: str, payload: OrderStageUpdateRequest, key: str, request_hash: str, actor_id: str) -> ProductionOrderStageRead | None:
        allowed = {"pending":{"pending","in_progress","completed","blocked","skipped"},"in_progress":{"pending","in_progress","completed","blocked"},"blocked":{"pending","in_progress","completed","blocked","skipped"},"completed":set(),"skipped":set()}
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "order_stage.update", key, request_hash, actor_id)
            if replay is not None: return ProductionOrderStageRead.model_validate(replay)
            before = self._read_stage(connection, tenant_id, stage_id)
            if before is None:
                self._release_idempotency(connection, tenant_id, "order_stage.update", key); return None
            order_id = connection.execute(text("select production_order_id from production.production_order_stages where tenant_id=:tenant_id and id=:id"), {"tenant_id":tenant_id,"id":stage_id}).scalar_one()
            order_status = connection.execute(text("select status from production.production_orders where tenant_id=:tenant_id and id=:id for update"), {"tenant_id":tenant_id,"id":order_id}).scalar_one()
            if payload.status in {"in_progress","completed"} and order_status != "in_progress":
                self._release_idempotency(connection, tenant_id, "order_stage.update", key); raise ValueError("production_order_must_be_in_progress")
            if payload.status not in allowed[before.status]:
                self._release_idempotency(connection, tenant_id, "order_stage.update", key); raise ValueError("invalid_stage_transition")
            connection.execute(text("""
                update production.production_order_stages set status=:status,actual_minutes=coalesce(:actual_minutes,actual_minutes),notes=coalesce(:notes,notes),progress_percent=:progress,
                started_at=case when cast(:status as varchar) in ('in_progress','completed') then coalesce(started_at,now()) else started_at end,
                completed_at=case when cast(:status as varchar) in ('completed','skipped') then now() else completed_at end,updated_at=now()
                where tenant_id=:tenant_id and id=:id
            """), {"status":payload.status,"actual_minutes":payload.actual_minutes,"notes":payload.notes,"progress":payload.progress_percent,"tenant_id":tenant_id,"id":stage_id})
            value = self._read_stage(connection, tenant_id, stage_id)
            statuses = set(connection.execute(text("select status from production.production_order_stages where tenant_id=:tenant_id and production_order_id=:id"), {"tenant_id":tenant_id,"id":order_id}).scalars())
            if statuses and statuses <= {"completed","skipped"}: connection.execute(text("update production.production_orders set status='in_validation',updated_at=now() where tenant_id=:tenant_id and id=:id and status='in_progress'"), {"tenant_id":tenant_id,"id":order_id})
            self._audit(connection, tenant_id, actor_id, "order_stage.update", "production_order_stage", stage_id, before.model_dump(mode="json"), value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, "order_stage.update", key, value.model_dump(mode="json"), 200)
            return value

    def _read_stage(self, connection, tenant_id: str, stage_id: str) -> ProductionOrderStageRead | None:
        row = connection.execute(text("select id,recipe_stage_id,labor_area_ref_id,labor_area_name_snapshot labor_area_name,weight_percent,name,sort_order,status,planned_minutes,actual_minutes,responsible_worker_ref_id responsible_worker_id,responsible_name_snapshot responsible_name,progress_percent,started_at,completed_at,notes from production.production_order_stages where tenant_id=:tenant_id and id=:id"), {"tenant_id":tenant_id,"id":stage_id}).mappings().first()
        return ProductionOrderStageRead.model_validate(dict(row)) if row else None

    def _read_order_resource(self,connection,tenant_id:str,resource_id:str,order_id:str|None=None)->ProductionOrderResourceRead|None:
        params={"tenant_id":tenant_id,"id":resource_id};order_filter=""
        if order_id is not None:params["order_id"]=order_id;order_filter=" and production_order_id=:order_id"
        row=connection.execute(text("""select id,resource_type,resource_ref_id,resource_code,resource_name_snapshot resource_name,unit,
            planned_quantity,actual_quantity,unit_cost_snapshot unit_cost,planned_cost,actual_cost,reservation_ref_id
            from production.production_order_resources where tenant_id=:tenant_id and id=:id"""+order_filter),params).mappings().first()
        if row is None:return None
        refs=connection.execute(text("select reservation_ref_id from production.production_order_resource_reservations where tenant_id=:tenant_id and production_order_resource_id=:id order by reservation_ref_id"),{"tenant_id":tenant_id,"id":resource_id}).scalars().all()
        return ProductionOrderResourceRead(**dict(row),reservation_ref_ids=list(refs))

    def _read_order(self, connection, tenant_id: str, order_id: str) -> ProductionOrderRead | None:
        row = connection.execute(text("""
            select id,code,product_service_id,recipe_id,recipe_version_id,quantity,unit,status,priority,required_at,planned_start_at,actual_start_at,actual_end_at,responsible_worker_ref_id responsible_worker_id,responsible_name_snapshot responsible_name,source_type,source_id,planned_cost,actual_cost,recipe_snapshot,resource_validation_snapshot,created_at
            from production.production_orders where tenant_id=:tenant_id and id=:id
        """), {"tenant_id":tenant_id,"id":order_id}).mappings().first()
        if row is None: return None
        stage_ids = connection.execute(text("select id from production.production_order_stages where tenant_id=:tenant_id and production_order_id=:id order by sort_order"), {"tenant_id":tenant_id,"id":order_id}).scalars().all()
        resource_ids=connection.execute(text("select id from production.production_order_resources where tenant_id=:tenant_id and production_order_id=:id order by resource_type,resource_code"),{"tenant_id":tenant_id,"id":order_id}).scalars().all()
        stages=[self._read_stage(connection, tenant_id, item) for item in stage_ids]
        overall_progress=sum(float(item.weight_percent)*float(item.progress_percent)/100 for item in stages)
        return ProductionOrderRead(**dict(row), overall_progress_percent=round(overall_progress,2), stages=stages,resources=[self._read_order_resource(connection,tenant_id,item,order_id) for item in resource_ids])

    def _read_sales_request(self, connection, tenant_id: str, request_id: str):
        row = connection.execute(text("""select id,sales_order_id,sales_order_line_id,product_service_ref_id product_service_id,
            product_service_code_snapshot product_service_code,product_service_name_snapshot product_service_name,
            recipe_version_ref_id recipe_version_id,quantity,unit,requested_due_date,status,created_at
            from production.sales_order_requests where tenant_id=:tenant and id=:id"""), {"tenant": tenant_id, "id": request_id}).mappings().first()
        return ProductionSalesRequestRead.model_validate(dict(row)) if row else None

    def list_sales_order_requests(self, tenant_id: str, status: str | None = None):
        condition = " and status=:status" if status else ""
        params = {"tenant": tenant_id, "status": status}
        with self.engine.connect() as connection:
            ids = connection.execute(text(f"select id from production.sales_order_requests where tenant_id=:tenant{condition} order by created_at desc limit 200"), params).scalars().all()
            return [self._read_sales_request(connection, tenant_id, item) for item in ids]

    def create_sales_order_request(self, tenant_id: str, payload, key: str, request_hash: str, actor_id: str):
        operation = "sales_order_request.create"
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, operation, key, request_hash, actor_id)
            if replay is not None:
                return ProductionSalesRequestRead.model_validate(replay)
            product = connection.execute(text("""select id,code,name,type,base_unit,status,current_recipe_version_id
                from production.product_services where tenant_id=:tenant and id=:id for share"""), {"tenant": tenant_id, "id": payload.product_service_id}).mappings().first()
            if not product or product["type"] != "product" or product["status"] != "active" or product["base_unit"] != payload.unit or not product["current_recipe_version_id"]:
                self._release_idempotency(connection, tenant_id, operation, key)
                raise ValueError("production_request_requires_approved_recipe")
            approved = connection.execute(text("select id from production.recipe_versions where tenant_id=:tenant and id=:id and status='approved'"), {"tenant": tenant_id, "id": product["current_recipe_version_id"]}).scalar_one_or_none()
            if not approved:
                self._release_idempotency(connection, tenant_id, operation, key)
                raise ValueError("production_request_requires_approved_recipe")
            request_id = f"por_{uuid4().hex[:26]}"
            inserted = connection.execute(text("""insert into production.sales_order_requests(id,tenant_id,sales_order_id,sales_order_line_id,
                product_service_ref_id,product_service_code_snapshot,product_service_name_snapshot,recipe_version_ref_id,quantity,unit,
                requested_due_date,status,created_by)
                values(:id,:tenant,:order_id,:line_id,:product_id,:code,:name,:recipe,:quantity,:unit,:due,'pending_configuration',:actor)
                on conflict(tenant_id,sales_order_line_id) do nothing returning id"""), {"id": request_id, "tenant": tenant_id,
                "order_id": payload.sales_order_id, "line_id": payload.sales_order_line_id, "product_id": product["id"],
                "code": product["code"], "name": product["name"], "recipe": approved, "quantity": payload.quantity,
                "unit": payload.unit, "due": payload.requested_due_date, "actor": actor_id}).scalar_one_or_none()
            if not inserted:
                existing = connection.execute(text("select id from production.sales_order_requests where tenant_id=:tenant and sales_order_line_id=:line"), {"tenant": tenant_id, "line": payload.sales_order_line_id}).scalar_one()
                value = self._read_sales_request(connection, tenant_id, existing)
                if (
                    value.sales_order_id != payload.sales_order_id
                    or value.product_service_id != payload.product_service_id
                    or value.quantity != payload.quantity
                    or value.unit != payload.unit
                    or value.requested_due_date != payload.requested_due_date
                ):
                    self._release_idempotency(connection, tenant_id, operation, key)
                    raise ErclaveError(
                        "production_request_source_conflict",
                        "The sales order line already has a production request with different source data.",
                        status_code=409,
                    )
            else:
                value = self._read_sales_request(connection, tenant_id, request_id)
            self._audit(connection, tenant_id, actor_id, operation, "sales_order_request", value.id, None, value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, operation, key, value.model_dump(mode="json"), 201)
            return value

    def _audit(self, connection, tenant_id: str, actor_id: str, action: str, resource_type: str, resource_id: str, before, after, key: str) -> None:
        connection.execute(text("insert into production.audit_events(id,tenant_id,actor_id,action,resource_type,resource_id,before_state,after_state,idempotency_key) values(:id,:tenant_id,:actor_id,:action,:resource_type,:resource_id,cast(:before as jsonb),cast(:after as jsonb),:key)"), {"id":f"pae_{uuid4().hex[:26]}","tenant_id":tenant_id,"actor_id":actor_id,"action":action,"resource_type":resource_type,"resource_id":resource_id,"before":json.dumps(before,default=str) if before is not None else None,"after":json.dumps(after,default=str),"key":key})

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
                insert into production.recipe_stages (id, tenant_id, recipe_version_id, labor_area_ref_id, labor_area_name, weight_percent, name, description, expected_minutes, sort_order, status)
                values (:id, :tenant_id, :version_id, :labor_area_ref_id, :labor_area_name, :weight_percent, :name, :description, :expected_minutes, :sort_order, :status)
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
        stages = connection.execute(text("select id, labor_area_ref_id, labor_area_name, weight_percent, name, description, expected_minutes, sort_order, status from production.recipe_stages where tenant_id=:tenant_id and recipe_version_id=:id order by sort_order"), {"tenant_id": tenant_id, "id": version_id}).mappings().all()
        return RecipeVersionRead(**dict(row), resources=[dict(item) for item in resources], stages=[dict(item) for item in stages])


_repository: ProductionRepository | None = None


def get_production_repository() -> ProductionRepository:
    global _repository
    if _repository is None:
        _repository = ProductionRepository(create_database_engine())
    return _repository
