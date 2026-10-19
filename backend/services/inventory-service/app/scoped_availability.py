"""Inventory owns stock eligibility and its exact original currency cost."""
from decimal import Decimal
from types import SimpleNamespace
from sqlalchemy import text
from .reservation_context import validate_local_context, validate_cost_currency
from .schemas import AvailabilityAllocation, AvailabilityCheckRead, AvailabilityItemRead


def check_scoped_availability(repository, tenant, payload, context):
    result = []
    with repository.engine.begin() as connection:
        for requested in payload.items:
            item = repository._item(connection, tenant, requested.inventory_item_id)
            assignment = connection.execute(text("select status from inventory.item_division_assignments where tenant_id=:t and item_id=:id and division_ref_id=:d"), {"t":tenant, "id":requested.inventory_item_id, "d":context.division_ref_id}).scalar()
            common = dict(inventory_item_id=requested.inventory_item_id, item_code=item.code if item else requested.inventory_item_id, item_name=item.name if item else requested.inventory_item_id, unit=requested.unit, required_quantity=requested.quantity, cost_currency=context.cost_currency)
            if not item or item.status != "active" or not item.use_in_recipe or item.base_unit != requested.unit or assignment != "active":
                result.append(AvailabilityItemRead(**common, on_hand_quantity=0, reserved_quantity=0, available_quantity=0, unit_cost=0, total_cost=0, ok=False, blocker_code="inventory_resource_invalid", allocations=[]))
                continue
            rows = repository._availability_rows(connection, tenant, item.id, requested.unit, context.division_ref_id)
            remaining = Decimal(str(requested.quantity))
            total = Decimal("0")
            allocations = []
            for row in rows:
                reference = SimpleNamespace(warehouse_id=row["warehouse_id"], inventory_item_id=item.id)
                validate_local_context(connection, tenant, reference, context)
                validate_cost_currency(connection, tenant, item.id, row["warehouse_id"], context)
                take = min(remaining, Decimal(str(row["available"])))
                if take > 0:
                    cost = Decimal(str(row["unit_cost"]))
                    allocations.append(AvailabilityAllocation(warehouse_id=row["warehouse_id"], warehouse_name=row["warehouse_name"], quantity=take, unit_cost=cost, original_unit_cost=cost, cost_currency=context.cost_currency))
                    total += take * cost
                    remaining -= take
            unit_cost = total / Decimal(str(requested.quantity))
            result.append(AvailabilityItemRead(**common, on_hand_quantity=sum(Decimal(str(row["on_hand"])) for row in rows), reserved_quantity=sum(Decimal(str(row["reserved"])) for row in rows), available_quantity=sum(Decimal(str(row["available"])) for row in rows), unit_cost=unit_cost, total_cost=total, original_unit_cost=unit_cost, original_total_cost=total, ok=remaining <= 0, blocker_code=None if remaining <= 0 else "insufficient_material", allocations=allocations))
    return AvailabilityCheckRead(source=payload.source, available=all(item.ok for item in result), items=result)
