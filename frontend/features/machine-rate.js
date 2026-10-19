import { getMachineRate, saveMachineRate, getDivisionMachineCapacity } from "../api/production-organization.js";
import { societyRateContext } from "./resource-rate-context.js";
import { resourceRateCopy } from "../i18n/resource-rates.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
export async function mountMachineRate(root, id, session, lang = "es") {
 root.classList.add("production-organization-panel");
 const c = resourceRateCopy[lang === "en" ? "en" : "es"], editable = session.permissions?.includes("production.machine.update");
 let row;
 try { row = await getMachineRate(id); }
 catch (error) { if (root.isConnected) root.textContent = getLocalizedErrorMessage(error, { lang }); return; }
 if (!root.isConnected) return;
 const context = societyRateContext(session, row.division_ref_id);
 root.innerHTML = `<form data-form="machine-rate" class="production-organization-form"><label><span>${c.rate}</span><input name="cost_per_minute" type="number" min="0" max="999999999999.999999" step="0.000001" required value="${escape(row.cost_per_minute)}"></label><label><span>${c.currency}</span><input name="cost_currency" readonly value="${escape(context?.currency || "")}"></label><p data-rate-history>${escape(row.cost_currency || c.pending)}</p><p>${c.history}</p><label><input type="checkbox" name="confirm_rate" required><span>${c.confirm}</span></label>${editable ? `<button type="submit" class="primary-action">${c.save}</button>` : ""}<p data-rate-message role="status">${context ? "" : c.missing}</p></form><form data-form="machine-capacity" class="production-organization-form"><label><span>${c.date}</span><input name="planned_date" type="date" required></label><button type="submit" class="secondary-action">${c.capacity}</button><p>${c.machineCapacityHint}</p><div data-machine-capacity-result role="status"></div></form>`;
 const form = root.querySelector("form"), message = root.querySelector("[data-rate-message]");
 let pending = false, key, fingerprint;
 function controls() { form.querySelectorAll("input,button").forEach(node => { node.disabled = pending || !editable || !context; }); }
 form.elements.cost_per_minute.addEventListener("input", () => { form.elements.confirm_rate.checked = false; });
 form.onsubmit = async event => {
  event.preventDefault(); if (pending || !editable || !context || !form.reportValidity()) return;
  const payload = { cost_per_minute: form.elements.cost_per_minute.value, cost_currency: context.currency };
  const serialized = JSON.stringify(payload); if (serialized !== fingerprint) { fingerprint = serialized; key = `machine-rate-${crypto.randomUUID()}`; }
  pending = true; controls();
  try {
   row = await saveMachineRate(id, payload, key); if (!form.isConnected) return;
   renderFormFeedback(form, [], { lang }); form.elements.cost_per_minute.value = row.cost_per_minute;
   form.elements.confirm_rate.checked = false; form.querySelector("[data-rate-history]").textContent = row.cost_currency || c.pending;
   message.textContent = c.saved; key = null; fingerprint = null;
  } catch (error) { if (form.isConnected) { pending = false; controls(); renderFormFeedback(form, [error], { lang }); } }
  finally { pending = false; if (form.isConnected) controls(); }
 };
 const capacityForm = root.querySelector('[data-form="machine-capacity"]');
 capacityForm.onsubmit = async event => {
  event.preventDefault(); if (!row.division_ref_id || !context || !capacityForm.reportValidity() || capacityForm.dataset.busy) return;
  capacityForm.dataset.busy = "true"; const button = capacityForm.querySelector("button"), target = capacityForm.querySelector("[data-machine-capacity-result]"); button.disabled = true;
  const date = capacityForm.elements.planned_date.value;
  try {
   const result = await getDivisionMachineCapacity(row.division_ref_id, date);
   if (!capacityForm.isConnected || capacityForm.elements.planned_date.value !== date) return;
   renderFormFeedback(capacityForm, [], { lang });
   target.innerHTML = result.data.map(machine => `<article><strong>${escape(machine.code)} · ${escape(machine.name)}</strong><p>${escape(machine.available_minutes)} ${c.available} · ${escape(machine.cost_per_minute)} ${escape(machine.cost_currency)}</p></article>`).join("") || c.machineEmpty;
  } catch (error) { if (capacityForm.isConnected) { target.replaceChildren(); renderFormFeedback(capacityForm, [error], { lang }); } }
  finally { delete capacityForm.dataset.busy; button.disabled = false; }
 };
 capacityForm.querySelectorAll("input,button").forEach(node => { node.disabled = !row.division_ref_id || !context; });
 capacityForm.elements.planned_date.onchange = () => capacityForm.querySelector("[data-machine-capacity-result]").replaceChildren();
 controls();
}
