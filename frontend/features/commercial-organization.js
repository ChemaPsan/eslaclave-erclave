import { mountCommercialTerms } from "./commercial-terms.js";
import { commercialTermsCopy } from "../i18n/commercial-terms.js";
import { findCommercialDivisions, getCommercialAssignments, saveCommercialAssignment } from "../api/commercial-organization.js";
import { commercialOrganizationCopy } from "../i18n/commercial-organization.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
export async function mountCommercialOrganization(root, kind, record, session, lang = "es", close = () => {}) {
 const module = { customer: "sales", supplier: "purchasing" }[kind];
 if (!module) return;
 const c = commercialOrganizationCopy[lang === "en" ? "en" : "es"], editable = session.permissions?.includes(`${module}.${kind}.update`);
 const label = (type, id) => { const row = session.scope?.[type]?.find(row => row.id === id); return row ? `${row.code} · ${row.name}` : id; };
 root.innerHTML = `<section class="commercial-organization-panel"><h2>${c.title}: ${escape(record.code)} · ${escape(record.commercial_name || record.title)}</h2><p>${c.hint}</p><p>${c.pending}</p><div data-assign-lookup></div><form data-form="commercial-organization"><p data-assign-division>${c.unassigned}</p><p data-assign-society></p><input type="hidden" name="division_ref_id"><label><span>${c.status}</span><select name="status"><option value="active">${c.active}</option><option value="inactive">${c.inactive}</option></select></label>${editable ? `<button class="primary-action" type="submit">${c.save}</button>` : ""}</form><p data-assign-message role="status"></p><div data-assign-history></div><button type="button" class="secondary-action" data-assign-terms data-unavailable>${commercialTermsCopy[lang === "en" ? "en" : "es"].title}</button><button class="secondary-action" type="button" data-assign-close>${c.close}</button></section>`;
 const panel = root.firstElementChild, form = panel.querySelector("form"), message = panel.querySelector("[data-assign-message]"), lookup = panel.querySelector("[data-assign-lookup]"), history = panel.querySelector("[data-assign-history]");
 let busy = false, current = null, key, fingerprint, offset = 0;
 const controls = () => { panel.querySelectorAll("button,input,select").forEach(node => { node.disabled = busy || node.hasAttribute("data-unavailable"); }); if (!editable) form.querySelectorAll("input,select").forEach(node => { node.disabled = true; }); };
 const error = value => { message.textContent = getLocalizedErrorMessage(value, { lang }); message.setAttribute("role", "alert"); };
 function select(value) {
  renderFormFeedback(form, [], { lang }); current = value; key = null; fingerprint = null; message.textContent = "";
  form.elements.division_ref_id.value = value.division_ref_id;
  panel.querySelector("[data-assign-terms]").toggleAttribute("data-unavailable", !value.revision);
  panel.querySelector("[data-assign-division]").textContent = `${c.division}: ${label("divisions", value.division_ref_id)}`;
  const society = value.society_ref_id || session.scope?.divisions?.find(row => row.id === value.division_ref_id)?.society_id;
  panel.querySelector("[data-assign-society]").textContent = `${c.society}: ${label("societies", society) || c.unassigned}`;
  form.elements.status.value = value.status; form.elements.status.querySelector('option[value="inactive"]').disabled = value.revision === 0; controls();
 }
 async function loadHistory() {
  const result = await getCommercialAssignments(kind, record.id, offset); if (!panel.isConnected) return;
  history.innerHTML = `<h3>${c.history}</h3>${result.data.map((row, index) => `<article><p>${escape(label("divisions", row.division_ref_id))} · ${c[row.status]}</p><button type="button" class="secondary-action" data-edit="${index}">${c.edit}</button></article>`).join("") || `<p>${c.empty}</p>`}<div class="commercial-assignment-actions"><button type="button" class="secondary-action" data-history-prev ${offset === 0 ? "data-unavailable" : ""}>${c.previous}</button><button type="button" class="secondary-action" data-history-next ${offset + 25 >= result.meta.total ? "data-unavailable" : ""}>${c.next}</button></div>`;
  history.querySelectorAll("[data-edit]").forEach(button => { button.onclick = () => { if (!busy) select(result.data[Number(button.dataset.edit)]); }; });
  const paginate = async delta => { if (busy) return; offset = Math.max(0, offset + delta); busy = true; controls(); try { await loadHistory(); } catch (value) { error(value); } finally { busy = false; controls(); } };
  history.querySelector("[data-history-prev]").onclick = () => paginate(-25); history.querySelector("[data-history-next]").onclick = () => paginate(25); controls();
 }
 async function searchBox() {
  lookup.innerHTML = `<label><span>${c.division}</span><input type="search" name="q" maxlength="240" data-error-path="division_ref_id"></label><button type="button" data-search class="secondary-action">${c.find}</button><div data-results></div><div class="commercial-assignment-actions"><button type="button" class="secondary-action" data-prev>${c.previous}</button><button type="button" class="secondary-action" data-next>${c.next}</button></div>`;
  let page = 0, query = "", rows = [];
  async function load() {
   busy = true; controls();
   try { const result = await findCommercialDivisions(kind, query, page); if (!panel.isConnected) return; rows = result.data;
    lookup.querySelector("[data-results]").innerHTML = rows.map((row, index) => `<button type="button" class="secondary-action" data-pick="${index}">${escape(row.code)} · ${escape(row.name)}</button>`).join("") || `<p>${c.empty}</p>`;
    lookup.querySelector("[data-prev]").toggleAttribute("data-unavailable", page === 0); lookup.querySelector("[data-next]").toggleAttribute("data-unavailable", page + 20 >= result.meta.total);
   } catch (value) { error(value); } finally { busy = false; controls(); }
  }
  lookup.querySelector("[data-search]").onclick = () => { if (busy) return; query = lookup.querySelector("[name=q]").value.trim(); page = 0; load(); };
  lookup.querySelector("[name=q]").onkeydown = event => { if (event.key === "Enter") { event.preventDefault(); lookup.querySelector("[data-search]").click(); } };
  lookup.querySelector("[data-prev]").onclick = () => { if (!busy) { page = Math.max(0, page - 20); load(); } }; lookup.querySelector("[data-next]").onclick = () => { if (!busy) { page += 20; load(); } };
  lookup.querySelector("[data-results]").onclick = async event => { const button = event.target.closest("[data-pick]"); if (!button || busy) return; const row = rows[Number(button.dataset.pick)]; busy = true; controls();
   try { const assigned = (await getCommercialAssignments(kind, record.id, 0, row.id)).data[0]; if (panel.isConnected) select(assigned || { revision: 0, status: "active", division_ref_id: row.id, society_ref_id: row.society_id }); } catch (value) { error(value); } finally { busy = false; controls(); }
  };
  await load();
 }
 form.onsubmit = async event => {
  event.preventDefault(); if (!editable || busy) return;
  if (!current) { renderFormFeedback(form, [c.select], { lang }); return; }
  const payload = { expected_revision: current.revision, status: form.elements.status.value }, serialized = JSON.stringify([current.division_ref_id, payload]);
  if (fingerprint !== serialized) { fingerprint = serialized; key = `assign-${crypto.randomUUID()}`; }
  busy = true; controls();
  try { const saved = await saveCommercialAssignment(kind, record.id, current.division_ref_id, payload, key); if (!panel.isConnected) return; select(saved); message.setAttribute("role", "status"); message.textContent = c.saved; await loadHistory().catch(error); }
  catch (value) { if (form.isConnected) { busy = false; controls(); renderFormFeedback(form, [value], { lang }); } }
  finally { busy = false; controls(); }
 };
 panel.querySelector("[data-assign-close]").onclick = close;
 panel.querySelector("[data-assign-terms]").onclick = () => { if (!busy && current?.revision) mountCommercialTerms(root, kind, record, current.division_ref_id, session, lang, () => mountCommercialOrganization(root, kind, record, session, lang, close)); };
 busy = true; controls(); try { await loadHistory(); if (editable && panel.isConnected) await searchBox(); } catch (value) { error(value); } finally { busy = false; controls(); }
}
