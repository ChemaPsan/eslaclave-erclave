import { getMembershipScope, saveMembershipScope } from "../api/organization-scope.js";
import { listOrganization } from "../api/organization.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
import { scopeCopy } from "../i18n/organization-scope.js";

const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));

export function divisionPreferenceKey(context) {
  return `erclave-active-division:${context?.tenant?.id || ""}:${context?.user?.id || ""}`;
}

export function availableDivisions(context) {
  const societies = new Map((context?.scope?.societies || []).map(row => [row.id, row]));
  return (context?.scope?.divisions || []).filter(row => societies.has(row.society_id))
    .map(row => ({ ...row, name: `${societies.get(row.society_id).name} / ${row.name}` }));
}

export async function mountScopeEditor(root, userId, permissions, lang = "es", onSaved = () => {}) {
  const c = scopeCopy[lang] || scopeCopy.es;
  root.innerHTML = `<p role="status">${c.loading}</p>`;
  let original;
  try { original = await getMembershipScope(userId); }
  catch (error) { if (root.isConnected) root.innerHTML = `<p role="alert">${escape(getLocalizedErrorMessage(error, { lang }))}</p>`; return; }
  if (!root.isConnected) return;
  const selected = new Map(original.division_ids.filter(id => id !== "*").map(id => [id, original.divisions?.find(row => row.id === id) || { id, name: id }]));
  const canSearch = permissions.includes("admin.division.read");
  const canSave = permissions.includes("admin.user.update");
  let pending = false, searchRevision = 0, priorPayload = "", commandKey;
  root.innerHTML = `<form class="admin-form organization-scope-form" data-form="organization-scope">
    <label><span>${c.edit}</span><select name="mode"><option value="restricted">${c.restricted}</option><option value="all" ${original.division_ids.includes("*") ? "selected" : ""}>${c.all}</option></select></label>
    <p>${c.hint}</p><div data-scope-restricted><label><span>${c.search}</span><input name="division_search" autocomplete="off" ${canSearch ? "" : "disabled"}></label>
    <button type="button" data-scope-search ${canSearch ? "" : "disabled"}>${c.find}</button>
    ${canSearch ? "" : `<p>${c.catalogPermission}</p>`}<div data-scope-results role="group" aria-label="${c.search}"></div>
    <p>${c.selected}</p><div data-scope-selected role="group" aria-label="${c.selected}"></div></div>
    <button class="primary-action" type="submit" ${canSave ? "" : "disabled"}>${c.save}</button><p data-scope-message role="status"></p></form>`;
  const form = root.querySelector("form"), mode = form.elements.mode;
  function renderSelected() {
    form.querySelector("[data-scope-selected]").innerHTML = [...selected.values()].map(row => `<p>${escape(row.code || "")} ${escape(row.name)} <button type="button" data-scope-remove="${escape(row.id)}">${c.remove}</button></p>`).join("");
    form.querySelectorAll("[data-scope-remove]").forEach(button => button.addEventListener("click", () => { selected.delete(button.dataset.scopeRemove); renderSelected(); }));
  }
  function toggle() { form.querySelector("[data-scope-restricted]").hidden = mode.value === "all"; }
  mode.addEventListener("change", toggle); toggle(); renderSelected();
  form.querySelector("[data-scope-search]").addEventListener("click", async () => {
    if (pending || !canSearch) return;
    const current = ++searchRevision;
    const message = form.querySelector("[data-scope-message]"); message.textContent = c.loading;
    try {
      const result = await listOrganization("divisions", { q: form.elements.division_search.value.trim(), status: "active", limit: 10 });
      if (!root.isConnected || current !== searchRevision) return;
      const target = form.querySelector("[data-scope-results]");
      target.innerHTML = result.data.map(row => `<p>${escape(row.society_name)} / ${escape(row.code)} · ${escape(row.name)} <button type="button" data-scope-add="${escape(row.id)}">${c.add}</button></p>`).join("") || `<p>${c.empty}</p>`;
      target.querySelectorAll("[data-scope-add]").forEach(button => button.addEventListener("click", () => {
        const row = result.data.find(item => item.id === button.dataset.scopeAdd);
        selected.set(row.id, row); renderSelected();
      })); message.textContent = "";
    } catch (error) { if (root.isConnected && current === searchRevision) renderFormFeedback(form, [error], { lang }); }
  });
  form.addEventListener("submit", async event => {
    event.preventDefault(); if (pending || !canSave) return;
    const all = mode.value === "all";
    // Existing references may be outside the first search page. Preserve their IDs and parent grants.
    const payload = { version: 2, expected_revision: original.revision,
      society_ids: all ? ["*"] : [...new Set([...selected.values()].flatMap(row => row.society_id ? [row.society_id] : original.society_ids))],
      division_ids: all ? ["*"] : [...selected.keys()] };
    if (!all && !payload.division_ids.length) payload.society_ids = [];
    const serialized = JSON.stringify(payload);
    if (serialized !== priorPayload) { commandKey = `scope-${crypto.randomUUID()}`; priorPayload = serialized; }
    pending = true; ++searchRevision;
    const controls = [...form.querySelectorAll("input,select,button")].map(node => [node, node.disabled]);
    controls.forEach(([node]) => { node.disabled = true; });
    try {
      original = await saveMembershipScope(userId, payload, commandKey);
      if (root.isConnected) { renderFormFeedback(form, [], { lang }); form.querySelector("[data-scope-message]").textContent = c.saved; onSaved(); }
    } catch (error) { if (root.isConnected) renderFormFeedback(form, [error], { lang }); }
    finally { pending = false; controls.forEach(([node, disabled]) => { node.disabled = disabled; }); }
  });
}
