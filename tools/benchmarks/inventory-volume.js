"use strict";

const assert = require("node:assert/strict");
const { performance } = require("node:perf_hooks");

const ITEM_COUNT = 10_000;
const LIMIT = 50;
const MAX_DURATION_MS = 2_000;

function buildRows() {
  const rows = [];
  for (const tenantId of ["ten_local_a", "ten_local_b"]) {
    for (let index = 0; index < ITEM_COUNT; index += 1) {
      const itemNumber = String(index).padStart(5, "0");
      const onHand = index % 17 === 0 ? 0 : index % 29 === 0 ? -1 : (index % 250) + 1;
      rows.push({
        tenantId,
        itemId: `itm_${tenantId}_${itemNumber}`,
        itemCode: `MAT-${itemNumber}`,
        itemName: index % 101 === 0 ? `Resina especial ${itemNumber}` : `Articulo ${itemNumber}`,
        warehouseId: index % 2 === 0 ? "wh_norte" : "wh_sur",
        warehouseCode: index % 2 === 0 ? "NTE" : "SUR",
        warehouseName: index % 2 === 0 ? "Almacen Norte" : "Almacen Sur",
        unit: index % 3 === 0 ? "kg" : "pz",
        itemType: index % 2 === 0 ? "rawMaterial" : "consumable",
        category: index % 5 === 0 ? "Quimicos" : "General",
        inventoryPolicy: index % 7 === 0 ? "lot" : "standard",
        minimumStock: 10,
        maximumStock: 200,
        onHandQuantity: onHand,
        availableQuantity: onHand
      });
    }
  }
  return rows;
}

function stockStatus(quantity) {
  if (quantity > 0) return "available";
  if (quantity < 0) return "negative";
  return "zero";
}

function query(rows, tenantId, filters = {}) {
  const normalizedQuery = String(filters.q || "").trim().toLocaleLowerCase("es-MX");
  return rows
    .filter((row) => row.tenantId === tenantId)
    .filter((row) => !normalizedQuery || [row.itemCode, row.itemName, row.warehouseCode, row.warehouseName]
      .join(" ").toLocaleLowerCase("es-MX").includes(normalizedQuery))
    .filter((row) => !filters.warehouseId || row.warehouseId === filters.warehouseId)
    .filter((row) => !filters.unit || row.unit === filters.unit)
    .filter((row) => !filters.itemType || row.itemType === filters.itemType)
    .filter((row) => !filters.category || row.category === filters.category)
    .filter((row) => !filters.inventoryPolicy || row.inventoryPolicy === filters.inventoryPolicy)
    .filter((row) => !filters.stockStatus || stockStatus(row.onHandQuantity) === filters.stockStatus)
    .filter((row) => !filters.belowMinimum || row.onHandQuantity < row.minimumStock)
    .filter((row) => !filters.aboveMaximum || row.onHandQuantity > row.maximumStock)
    .sort((left, right) => left.itemCode.localeCompare(right.itemCode) || left.warehouseId.localeCompare(right.warehouseId));
}

function page(rows, cursor = 0, limit = LIMIT) {
  const data = rows.slice(cursor, cursor + limit);
  const nextCursor = cursor + data.length;
  return { data, nextCursor: nextCursor < rows.length ? nextCursor : null };
}

const startedAt = performance.now();
const rows = buildRows();
assert.equal(rows.length, ITEM_COUNT * 2);
assert.ok(rows.every((row) => row.availableQuantity === row.onHandQuantity));

const partial = query(rows, "ten_local_a", { q: "especial 001" });
assert.ok(partial.length > 0);
assert.ok(partial.every((row) => row.tenantId === "ten_local_a" && row.itemName.toLowerCase().includes("especial 001")));

const filtered = query(rows, "ten_local_a", {
  warehouseId: "wh_norte",
  unit: "kg",
  itemType: "rawMaterial",
  category: "Quimicos",
  stockStatus: "available"
});
assert.ok(filtered.length > 0);
assert.ok(filtered.every((row) => row.tenantId === "ten_local_a" && row.warehouseId === "wh_norte"));

const all = query(rows, "ten_local_a");
const visited = [];
let cursor = 0;
do {
  const result = page(all, cursor);
  assert.ok(result.data.length <= LIMIT);
  visited.push(...result.data.map((row) => row.itemId));
  cursor = result.nextCursor;
} while (cursor !== null);
assert.equal(visited.length, ITEM_COUNT);
assert.equal(new Set(visited).size, ITEM_COUNT);
assert.ok(visited.every((id) => id.includes("ten_local_a")));

const durationMs = performance.now() - startedAt;
assert.ok(durationMs < MAX_DURATION_MS, `Benchmark exceeded ${MAX_DURATION_MS} ms: ${durationMs.toFixed(1)} ms`);
process.stdout.write(`PASS inventory-volume items=${ITEM_COUNT} rows=${rows.length} duration_ms=${durationMs.toFixed(1)}\n`);
