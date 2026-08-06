import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from erclave_common.db import create_database_engine
from erclave_common.errors import ErclaveError

from .schemas import (
    MachineRead, OrderStageUpdateRequest, ProductionOrderRead, ProductionOrderStageRead,
    RecipeRead, RecipeVersionRead, ProductServiceRead, ResourceValidationRead,
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
                    select id, code, name, type, category, base_unit, status, target_price, standard_cost, responsible_area, cost_center, expected_margin, description
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
                        id, tenant_id, code, name, type, category, base_unit, status, target_price, responsible_area, cost_center, expected_margin, description
                    )
                    values (
                        :id, :tenant_id, lower(:code), :name, :type, :category, :base_unit, 'active', :target_price, :responsible_area, :cost_center, :expected_margin, :description
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
                    "cost_center": cost_center,
                    "expected_margin": expected_margin,
                    "description": description,
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
                        cost_center = coalesce(:cost_center, cost_center),
                        expected_margin = coalesce(:expected_margin, expected_margin),
                        description = coalesce(:description, description),
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
                select id, code, name, type, category, base_unit, status, target_price, standard_cost, responsible_area, cost_center, expected_margin, description
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
            rows = connection.execute(text(f"select id,code,name,machine_type,area_name,available_minutes_per_day,cost_per_minute,status from production.machines where {' and '.join(filters)} order by code"), params).mappings().all()
        return [MachineRead.model_validate(dict(row)) for row in rows]

    def create_machine(self, tenant_id: str, payload, key: str, request_hash: str, actor_id: str) -> MachineRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "machine.create", key, request_hash, actor_id)
            if replay is not None:
                return MachineRead.model_validate(replay)
            machine_id = f"maq_{uuid4().hex[:26]}"
            row = connection.execute(text("""
                insert into production.machines(id,tenant_id,code,name,machine_type,area_name,available_minutes_per_day,cost_per_minute)
                values(:id,:tenant_id,lower(:code),:name,:machine_type,:area_name,:available_minutes_per_day,:cost_per_minute)
                on conflict(tenant_id,code) do nothing
                returning id,code,name,machine_type,area_name,available_minutes_per_day,cost_per_minute,status
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
            before = connection.execute(text("select id,code,name,machine_type,area_name,available_minutes_per_day,cost_per_minute,status from production.machines where tenant_id=:tenant_id and id=:id for update"), {"tenant_id": tenant_id, "id": machine_id}).mappings().first()
            if before is None:
                self._release_idempotency(connection, tenant_id, "machine.update", key)
                return None
            data = payload.model_dump(exclude_none=True)
            if data:
                sets = ",".join(f"{name}=:{name}" for name in data)
                connection.execute(text(f"update production.machines set {sets},updated_at=now() where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": machine_id, **data})
            after = connection.execute(text("select id,code,name,machine_type,area_name,available_minutes_per_day,cost_per_minute,status from production.machines where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": machine_id}).mappings().one()
            value = MachineRead.model_validate(dict(after))
            self._audit(connection, tenant_id, actor_id, "machine.update", "machine", machine_id, dict(before), value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, "machine.update", key, value.model_dump(mode="json"), 200)
            return value

    def validate_resources(self, tenant_id: str, payload, key: str, request_hash: str, actor_id: str) -> ResourceValidationRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "resource.validate", key, request_hash, actor_id)
            if replay is not None:
                return ResourceValidationRead.model_validate(replay)
            value = self._validate_resources(connection, tenant_id, payload)
            if value is None:
                self._release_idempotency(connection, tenant_id, "resource.validate", key)
                return None
            self._complete_idempotency(connection, tenant_id, "resource.validate", key, value.model_dump(mode="json"), 200)
            return value

    def _validate_resources(self, connection, tenant_id: str, payload) -> ResourceValidationRead | None:
        from datetime import datetime, timezone
        version = self._read_version(connection, tenant_id, payload.recipe_version_id)
        if version is None or version.status != "approved" or version.base_unit != payload.unit:
            return None
        scale = payload.quantity / version.base_quantity
        observations = {(item.resource_type, item.resource_ref_id, item.unit): item for item in payload.observed_resources}
        rows, blockers = [], []
        for resource in version.resources:
            required = resource.quantity * scale
            observation = observations.get((resource.resource_type, resource.resource_ref_id or "", resource.unit))
            available = observation.available_quantity if observation else 0
            source = observation.source if observation else "unavailable"
            if resource.resource_type == "machine" and resource.resource_ref_id:
                machine = connection.execute(text("select available_minutes_per_day,cost_per_minute,status from production.machines where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": resource.resource_ref_id}).mappings().first()
                if machine:
                    available = float(machine["available_minutes_per_day"]) if machine["status"] == "active" else 0
                    source = "production.machines"
                    unit_cost = float(machine["cost_per_minute"])
                else:
                    unit_cost = resource.unit_cost
            else:
                unit_cost = observation.unit_cost if observation and observation.unit_cost is not None else resource.unit_cost
            ok = available >= required
            blocker = None if ok else f"insufficient_{resource.resource_type}:{resource.resource_code}"
            if blocker:
                blockers.append(blocker)
            rows.append(ResourceValidationRow(resource_type=resource.resource_type,resource_ref_id=resource.resource_ref_id,resource_code=resource.resource_code,resource_name=resource.resource_name,unit=resource.unit,required_quantity=required,available_quantity=available,unit_cost=unit_cost,total_cost=required*unit_cost,source=source,ok=ok,blocker_code=blocker))
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

    def create_order(self, tenant_id: str, payload, key: str, request_hash: str, actor_id: str) -> ProductionOrderRead | None:
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "order.create", key, request_hash, actor_id)
            if replay is not None:
                return ProductionOrderRead.model_validate(replay)
            validation = self._validate_resources(connection, tenant_id, payload)
            if validation is None or not validation.can_release:
                self._release_idempotency(connection, tenant_id, "order.create", key)
                raise ValueError("resources_unavailable" if validation else "approved_recipe_required")
            version = self._read_version(connection, tenant_id, payload.recipe_version_id)
            recipe = self._read_recipe(connection, tenant_id, version.recipe_id)
            assignments = {item.recipe_stage_id: item.responsible_name for item in payload.stage_assignments}
            order_id, code = f"ord_{uuid4().hex[:26]}", f"OP-{uuid4().hex[:10].upper()}"
            recipe_snapshot = recipe.model_dump(mode="json")
            connection.execute(text("""
                insert into production.production_orders(id,tenant_id,code,product_service_id,recipe_id,recipe_version_id,quantity,unit,status,priority,required_at,responsible_name_snapshot,planned_start_at,source_type,source_id,source_line_id,planned_cost,recipe_snapshot,resource_validation_snapshot,validated_at,created_by)
                values(:id,:tenant_id,:code,:product_service_id,:recipe_id,:recipe_version_id,:quantity,:unit,'released',:priority,:required_at,:responsible,:planned_start_at,:source_type,:source_id,:source_line_id,:planned_cost,cast(:recipe_snapshot as jsonb),cast(:validation as jsonb),:validated_at,:actor_id)
            """), {"id":order_id,"tenant_id":tenant_id,"code":code,"product_service_id":recipe.product_service_id,"recipe_id":recipe.id,"recipe_version_id":version.id,"quantity":payload.quantity,"unit":payload.unit,"priority":payload.priority,"required_at":payload.required_at,"responsible":payload.responsible_name,"planned_start_at":payload.planned_start_at,"source_type":payload.source_type,"source_id":payload.source_id,"source_line_id":payload.source_line_id,"planned_cost":validation.planned_cost,"recipe_snapshot":json.dumps(recipe_snapshot),"validation":json.dumps(validation.model_dump(mode="json")),"validated_at":validation.validated_at,"actor_id":actor_id})
            for stage in version.stages:
                if stage.status != "active": continue
                connection.execute(text("""
                    insert into production.production_order_stages(id,tenant_id,production_order_id,recipe_stage_id,name,description_snapshot,sort_order,status,planned_minutes,responsible_name_snapshot)
                    values(:id,:tenant_id,:order_id,:recipe_stage_id,:name,:description,:sort_order,'pending',:planned_minutes,:responsible)
                """), {"id":f"ost_{uuid4().hex[:26]}","tenant_id":tenant_id,"order_id":order_id,"recipe_stage_id":stage.id,"name":stage.name,"description":stage.description,"sort_order":stage.sort_order,"planned_minutes":stage.expected_minutes,"responsible":assignments.get(stage.id)})
            value = self._read_order(connection, tenant_id, order_id)
            self._audit(connection, tenant_id, actor_id, "order.create", "production_order", order_id, None, value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, "order.create", key, value.model_dump(mode="json"), 201)
            return value

    def update_order_status(self, tenant_id: str, order_id: str, payload, key: str, request_hash: str, actor_id: str) -> ProductionOrderRead | None:
        allowed = {"released":{"waiting_resources","in_progress","cancelled"},"waiting_resources":{"released","cancelled"},"in_progress":{"paused","in_validation","cancelled"},"paused":{"in_progress","cancelled"},"in_validation":{"in_progress","completed"},"completed":set(),"cancelled":set()}
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "order.status", key, request_hash, actor_id)
            if replay is not None: return ProductionOrderRead.model_validate(replay)
            before = self._read_order(connection, tenant_id, order_id)
            if before is None:
                self._release_idempotency(connection, tenant_id, "order.status", key); return None
            if payload.status not in allowed[before.status]:
                self._release_idempotency(connection, tenant_id, "order.status", key); raise ValueError("invalid_order_transition")
            timestamps = ",actual_start_at=coalesce(actual_start_at,now())" if payload.status == "in_progress" else ",actual_end_at=now()" if payload.status in {"completed","cancelled"} else ""
            connection.execute(text(f"update production.production_orders set status=:status,actual_cost=coalesce(:actual_cost,actual_cost),updated_at=now(){timestamps} where tenant_id=:tenant_id and id=:id"), {"status":payload.status,"actual_cost":payload.actual_cost,"tenant_id":tenant_id,"id":order_id})
            value = self._read_order(connection, tenant_id, order_id)
            self._audit(connection, tenant_id, actor_id, "order.status", "production_order", order_id, before.model_dump(mode="json"), {**value.model_dump(mode="json"),"reason":payload.reason}, key)
            self._complete_idempotency(connection, tenant_id, "order.status", key, value.model_dump(mode="json"), 200)
            return value

    def update_order_stage(self, tenant_id: str, stage_id: str, payload: OrderStageUpdateRequest, key: str, request_hash: str, actor_id: str) -> ProductionOrderStageRead | None:
        allowed = {"pending":{"in_progress","blocked","skipped"},"in_progress":{"completed","blocked"},"blocked":{"pending","in_progress","skipped"},"completed":set(),"skipped":set()}
        with self.engine.begin() as connection:
            replay = self._claim_idempotency(connection, tenant_id, "order_stage.update", key, request_hash, actor_id)
            if replay is not None: return ProductionOrderStageRead.model_validate(replay)
            before = self._read_stage(connection, tenant_id, stage_id)
            if before is None:
                self._release_idempotency(connection, tenant_id, "order_stage.update", key); return None
            if payload.status not in allowed[before.status]:
                self._release_idempotency(connection, tenant_id, "order_stage.update", key); raise ValueError("invalid_stage_transition")
            progress = 100 if payload.status in {"completed","skipped"} else 50 if payload.status == "in_progress" else 0
            connection.execute(text("""
                update production.production_order_stages set status=:status,actual_minutes=coalesce(:actual_minutes,actual_minutes),notes=coalesce(:notes,notes),progress_percent=:progress,
                started_at=case when cast(:status as varchar)='in_progress' then coalesce(started_at,now()) else started_at end,
                completed_at=case when cast(:status as varchar) in ('completed','skipped') then now() else completed_at end,updated_at=now()
                where tenant_id=:tenant_id and id=:id
            """), {"status":payload.status,"actual_minutes":payload.actual_minutes,"notes":payload.notes,"progress":progress,"tenant_id":tenant_id,"id":stage_id})
            value = self._read_stage(connection, tenant_id, stage_id)
            order_id = connection.execute(text("select production_order_id from production.production_order_stages where tenant_id=:tenant_id and id=:id"), {"tenant_id":tenant_id,"id":stage_id}).scalar_one()
            statuses = set(connection.execute(text("select status from production.production_order_stages where tenant_id=:tenant_id and production_order_id=:id"), {"tenant_id":tenant_id,"id":order_id}).scalars())
            if payload.status == "in_progress": connection.execute(text("update production.production_orders set status='in_progress',actual_start_at=coalesce(actual_start_at,now()),updated_at=now() where tenant_id=:tenant_id and id=:id and status in ('released','paused')"), {"tenant_id":tenant_id,"id":order_id})
            if statuses and statuses <= {"completed","skipped"}: connection.execute(text("update production.production_orders set status='in_validation',updated_at=now() where tenant_id=:tenant_id and id=:id and status='in_progress'"), {"tenant_id":tenant_id,"id":order_id})
            self._audit(connection, tenant_id, actor_id, "order_stage.update", "production_order_stage", stage_id, before.model_dump(mode="json"), value.model_dump(mode="json"), key)
            self._complete_idempotency(connection, tenant_id, "order_stage.update", key, value.model_dump(mode="json"), 200)
            return value

    def _read_stage(self, connection, tenant_id: str, stage_id: str) -> ProductionOrderStageRead | None:
        row = connection.execute(text("select id,recipe_stage_id,name,sort_order,status,planned_minutes,actual_minutes,responsible_name_snapshot responsible_name,progress_percent,started_at,completed_at,notes from production.production_order_stages where tenant_id=:tenant_id and id=:id"), {"tenant_id":tenant_id,"id":stage_id}).mappings().first()
        return ProductionOrderStageRead.model_validate(dict(row)) if row else None

    def _read_order(self, connection, tenant_id: str, order_id: str) -> ProductionOrderRead | None:
        row = connection.execute(text("""
            select id,code,product_service_id,recipe_id,recipe_version_id,quantity,unit,status,priority,required_at,planned_start_at,actual_start_at,actual_end_at,responsible_name_snapshot responsible_name,source_type,source_id,planned_cost,actual_cost,recipe_snapshot,resource_validation_snapshot,created_at
            from production.production_orders where tenant_id=:tenant_id and id=:id
        """), {"tenant_id":tenant_id,"id":order_id}).mappings().first()
        if row is None: return None
        stage_ids = connection.execute(text("select id from production.production_order_stages where tenant_id=:tenant_id and production_order_id=:id order by sort_order"), {"tenant_id":tenant_id,"id":order_id}).scalars().all()
        return ProductionOrderRead(**dict(row), stages=[self._read_stage(connection, tenant_id, item) for item in stage_ids])

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
                insert into production.recipe_stages (id, tenant_id, recipe_version_id, labor_area_ref_id, labor_area_name, name, description, expected_minutes, sort_order, status)
                values (:id, :tenant_id, :version_id, :labor_area_ref_id, :labor_area_name, :name, :description, :expected_minutes, :sort_order, :status)
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
        stages = connection.execute(text("select id, labor_area_ref_id, labor_area_name, name, description, expected_minutes, sort_order, status from production.recipe_stages where tenant_id=:tenant_id and recipe_version_id=:id order by sort_order"), {"tenant_id": tenant_id, "id": version_id}).mappings().all()
        return RecipeVersionRead(**dict(row), resources=[dict(item) for item in resources], stages=[dict(item) for item in stages])


_repository: ProductionRepository | None = None


def get_production_repository() -> ProductionRepository:
    global _repository
    if _repository is None:
        _repository = ProductionRepository(create_database_engine())
    return _repository
