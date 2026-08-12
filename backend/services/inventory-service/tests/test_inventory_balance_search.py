from pathlib import Path
import importlib
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
repositories = importlib.import_module("app.repositories")


class EmptyResult:
    def mappings(self):
        return self

    def __iter__(self):
        return iter(())


class CaptureConnection:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement, params):
        self.calls.append((str(statement), params))
        return EmptyResult()


class CaptureEngine:
    def __init__(self):
        self.calls = []

    def connect(self):
        return CaptureConnection(self.calls)


@pytest.mark.parametrize("query", ["alg", "god", "don", "algodon", "algodón"])
def test_balance_search_normalizes_prefix_middle_suffix_and_accents(query):
    engine = CaptureEngine()
    repository = repositories.InventoryRepository(engine)

    data, page = repository.list_balances("ten_demo", q=query, limit=25)

    assert data == []
    assert page.limit == 25
    statement, params = engine.calls[0]
    assert "from inventory.movements where tenant_id=:t" in statement
    assert "from inventory.items where tenant_id=:t" in statement
    assert "c.tenant_id=:t" in statement
    assert "inventory.search_normalize(i.code||' '||i.name" in statement
    assert "inventory.search_normalize(w.code||' '||w.name)" in statement
    assert "like '%'||inventory.search_normalize(:q)||'%'" in statement
    assert params["q"] == query


def test_search_migration_has_trigram_indexes_and_reversible_normalizer():
    migration = (ROOT.parents[1] / "alembic" / "versions" / "20260727_0008_inventory_search_indexes.py").read_text(encoding="utf-8")

    assert "create extension if not exists pg_trgm" in migration
    assert "returns text language sql immutable parallel safe" in migration
    assert "'áéíóúüñ', 'aeiouun'" in migration
    assert "ix_inventory_items_search_trgm" in migration
    assert "ix_inventory_warehouses_search_trgm" in migration
    assert "drop function if exists inventory.search_normalize(text)" in migration
