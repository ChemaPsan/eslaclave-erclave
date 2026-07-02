from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from erclave_common.db import create_database_engine

from .schemas import ProductServiceRead


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
    ) -> ProductServiceRead | None:
        product_service_id = f"prs_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
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
                return None
            product_service = self._get_product_service(connection, tenant_id, row["id"])

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
    ) -> ProductServiceRead | None:
        with self.engine.begin() as connection:
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
                return None
            product_service = self._get_product_service(connection, tenant_id, product_service_id)

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


_repository: ProductionRepository | None = None


def get_production_repository() -> ProductionRepository:
    global _repository
    if _repository is None:
        _repository = ProductionRepository(create_database_engine())
    return _repository
