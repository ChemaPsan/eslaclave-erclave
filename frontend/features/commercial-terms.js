import { getCommercialTerms, saveCommercialTerms, getCommercialTermReferences } from "../api/commercial-organization.js";
import { commercialTermsCopy } from "../i18n/commercial-terms.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
export async function mountCommercialTerms(root, kind, record, division, session, lang = "es", close = () => {}) {
 const module = { customer: "sales", supplier: "purchasing" }[kind]; if (!module) return;
 const c = commercialTermsCopy[lang === "en" ? "en" : "es"], editable = session.permissions?.includes(`${module}.${kind}.update`), extra = kind === "customer" ? "credit_limit" : "lead_time_days";
 const organization = session.scope?.divisions?.find(row => row.id === division), identity = organization ? `${organization.code} · ${organization.name}` : division;
 root.innerHTML = `<section class="commercial-organization-panel"><h2>${c.title}</h2><p>${escape(record.code)} · ${escape(record.commercial_name || record.title)}</p><p>${escape(identity)}</p><p>${c.hint}</p><p>${c.scopeHint}</p><p data-terms-state>${c.loading}</p><form data-form="commercial-terms"><label><span>${c.currency}</span><select name="values.currency" required></select></label><label><span>${c.payment}</span><select name="values.payment_terms" required></select></label><label><span>${kind === "customer" ? c.credit : c.lead}</span><input name="values.${extra}" type="number" min="0" ${kind === "customer" ? 'step="0.01" max="9999999999999999.99"' : 'step="1" max="3650"'} required>${kind === "customer" ? `<small>${c.creditHint}</small>` : ""}</label>${editable ? `<button type="submit" class="primary-action">${c.save}</button>` : ""}</form><p data-terms-message role="status"></p><div class="commercial-assignment-actions"><button class="secondary-action" type="button" data-terms-reload>${c.reload}</button><button class="secondary-action" type="button" data-terms-close>${c.close}</button></div></section>`;
 const panel = root.firstElementChild, form = panel.querySelector("form"), message = panel.querySelector("[data-terms-message]"), state = panel.querySelector("[data-terms-state]");
 let current = null, busy = false, referencesReady = false, key, fingerprint;
 const controls = () => { form.querySelectorAll("input,select,button").forEach(node => { node.disabled = busy || !editable || !referencesReady || !current?.assignment_active; }); panel.querySelector("[data-terms-reload]").disabled = busy; };
 function options(name, rows, value) {
  const select = form.elements[`values.${name}`], list = rows || [];
  select.innerHTML = `<option value="">${c.choose}</option>` + list.map(row => `<option value="${escape(row.code)}">${escape(row.code)} · ${escape(lang === "en" ? row.name_en || row.name_es : row.name_es || row.name_en)}</option>`).join("");
  if (value && !list.some(row => row.code === value)) select.insertAdjacentHTML("beforeend", `<option value="${escape(value)}">${escape(value)}${referencesReady ? ` (${c.historic})` : ""}</option>`);
  select.value = value || "";
 }
 function status() { state.textContent = !current ? c.loading : !current.assignment_active ? c.inactive : !current.values ? c.pending : current.requires_confirmation ? c.reconfirm : c.confirmed; }
 async function load() {
  busy = true; referencesReady = false; controls(); message.textContent = ""; renderFormFeedback(form, [], { lang });
  try {
   const saved = await getCommercialTerms(kind, record.id, division); if (!panel.isConnected) return;
   current = saved; key = null; fingerprint = null; status();
   // Display confirmed values even if catalogs fail. No values are taken from the master.
   options("currency", [], saved.values?.currency); options("payment_terms", [], saved.values?.payment_terms); form.elements[`values.${extra}`].value = saved.values?.[extra] ?? "";
   if (editable && saved.assignment_active) {
    const references = await getCommercialTermReferences(kind); if (!panel.isConnected) return;
    referencesReady = true; options("currency", references.currencies, saved.values?.currency); options("payment_terms", references.payment_terms, saved.values?.payment_terms);
   }
  } catch (error) { if (panel.isConnected) { message.textContent = getLocalizedErrorMessage(error, { lang }); message.setAttribute("role", "alert"); } }
  finally { busy = false; if (panel.isConnected) controls(); }
 }
 form.onsubmit = async event => {
  event.preventDefault(); if (busy || !editable || !referencesReady || !current?.assignment_active) return;
  const values = { currency: form.elements["values.currency"].value, payment_terms: form.elements["values.payment_terms"].value, [extra]: kind === "customer" ? form.elements[`values.${extra}`].value : Number(form.elements[`values.${extra}`].value) };
  const payload = { expected_revision: current.revision, values }, serialized = JSON.stringify(payload);
  if (fingerprint !== serialized) { fingerprint = serialized; key = `terms-${crypto.randomUUID()}`; }
  message.textContent = ""; message.setAttribute("role", "status"); renderFormFeedback(form, [], { lang });
  busy = true; controls();
  try { const saved = await saveCommercialTerms(kind, record.id, division, payload, key); if (!panel.isConnected) return; current = saved; key = null; fingerprint = null; renderFormFeedback(form, [], { lang }); status(); message.setAttribute("role", "status"); message.textContent = c.saved; }
  catch (error) { if (panel.isConnected) { busy = false; controls(); renderFormFeedback(form, [error], { lang }); } }
  finally { busy = false; if (panel.isConnected) controls(); }
 };
 panel.querySelector("[data-terms-reload]").onclick = load;
 panel.querySelector("[data-terms-close]").onclick = close;
 await load();
}
