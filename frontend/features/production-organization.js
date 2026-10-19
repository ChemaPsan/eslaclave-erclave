import { mountMachineRate } from "./machine-rate.js";
import { findAssignmentDivisions, findAssignmentCenters, getMachineDivision, getProductServiceDivisions, saveProductionAssignment, saveProductEstimatedCost } from "../api/production-organization.js";
import { productionOrganizationCopy } from "../i18n/production-organization.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
export async function mountProductionOrganization(root, kind, record, session, lang = "es", close = () => {}) {
 const c = productionOrganizationCopy[lang === "en" ? "en" : "es"], permissions = session.permissions || [], editable = permissions.includes(`production.${kind}.update`);
 const centersAllowed = kind === "product_service" && permissions.includes("costing.cost_center.read") && session.capabilities?.cost_center_catalog?.available;
 const label = id => { const row = session.scope?.divisions?.find(row => row.id === id); return row ? `${row.code} · ${row.name}` : id; };
 root.innerHTML = `<section class="production-organization-panel"><h2>${c.title}: ${escape(record.code)} · ${escape(record.title || record.name)}</h2><p>${c.hint}</p>${kind === "machine" ? `<p>${c.locked}</p>` : ""}<div data-assign-lookup></div><form data-form="production-organization" class="production-organization-form"><p data-assign-division>${c.unassigned}</p><input type="hidden" name="division_ref_id"><div data-assign-center-area></div>${kind === "product_service" ? `<label><span>${c.status}</span><select name="status"><option value="active">${c.active}</option><option value="inactive">${c.inactive}</option></select></label>` : ""}<div data-assign-center-lookup></div>${editable ? `<button class="primary-action" type="submit">${c.save}</button>` : ""}</form><div data-product-estimated-cost></div><p data-assign-message role="status"></p><div data-assign-history></div><div data-machine-rate></div><button class="secondary-action" type="button" data-assign-close>${c.close}</button></section>`;
 const panel = root.querySelector(".production-organization-panel"), form = panel.querySelector("form"), message = panel.querySelector("[data-assign-message]"), lookup = panel.querySelector("[data-assign-lookup]"), history = panel.querySelector("[data-assign-history]");
 let busy = false, current = null, center = null, key, fingerprint, costKey, costFingerprint, offset = 0, version = 0;
 const controls = () => { panel.querySelectorAll("button,input,select").forEach(node => { if (node.closest("[data-machine-rate]")) return; node.disabled = busy || node.hasAttribute("data-unavailable"); }); if (!editable) form.querySelectorAll("input,select").forEach(node => { node.disabled = true; }); };
 const error = value => { message.textContent = getLocalizedErrorMessage(value, { lang }); message.setAttribute("role", "alert"); };
 function centerDisplay() { panel.querySelector("[data-assign-center-area]").innerHTML = kind === "product_service" ? `<p>${c.center}: <strong>${escape(center ? `${center.code || center.id} ${center.name || ""}` : c.clear)}</strong></p><p>${c.centerHint}</p>${!centersAllowed ? `<p>${c.noCenterAccess}</p>` : ""}` : ""; }
 function renderEstimatedCost() {
  if (kind !== "product_service") return;
  const target = panel.querySelector("[data-product-estimated-cost]");
  if (!current?.division_ref_id) { target.replaceChildren(); return; }
  const division = session.scope?.divisions?.find(row => row.id === current.division_ref_id);
  const currency = session.scope?.societies?.find(row => row.id === division?.society_id)?.base_currency || null;
  const display = current.estimated_unit_cost == null ? c.estimatedCostMissing : `${current.estimated_unit_cost} ${current.cost_currency || currency || ""}`;
  const unavailable = !current.revision ? c.estimatedCostFirst : current.status !== "active" ? c.estimatedCostInactive : !currency ? c.estimatedCostCurrencyMissing : "";
  target.innerHTML = `<section class="production-estimated-cost"><h3>${c.estimatedCostTitle}</h3><p>${c.estimatedCostHint}</p><p><strong>${escape(display)}</strong></p>${unavailable ? `<p>${escape(unavailable)}</p>` : editable ? `<form data-form="production-estimated-cost"><label><span>${c.estimatedCostValue} (${escape(currency)})</span><input name="estimated_unit_cost" inputmode="decimal" type="number" min="0" step="0.000001" data-error-path="estimated_unit_cost" value="${escape(current.estimated_unit_cost ?? "")}"></label><div class="production-assignment-actions"><button class="primary-action" type="submit">${c.estimatedCostConfirm}</button>${current.estimated_unit_cost != null ? `<button class="secondary-action" type="button" data-clear-estimated-cost>${c.estimatedCostClear}</button>` : ""}</div></form>` : ""}</section>`;
  const costForm = target.querySelector("form");
  async function submitCost(clear) {
   if (busy || !editable) return;
   const value = costForm.elements.estimated_unit_cost.value.trim();
   if (!clear && !/^\d{1,12}(?:\.\d{1,6})?$/.test(value)) { renderFormFeedback(costForm, [{ field: "estimated_unit_cost", message: c.estimatedCostInvalid }], { lang }); return; }
   const payload = { expected_revision: current.revision, estimated_unit_cost: clear ? null : value, cost_currency: clear ? null : currency };
   const serialized = JSON.stringify(payload);
   if (costFingerprint !== serialized) { costFingerprint = serialized; costKey = `estimate-${crypto.randomUUID()}`; }
   busy = true; controls();
   try { const saved = await saveProductEstimatedCost(record.id, current.division_ref_id, payload, costKey); if (!panel.isConnected) return; await select(saved); message.setAttribute("role", "status"); message.textContent = clear ? c.estimatedCostCleared : c.estimatedCostSaved; await loadHistory(); }
   catch (value) { if (costForm.isConnected) renderFormFeedback(costForm, [value], { lang }); }
   finally { busy = false; if (panel.isConnected) controls(); }
  }
  if (costForm) { costForm.onsubmit = event => { event.preventDefault(); submitCost(false); }; costForm.querySelector("[data-clear-estimated-cost]")?.addEventListener("click", () => submitCost(true)); }
 }
 async function searchBox(container, type) {
  container.innerHTML = `<div data-assignment-search="${type}"><label><span>${type === "division" ? c.division : c.center}</span><input type="search" name="q" maxlength="240" data-error-path="${type === "division" ? "division_ref_id" : "cost_center_ref_id"}"></label><button type="button" data-search class="secondary-action">${c.find}</button></div><div data-results></div><div class="production-assignment-actions"><button type="button" class="secondary-action" data-prev>${c.previous}</button><button type="button" class="secondary-action" data-next>${c.next}</button>${type === "center" ? `<button type="button" class="secondary-action" data-clear>${c.clear}</button>` : ""}</div>`;
  let page = 0, query = "", total = 0, rows = [];
  const results = container.querySelector("[data-results]");
  async function load() {
   const ticket = version; busy = true; controls();
   try { const result = await (type === "division" ? findAssignmentDivisions(query, page) : findAssignmentCenters(current.division_ref_id, query, page)); if (!container.isConnected || ticket !== version) return;
    rows = result.data; total = result.meta.total; results.innerHTML = rows.map((row, index) => `<button type="button" class="secondary-action" data-pick="${index}">${escape(row.code)} · ${escape(row.name)}</button>`).join("") || `<p>${c.empty}</p>`;
   } catch (value) { if (container.isConnected) error(value); }
   finally { busy = false; if (panel.isConnected) { controls(); container.querySelector("[data-prev]").toggleAttribute("data-unavailable", page === 0); container.querySelector("[data-next]").toggleAttribute("data-unavailable", page + 20 >= total); controls(); } }
  }
  container.querySelector("[data-search]").onclick = () => { if (busy) return; query = container.querySelector("[name=q]").value.trim(); page = 0; load(); };
  container.querySelector("[name=q]").onkeydown = event => { if (event.key === "Enter") { event.preventDefault(); container.querySelector("[data-search]").click(); } };
  container.querySelector("[data-prev]").onclick = () => { page = Math.max(0, page - 20); load(); };
  container.querySelector("[data-next]").onclick = () => { page += 20; load(); };
  container.querySelector("[data-clear]")?.addEventListener("click", () => { center = null; centerDisplay(); });
  results.onclick = async event => { const button = event.target.closest("[data-pick]"); if (!button || busy) return; const row = rows[Number(button.dataset.pick)]; if (type === "center") { center = row; centerDisplay(); return; }
   busy = true; controls(); try { const assigned = kind === "product_service" ? (await getProductServiceDivisions(record.id, 0, row.id)).data[0] : current; if (panel.isConnected) await select({ ...(assigned || { revision: 0, status: "active" }), division_ref_id: row.id }); } catch (value) { error(value); } finally { busy = false; if (panel.isConnected) controls(); }
  };
  await load();
 }
 async function select(value) {
  version++; current = value; key = null; fingerprint = null; costKey = null; costFingerprint = null; center = value.cost_center_snapshot || (value.cost_center_ref_id ? { id: value.cost_center_ref_id } : null);
  form.elements.division_ref_id.value = value.division_ref_id || ""; panel.querySelector("[data-assign-division]").textContent = value.division_ref_id ? `${c.division}: ${label(value.division_ref_id)}` : c.unassigned;
  if (kind === "product_service") { form.elements.status.value = value.status || "active"; form.elements.status.querySelector('option[value="inactive"]').disabled = value.revision === 0; }
  else if (form.querySelector("[type=submit]")) form.querySelector("[type=submit]").hidden = value.revision > 0 || !session.scope?.all_divisions;
  centerDisplay(); renderEstimatedCost(); const target = panel.querySelector("[data-assign-center-lookup]"); target.replaceChildren();
  if (editable && centersAllowed && value.division_ref_id && value.status !== "inactive") await searchBox(target, "center");
 }
 async function loadHistory() {
  const result = await getProductServiceDivisions(record.id, offset); if (!panel.isConnected) return;
  history.innerHTML = `<h3>${c.history}</h3>${result.data.map((row, index) => `<article><p>${escape(label(row.division_ref_id))} · ${c[row.status]}</p><button type="button" class="secondary-action" data-edit="${index}">${c.edit}</button></article>`).join("") || `<p>${c.empty}</p>`}<div class="production-assignment-actions"><button type="button" class="secondary-action" data-history-prev ${offset === 0 ? "disabled data-unavailable" : ""}>${c.previous}</button><button type="button" class="secondary-action" data-history-next ${offset + 25 >= result.meta.total ? "disabled data-unavailable" : ""}>${c.next}</button></div>`;
  history.querySelectorAll("[data-edit]").forEach(button => { button.onclick = () => select(result.data[Number(button.dataset.edit)]); });
  history.querySelector("[data-history-prev]").onclick = () => { offset = Math.max(0, offset - 25); loadHistory().catch(error); };
  history.querySelector("[data-history-next]").onclick = () => { offset += 25; loadHistory().catch(error); };
 }
 form.onsubmit = async event => {
  event.preventDefault(); if (!editable || busy) return;
  if (!current?.division_ref_id) { renderFormFeedback(form, [c.select], { lang }); return; }
  const payload = { expected_revision: current.revision, ...(kind === "machine" ? { division_ref_id: current.division_ref_id } : { status: form.elements.status.value, cost_center_ref_id: center?.id || null }) };
  const serialized = JSON.stringify(payload); if (fingerprint !== serialized) { fingerprint = serialized; key = `assign-${crypto.randomUUID()}`; }
  busy = true; controls();
  try { const saved = await saveProductionAssignment(kind, record.id, current.division_ref_id, payload, key); if (!panel.isConnected) return; await select(saved); message.setAttribute("role", "status"); message.textContent = c.saved; if (kind === "machine") { lookup.replaceChildren(); await mountMachineRate(panel.querySelector("[data-machine-rate]"), record.id, session, lang); } else await loadHistory().catch(error); }
  catch (value) { if (form.isConnected) { busy = false; controls(); renderFormFeedback(form, [value], { lang }); } }
  finally { busy = false; if (panel.isConnected) controls(); }
 };
 if (kind === "product_service") form.elements.status.onchange = async () => {
  const target = panel.querySelector("[data-assign-center-lookup]"); target.replaceChildren();
  if (form.elements.status.value === "inactive") { center = current?.cost_center_snapshot || (current?.cost_center_ref_id ? { id: current.cost_center_ref_id } : null); centerDisplay(); }
  if (editable && centersAllowed && current?.division_ref_id && form.elements.status.value === "active") await searchBox(target, "center");
 };
 panel.querySelector("[data-assign-close]").onclick = close;
 try {
  if (kind === "machine") { const value = await getMachineDivision(record.id); if (!panel.isConnected) return; await select(value); if (value.division_ref_id) await mountMachineRate(panel.querySelector("[data-machine-rate]"), record.id, session, lang); if (editable && !value.division_ref_id && session.scope?.all_divisions) await searchBox(lookup, "division"); }
  else { await loadHistory(); if (editable) await searchBox(lookup, "division"); }
 } catch (value) { if (panel.isConnected) error(value); }
 controls();
}
