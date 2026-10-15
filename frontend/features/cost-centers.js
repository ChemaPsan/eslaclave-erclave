import { listCostCenters, saveCostCenter } from "../api/cost-centers.js";
import { costCenterCopy } from "../i18n/cost-centers.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
export function mountCostCenters(root, division, permissions, lang = "es", close = () => {}) {
 const c = costCenterCopy[lang === "en" ? "en" : "es"], can = action => permissions.includes(`costing.cost_center.${action}`);
 root.innerHTML = `<section class="cost-center-panel"><h4>${c.title}: ${escape(division.code)} · ${escape(division.name)}</h4><p>${c.hint}</p>
 <form data-cc-search class="org-toolbar"><label><span>${c.search}</span><input name="q" maxlength="240" type="search"></label><label><span>${c.status}</span><select name="status"><option value="">${c.all}</option><option value="active">${c.active}</option><option value="inactive">${c.inactive}</option></select></label><button class="secondary-action" type="submit">${c.find}</button></form>
 <div data-cc-editor></div><p role="status" data-cc-message></p><div data-cc-list></div><div class="org-actions"><button type="button" class="secondary-action" data-cc-prev>${c.previous}</button><span data-cc-count></span><button type="button" class="secondary-action" data-cc-next>${c.next}</button><button type="button" class="secondary-action" data-cc-close>${c.close}</button></div></section>`;
 const panel = root.querySelector(".cost-center-panel"), list = panel.querySelector("[data-cc-list]"), editor = panel.querySelector("[data-cc-editor]"), message = panel.querySelector("[data-cc-message]");
 let busy = false, items = [], offset = 0, total = 0, q = "", status = "", editing = null;
 const statusKeys = new Map();
 const showError = error => { message.textContent = getLocalizedErrorMessage(error, { lang }); message.setAttribute("role", "alert"); };
 function controls() {
   panel.querySelectorAll("button,input,select").forEach(node => { node.disabled = busy; });
   panel.querySelector("[data-cc-prev]").disabled = busy || offset === 0;
   panel.querySelector("[data-cc-next]").disabled = busy || offset + 25 >= total;
 }
 function renderEditor(item = null) {
   editing = item;
   if (!item && (!can("create") || division.status === "inactive")) { editor.replaceChildren(); return; }
   editor.innerHTML = `<form class="admin-form org-form cost-center-form" data-form="cost-center"><label><span>${c.name} *</span><input name="name" data-error-path="name" maxlength="240" required value="${escape(item?.name)}"></label><button type="submit" class="primary-action">${item ? c.save : c.create}</button>${item ? `<button type="button" class="secondary-action" data-cc-cancel>${c.cancel}</button>` : ""}</form>`;
   const form = editor.querySelector("form"); let key, fingerprint;
   form.querySelector("[data-cc-cancel]")?.addEventListener("click", () => renderEditor());
   form.addEventListener("submit", async event => {
     event.preventDefault(); if (busy) return;
     const payload = { name: form.elements.name.value.trim(), ...(item ? { expected_revision: item.revision } : { division_ref_id: division.id }) };
     const serialized = JSON.stringify(payload); if (serialized !== fingerprint) { fingerprint = serialized; key = `cc-${crypto.randomUUID()}`; }
     busy = true; controls();
     try {
       await saveCostCenter({ id: item?.id, payload, key });
       if (!panel.isConnected) return;
       renderEditor(); await load(c.saved);
     } catch (error) { if (form.isConnected) { busy = false; controls(); renderFormFeedback(form, [error], { lang }); } }
     finally { busy = false; if (panel.isConnected) controls(); }
   });
 }
 async function load(success = "") {
   busy = true; controls(); message.setAttribute("role", "status"); message.textContent = c.loading;
   try {
     const result = await listCostCenters(division.id, { q, status, offset }); if (!panel.isConnected) return;
     items = result.data; total = result.meta.total;
     list.innerHTML = items.map(item => `<article class="org-card" data-cc-id="${escape(item.id)}"><div><small>${escape(item.code)}</small><p><strong>${escape(item.name)}</strong></p><span class="chip">${c[item.status]}</span></div><div class="org-actions">${can("update") ? `<button type="button" class="secondary-action" data-cc-action="edit">${c.edit}</button>` : ""}${can("status") && (item.status === "active" || division.status !== "inactive") ? `<button type="button" class="secondary-action" data-cc-action="${item.status === "active" ? "deactivate" : "activate"}">${item.status === "active" ? c.deactivate : c.activate}</button>` : ""}</div></article>`).join("") || `<p>${c.empty}</p>`;
     panel.querySelector("[data-cc-count]").textContent = c.count.replace("{total}", total); message.textContent = success;
   } catch (error) { if (panel.isConnected) showError(error); }
   finally { busy = false; if (panel.isConnected) controls(); }
 }
 panel.querySelector("[data-cc-search]").onsubmit = event => { event.preventDefault(); if (busy) return; q = event.currentTarget.elements.q.value.trim(); status = event.currentTarget.elements.status.value; offset = 0; load(); };
 panel.querySelector("[data-cc-prev]").onclick = () => { offset -= 25; load(); };
 panel.querySelector("[data-cc-next]").onclick = () => { offset += 25; load(); };
 panel.querySelector("[data-cc-close]").onclick = close;
 list.addEventListener("click", async event => {
   const button = event.target.closest("[data-cc-action]"); if (!button || busy) return;
   const item = items.find(row => row.id === button.closest("[data-cc-id]").dataset.ccId), action = button.dataset.ccAction;
   if (action === "edit") { renderEditor(item); controls(); return; }
   const fingerprint = `${item.id}:${item.revision}:${action}`;
   if (!statusKeys.has(fingerprint)) statusKeys.set(fingerprint, `cc-${crypto.randomUUID()}`);
   busy = true; controls();
   try { await saveCostCenter({ id: item.id, action, payload: { expected_revision: item.revision }, key: statusKeys.get(fingerprint) }); if (panel.isConnected) { statusKeys.delete(fingerprint); if (editing?.id === item.id) renderEditor(); await load(c.saved); } }
   catch (error) { if (panel.isConnected) showError(error); }
   finally { busy = false; if (panel.isConnected) controls(); }
 });
 renderEditor(); load();
}
