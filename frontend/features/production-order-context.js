import { getDivisionRecipes, validateProductionResources, createProductionOrder, getProductionRequestRecipes, validateProductionRequestResources, createProductionRequestOrder } from "../api/production.js";
import { getDivisionProductionWorkers } from "../api/hr-organization.js";
import { productionOrderCopy } from "../i18n/production-order-context.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
export function renderProductionOrderContext(context, lang = "es") {
 const c = productionOrderCopy[lang === "en" ? "en" : "es"];
 if (!context) return `<p class="helper-copy">${c.legacy}</p>`;
 return `<section class="production-order-context-summary"><strong>${c.history}</strong><p>${c.division}: ${escape(context.division_code)} · ${escape(context.division_name)}</p><p>${c.society}: ${escape(context.society_ref_id)} · ${c.currency}: ${escape(context.cost_currency)}</p></section>`;
}
export async function mountProductionOrderForm(root, session, { lang = "es", today = "", managedCode = false, resolveCode, onSaved, onClose, sourceRequest = null } = {}) {
 const c = productionOrderCopy[lang === "en" ? "en" : "es"], permissions = session?.permissions || [];
 const canRelease = permissions.includes("production.order.release"), canValidate = permissions.includes("production.order.validate") || canRelease;
 const sourceContext = sourceRequest?.organization_context;
 const validate = (payload,key) => sourceRequest ? validateProductionRequestResources(sourceRequest.id,payload,key) : validateProductionResources(payload,key);
 const create = (payload,key) => sourceRequest ? createProductionRequestOrder(sourceRequest.id,payload,key) : createProductionOrder(payload,key);
 const divisions = session?.scope?.version === 2 ? session.scope.divisions || [] : [];
 root.innerHTML = `<form data-form="production-order-context" class="production-order-context-form"><div class="modal-head"><h2>${c.title}</h2><button type="button" data-close class="secondary-action">${c.close}</button></div><p>${sourceRequest ? c.sourceHint : c.hint}</p>${sourceRequest ? `<p data-source-product>${c.product}: ${escape(sourceRequest.product_service_code)} · ${escape(sourceRequest.product_service_name)}</p>` : `<p>${c.changed}</p>`}<div data-division-lookup></div><p data-society-context></p><div data-recipe-lookup></div><div class="production-order-context-grid"><label><span>${c.code}</span><input name="code" maxlength="80" ${managedCode ? 'readonly' : ''} placeholder="${managedCode ? c.managed : ''}"></label><label><span>${c.quantity}</span><input name="quantity" type="number" min="0" step="any" required value="${escape(sourceRequest?.original_quantity ?? sourceRequest?.quantity ?? '1')}" ${sourceRequest ? 'readonly' : ''}></label><label><span>${c.unit}</span><input name="unit" readonly required></label><label><span>${c.start}</span><input name="planned_start_date" type="date" required value="${escape(today)}"></label><label><span>${c.days}</span><input name="planned_duration_days" type="number" min="1" max="365" step="1" required value="1"></label><label><span>${c.due}</span><input name="required_date" data-error-path="required_at" type="date" required value="${escape(today)}"></label><label><span>${c.priority}</span><select name="priority"><option value="medium">${c.medium}</option><option value="high">${c.high}</option><option value="low">${c.low}</option></select></label></div><div data-worker-lookup></div><h3>${c.stages}</h3><div data-stage-lookups></div><div class="production-order-context-actions">${canValidate ? `<button type="button" data-validate class="secondary-action">${c.validate}</button>` : ''}${canRelease ? `<button type="submit" class="primary-action">${c.release}</button>` : ''}</div><div data-validation-preview role="status"></div><p data-order-message role="status"></p></form>`;
 const form = root.querySelector("form"), preview = form.querySelector("[data-validation-preview]"), message = form.querySelector("[data-order-message]");
 let division = null, society = null, recipe = null, version = null, responsible = null, assignments = new Map(), busy = false, selectionRevision = 0, recipeRevision = 0, lastCreate = null;
 const commands = new Map(), codeKey = `order-code-${crypto.randomUUID()}`; let resolvedCode = null, resolvedCodeInput = null;
 function commandKey(kind, payload) { const fingerprint = JSON.stringify(payload), prior = commands.get(kind); if (prior?.fingerprint === fingerprint) return prior.key; const key = `production-${kind}-${crypto.randomUUID()}`; commands.set(kind, { fingerprint, key }); return key; }
 function invalidate() { preview.replaceChildren(); message.textContent = ""; }
 function lock(value) { busy = value; form.querySelectorAll("button,input,select").forEach(node => { node.disabled = value || node.hasAttribute("data-unavailable"); }); }
 function feedback(error) { renderFormFeedback(form, [error], { lang }); }
 async function lookup(container, field, label, load, onPick) {
  const generation = selectionRevision, token = crypto.randomUUID(); container.dataset.lookupToken = token;
  const valid = () => container.isConnected && container.dataset.lookupToken === token && (field === "division_ref_id" || generation === selectionRevision);
  container.innerHTML = `<div class="production-order-context-lookup"><label><span>${label}</span><input type="search" name="${field}_search" data-error-path="${field}" maxlength="240" autocomplete="off"></label><div class="production-order-context-actions"><button type="button" data-find>${c.search}</button><button type="button" data-prev disabled data-unavailable>${c.previous}</button><button type="button" data-next disabled data-unavailable>${c.next}</button></div><p data-selected>${c.choose}</p><div data-options></div><p data-search-error role="status"></p></div>`;
  let offset = 0, query = "", pending = false, rows = [], requestVersion = 0;
  const options = container.querySelector("[data-options]"), search = container.querySelector("input"), previous = container.querySelector("[data-prev]"), next = container.querySelector("[data-next]");
  async function fetchPage() {
   if (busy || pending) return; pending = true; const ticket = ++requestVersion;
   container.querySelectorAll("button,input").forEach(node => node.disabled = true);
   try {
    const response = await load(query, offset);
    if (!valid() || ticket !== requestVersion) return;
    rows = response.data || []; const total = response.meta?.total ?? response.page?.total;
    const hasMore = total == null ? Boolean(response.page?.next_cursor) || rows.length === 20 : offset + 20 < total;
    options.innerHTML = rows.map((row, index) => `<button class="secondary-action" type="button" data-choice="${index}">${escape(row.label || [row.code || row.employee_number, row.name || row.full_name].filter(Boolean).join(' · '))}</button>`).join('') || `<p>${c.empty}</p>`;
    previous.toggleAttribute("data-unavailable", offset === 0); next.toggleAttribute("data-unavailable", !hasMore);
    container.querySelector("[data-search-error]").textContent = "";
   } catch (error) { if (valid()) { const target = container.querySelector("[data-search-error]"); target.setAttribute("role", "alert"); target.textContent = getLocalizedErrorMessage(error, { lang }); } }
   finally { pending = false; if (valid()) container.querySelectorAll("button,input").forEach(node => node.disabled = busy || node.hasAttribute("data-unavailable")); }
  }
  options.onclick = event => { const choice = event.target.closest("[data-choice]"); if (!choice || pending || busy || !valid()) return; const row = rows[Number(choice.dataset.choice)]; container.querySelector("[data-selected]").textContent = row.label || [row.code || row.employee_number, row.name || row.full_name].filter(Boolean).join(' · '); renderFormFeedback(form, [], { lang }); invalidate(); onPick(row); };
  container.querySelector("[data-find]").onclick = () => { query = search.value.trim(); offset = 0; fetchPage(); };
  search.onkeydown = event => { if (event.key === "Enter") { event.preventDefault(); container.querySelector("[data-find]").click(); } };
  previous.onclick = () => { offset = Math.max(0, offset - 20); fetchPage(); }; next.onclick = () => { offset += 20; fetchPage(); };
  await fetchPage();
 }
 async function chooseRecipe(row) {
  const recipeTicket = ++recipeRevision;
  recipe = row; version = row.versions?.find(item => item.id === row.current_version_id && item.status === "approved") || null;
  responsible = null; assignments = new Map(); form.elements.unit.value = sourceRequest?.unit || version?.base_unit || "";
  const stages = form.querySelector("[data-stage-lookups]"); stages.replaceChildren(); form.querySelector("[data-worker-lookup]").replaceChildren();
  if (!version) { feedback({ field: "recipe_version_id", message: c.selectRecipe }); return; }
  const selectedDivision = division.id;
  const load = (q, offset) => getDivisionProductionWorkers(selectedDivision, q, offset);
  await lookup(form.querySelector("[data-worker-lookup]"), "responsible_worker_id", c.responsible, load, worker => { responsible = worker; });
  if (recipeTicket !== recipeRevision || division?.id !== selectedDivision || recipe?.id !== row.id) return;
  for (const [index, stage] of (version.stages || []).filter(item => item.status === "active").entries()) {
   if (!form.isConnected || division?.id !== selectedDivision || recipe?.id !== row.id || recipeTicket !== recipeRevision) return;
   const area = document.createElement("div"); stages.append(area);
   await lookup(area, `stage_assignments.${index}.responsible_worker_id`, stage.name, load, worker => assignments.set(stage.id, worker));
  }
 }
 async function chooseDivision(row) {
  selectionRevision++; recipeRevision++; division = row; society = session.scope?.societies?.find(item => item.id === row.society_id); recipe = null; version = null; responsible = null; assignments = new Map();
  form.elements.unit.value = ""; form.querySelector("[data-worker-lookup]").replaceChildren(); form.querySelector("[data-stage-lookups]").replaceChildren();
  form.querySelector("[data-society-context]").textContent = society?.base_currency ? `${c.society}: ${society.code || ''} · ${society.name || society.id} · ${c.currency}: ${society.base_currency}` : c.currencyMissing;
  await lookup(form.querySelector("[data-recipe-lookup]"), "recipe_version_id", c.recipe, (q, offset) => sourceRequest ? getProductionRequestRecipes(sourceRequest.id, q, offset) : getDivisionRecipes(row.id, q, offset), chooseRecipe);
  if(sourceRequest)form.querySelector("[data-recipe-lookup] input").maxLength=120;
 }
 function capture(requireWorkers) {
  if (!division) { feedback({ field: "division_ref_id", message: c.selectDivision }); return null; }
  if (!society?.base_currency) { feedback(c.currencyMissing); return null; }
  if (!recipe || !version) { feedback({ field: "recipe_version_id", message: c.selectRecipe }); return null; }
  if (!form.reportValidity()) return null;
  const stages = (version.stages || []).filter(row => row.status === "active");
  if (!(Number(form.elements.quantity.value) > 0)) { feedback({ field: "quantity", message: c.positiveQuantity }); return null; }
  if (requireWorkers && (!responsible || stages.some(stage => !assignments.has(stage.id)))) { const missingIndex = stages.findIndex(stage => !assignments.has(stage.id)); feedback({ field: !responsible ? "responsible_worker_id" : `stage_assignments.${missingIndex}.responsible_worker_id`, message: c.selectWorkers }); return null; }
  const validation = { division_ref_id: division.id, recipe_version_id: version.id, quantity: sourceRequest ? String(sourceRequest.original_quantity ?? sourceRequest.quantity) : form.elements.quantity.value, unit: sourceRequest?.unit || version.base_unit, planned_start_date: form.elements.planned_start_date.value, planned_duration_days: Number(form.elements.planned_duration_days.value) };
  return { validation, stages };
 }
 function showValidation(value) {
  const currency = value.cost_currency || value.organization_context?.cost_currency;
  preview.innerHTML = `<p>${value.can_release ? c.ready : c.blocked}</p><p>${c.planned}: ${escape(value.original_planned_cost ?? value.planned_cost)} ${escape(currency || '')}</p>${(value.rows || []).map(row => `<article><strong>${escape(row.resource_name)}</strong><p>${c.required}: ${escape(row.required_quantity)} / ${c.available}: ${escape(row.available_quantity)} ${escape(row.unit)}</p><p>${escape(row.original_total_cost ?? row.total_cost)} ${escape(row.cost_currency || currency || '')}</p>${row.blocker_code ? `<p>${escape(getLocalizedErrorMessage({ code: row.blocker_code, status: 422 }, { lang }))}</p>` : ''}</article>`).join('')}`;
 }
 async function run(release) {
  if (busy || !canValidate || (release && !canRelease)) return;
  const input = capture(release); if (!input) return;
  const base = { ...input.validation, code: form.elements.code.value.trim() || null, planned_start_at: new Date(`${form.elements.planned_start_date.value}T08:00:00`).toISOString(), required_at: new Date(`${form.elements.required_date.value}T23:59:59`).toISOString(), priority: form.elements.priority.value, responsible_worker_id: responsible?.id, stage_assignments: input.stages.map(stage => ({ recipe_stage_id: stage.id, responsible_worker_id: assignments.get(stage.id)?.id })), ...(sourceRequest ? {} : {source_type: "manual"}) };
  const captureFingerprint = JSON.stringify(base);
  lock(true); renderFormFeedback(form, [], { lang });
  try {
   if (release && lastCreate?.fingerprint === captureFingerprint) { const saved = await create(lastCreate.payload, lastCreate.key); if (form.isConnected) { commands.clear(); lastCreate = null; message.textContent = c.saved; await onSaved?.(saved); } return; }
   const validation = await validate(input.validation, commandKey("validate", input.validation));
   if (!form.isConnected) return; showValidation(validation);
   if (!release || !validation.can_release) return;
   if (resolveCode && (resolvedCode === null || resolvedCodeInput !== base.code)) { resolvedCode = await resolveCode(base.code || "", codeKey); resolvedCodeInput = base.code; }
   const payload = { ...base, code: resolvedCode ?? base.code };
   const createKey = commandKey("create", payload); lastCreate = { fingerprint: captureFingerprint, payload, key: createKey };
   const saved = await create(payload, createKey);
   if (form.isConnected) { commands.clear(); lastCreate = null; message.textContent = c.saved; await onSaved?.(saved); }
  } catch (error) { if (form.isConnected) { lock(false); feedback(error); } }
  finally { if (form.isConnected) lock(false); }
 }
 form.oninput = event => { if (event.target.type !== "search") invalidate(); };
 form.onchange = invalidate; form.onsubmit = event => { event.preventDefault(); run(true); };
 form.querySelector("[data-validate]")?.addEventListener("click", () => run(false)); form.querySelector("[data-close]").onclick = () => onClose?.();
 if (!divisions.length) { message.textContent = c.scopeMissing; form.querySelectorAll("input,button,select").forEach(node => { if (!node.hasAttribute("data-close")) { node.setAttribute("data-unavailable", ""); node.disabled = true; } }); return; }
 if (sourceRequest) {
  const fixed = divisions.find(row => row.id === sourceContext?.division_ref_id);
  if (!fixed || sourceRequest.production_order_id || sourceRequest.production_order_ref_id) { message.textContent = fixed ? c.requestConverted : c.scopeMissing; form.querySelectorAll("input,button,select").forEach(node => { if (!node.hasAttribute("data-close")) { node.setAttribute("data-unavailable", ""); node.disabled = true; } }); return; }
  form.querySelector("[data-division-lookup]").innerHTML = `<label><span>${c.division}</span><input name="division_ref_id" readonly value="${escape(fixed.code || fixed.name || fixed.id)}"></label>`;
  form.elements.unit.value = sourceRequest.unit;
  if (sourceRequest.requested_due_date) form.elements.required_date.value = sourceRequest.requested_due_date.slice(0,10);
  await chooseDivision(fixed); form.elements.unit.value = sourceRequest.unit; return;
 }
 // Division remains an explicit choice; the browser preference never becomes document authority.
 await lookup(form.querySelector("[data-division-lookup]"), "division_ref_id", c.division, async (q, offset) => { const rows = divisions.filter(row => [row.code,row.name].join(' ').toLowerCase().includes(q.toLowerCase())); return { data: rows.slice(offset,offset+20), meta: { total: rows.length } }; }, chooseDivision);
}
