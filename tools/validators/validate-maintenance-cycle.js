const { fail, ok, readText } = require("./shared");

const frontend = readText("frontend/app.js");
const errors = [];

for (const token of [
  "maintenanceMaterialSourceOrderId",
  "data-request-maintenance-material",
  "data-open-spare-parts-warehouse",
  'initialFields = {}',
  'type:"spare_parts"',
  "maintenance-material-request",
  "line.item_name",
  'item.id===order.assigned_worker_id?"selected"',
  "openMaintenanceActionModal",
  "openMaintenanceTimeModal",
  "maintenanceTimeFields",
  "data-log-maintenance-time",
  'name="time_started_at"',
  'name="time_ended_at"',
  'id="maintenanceActionForm"',
  'name="diagnosis"',
  'name="work_performed"',
  'name="verification_notes"',
  'Technician assigned: ${result.assigned_worker_name}',
  'Tecnico asignado: ${result.assigned_worker_name}'
]) {
  if (!frontend.includes(token)) errors.push(`Maintenance UI continuity missing ${token}`);
}

if (/action==="resolve"[^}]*prompt\(/s.test(frontend) || /action==="cancel"[^}]*prompt\(/s.test(frontend)) {
  errors.push("Maintenance transitions must use ERClave forms instead of browser prompts.");
}

if (errors.length) fail("maintenance cycle validation failed", errors);
else ok("Maintenance assignment and spare-parts request continuity are visible and wired.");
