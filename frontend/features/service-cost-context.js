import { societyRateContext } from "./resource-rate-context.js";
import { serviceCostCopy } from "../i18n/service-cost-context.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
const contexts = new WeakMap();
export function mountServiceCostContext(form, record, session, lang = "es") {
 if (!form || !record.fields?.divisionRefId) return;
 const c = serviceCostCopy[lang === "en" ? "en" : "es"], context = societyRateContext(session, record.fields.divisionRefId);
 const currency = context?.societyId === record.fields.societyRefId ? context.currency : null;
 const documentCurrency = record.fields.currency || record.fields.commercialTermsSnapshot?.values?.currency;
 const usable = Boolean(currency && documentCurrency), different = usable && currency !== documentCurrency;
 contexts.set(form, { currency, documentCurrency, different, usable, c });
 const group = document.createElement("div"); group.className = "service-cost-context wide-field";
 group.innerHTML = `<label class="preview-field"><span>${c.currency}</span><input name="cost_currency" readonly value="${escape(currency || '')}"></label><p>${c.document}: ${escape(documentCurrency || '')}</p><label class="preview-field" data-service-rate ${different ? '' : 'hidden'}><span>${c.rate}: 1 ${escape(currency || '')} = … ${escape(documentCurrency || '')}</span><input name="cost_exchange_rate" type="number" min="0.000000000001" max="999999999999.999999999999" step="0.000000000001" ${different ? 'required' : 'disabled value="1"'}></label><label class="service-cost-confirm"><input name="confirm_cost_currency" type="checkbox" required><span>${c.confirm}</span></label>${usable ? '' : `<p role="alert">${c.missing}</p>`}`;
 form.querySelector('[type="submit"]').before(group);
 if (!usable) form.querySelector('[type="submit"]').disabled = true;
 for (const name of ["hourly_cost", "unit_cost"]) { const field = form.elements[name]; if (field) { field.step = "0.000001"; field.max = "999999999999.999999"; field.addEventListener("input", () => { form.elements.confirm_cost_currency.checked = false; }); } }
}
export function serviceCostPayload(form) {
 const context = contexts.get(form); if (!context) return {};
 if (!context.usable) throw { code: "operational_cost_currency_unavailable", status: 422 };
 if (!form.elements.confirm_cost_currency.checked) throw { field: "confirm_cost_currency", message: context.c.confirmation };
 const rate = context.different ? form.elements.cost_exchange_rate.value : "1";
 if (!(Number(rate) > 0)) throw { field: "cost_exchange_rate", message: context.c.positive };
 return { cost_currency: context.currency, cost_exchange_rate: rate };
}
export function renderServiceCostHistory(entry, documentCurrency, lang = "es") {
 const c = serviceCostCopy[lang === "en" ? "en" : "es"];
 if (!entry.cost_currency) return `${escape(entry.total_cost ?? '0')} ${escape(documentCurrency || '')}<small>${c.legacy}</small>`;
 return `${c.original}: ${escape(entry.original_total_cost)} ${escape(entry.cost_currency)}<small>1 ${escape(entry.cost_currency)} = ${escape(entry.cost_exchange_rate)} ${escape(entry.document_currency)} · ${c.converted}: ${escape(entry.total_cost)} ${escape(entry.document_currency)}</small>`;
}
