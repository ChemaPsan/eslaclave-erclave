import { mountCostCenters } from "./cost-centers.js";
import { costCenterCopy } from "../i18n/cost-centers.js";
import { mountScopedConfiguration } from "./scoped-configuration.js";
import { configurationCopy } from "../i18n/scoped-configuration.js";
import { listOrganization, saveOrganization } from "../api/organization.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
import { organizationCopy } from "../i18n/organization.js";

const stems = { "fiscal-issuers": "fiscal_issuer", societies: "society", divisions: "division" };
const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const contacts = ["contact_name", "contact_email", "contact_phone", "contact_position"];
const fiscalFields = ["legal_name", "tax_id", "fiscal_regime", "cfdi_usage", "fiscal_address", "postal_code", "country_code", ...contacts];
const maxima = { code: 80, tax_id: 80, fiscal_regime: 80, cfdi_usage: 80, fiscal_address: 2000, address: 2000, postal_code: 20, country_code: 2, phone: 80, contact_phone: 80 };

function input(c, field, value = "", { required = false, disabled = false, readonly = false, label = field } = {}) {
  return `<label><span>${escape(c[label])}${required ? " *" : ""}</span><input name="${field}" data-error-path="${field}" value="${escape(value)}" type="${field === "contact_email" ? "email" : "text"}" maxlength="${maxima[field] || 240}" ${required ? "required" : ""} ${disabled ? "disabled" : ""} ${readonly ? "readonly" : ""} ${field === "country_code" ? 'pattern="[A-Za-z]{2}"' : ""}></label>`;
}

export function renderOrganizationPanel(data, lang = "es") {
  const c = organizationCopy[lang === "en" ? "en" : "es"];
  const corporate = data.organization?.corporate || data.tenant || {};
  const canEdit = (data.session?.permissions || []).includes("admin.setting.update");
  const fields = ["commercial_name", "legal_name", "tax_id", "phone", ...contacts];
  return `<section class="admin-section admin-detail-panel organization-panel">
    <details><summary>${c.corporate}</summary><p>${c.corporateHint}</p>
      <form class="admin-form org-form" data-form="admin-update-corporate">
        ${fields.map(field => input(c, field, corporate[field], { required: field === "commercial_name", disabled: !canEdit, label: ["legal_name", "tax_id", "phone"].includes(field) ? `corporate_${field}` : field })).join("")}
        ${canEdit ? `<button class="primary-action" type="submit">${c.updateCorporate}</button>` : ""}
      </form>
    </details>
    <div data-organization-root></div>
  </section>`;
}

export function bindOrganizationPanel(container, data, lang = "es") {
  const root = container.querySelector("[data-organization-root]");
  if (!root) return;
  const c = organizationCopy[lang === "en" ? "en" : "es"];
  const permissions = data.session?.permissions || [];
  const can = (kind, action) => permissions.includes(`admin.${stems[kind]}.${action}`);
  const kinds = Object.keys(stems).filter(kind => can(kind, "read"));
  if (!kinds.length) { root.innerHTML = `<p>${c.noPermission}</p>`; return; }
  let kind = kinds[0], items = [], offset = 0, total = 0, q = "", status = "", version = 0, codeMode = "managed";
  let requestController, pending = false, editing = false, parentController;
  const apiError = error => getLocalizedErrorMessage(error, { lang });
  const button = (action, label, disabled = false) => `<button type="button" class="secondary-action small-action" data-org-action="${action}" ${disabled ? "disabled" : ""}>${label}</button>`;
  const parentKind = () => kind === "societies" ? "fiscal-issuers" : kind === "divisions" ? "societies" : null;
  const parentField = () => kind === "societies" ? "issuer_id" : "society_id";

  root.innerHTML = `<h3>${c.title}</h3><p>${c.description}</p>
    <div class="org-tabs" role="group" aria-label="${c.title}">${kinds.map(value => `<button type="button" class="secondary-action" data-org-kind="${value}">${c[value]}</button>`).join("")}</div>
    <form class="org-toolbar" data-org-search><label><span>${c.search}</span><input name="q" maxlength="240" type="search"></label>
      <label><span>${c.status}</span><select name="status"><option value="">${c.all}</option><option value="active">${c.active}</option><option value="inactive">${c.inactive}</option></select></label>
      <button type="submit" class="secondary-action">${c.find}</button>${button("create", c.create)}</form>
    <p data-org-message role="status" aria-live="polite"></p><div data-org-editor></div><div class="org-list" data-org-list></div>
    <div class="org-actions">${button("previous", c.previous)}<span data-org-count></span>${button("next", c.next)}</div>`;
  const list = root.querySelector("[data-org-list]"), editor = root.querySelector("[data-org-editor]"), message = root.querySelector("[data-org-message]");
  const messageText = (text, failure = false) => { message.textContent = text; message.setAttribute("role", failure ? "alert" : "status"); };
  function controls() {
    root.querySelectorAll("[data-org-kind]").forEach(node => { node.setAttribute("aria-pressed", String(node.dataset.orgKind === kind)); node.disabled = pending || editing; });
    root.querySelector("[data-org-action=create]").hidden = !can(kind, "create");
    root.querySelectorAll("[data-org-search] input,[data-org-search] select,[data-org-search] button").forEach(node => { node.disabled = pending || editing; });
    root.querySelector("[data-org-action=previous]").disabled = pending || editing || offset === 0;
    root.querySelector("[data-org-action=next]").disabled = pending || editing || offset + 25 >= total;
    list.querySelectorAll("button").forEach(node => { node.disabled = pending || editing; });
  }
  function renderList() {
    list.innerHTML = items.length ? items.map(item => `<article class="org-card"><div>
      <small>${escape(item.code)}</small><p><strong>${escape(item.legal_name || item.name)}</strong></p>
      ${item.issuer_name || item.society_name ? `<p>${kind === "societies" ? c.issuer : c.society}: ${escape(item.issuer_name || item.society_name)}</p>` : ""}
      ${item.base_currency ? `<p>${c.base_currency}: ${escape(item.base_currency)}</p>` : ""}
      <span class="chip ${item.status === "active" ? "active" : "warning"}">${c[item.status]}</span>
      </div><div class="org-actions" data-org-id="${escape(item.id)}">
      ${can(kind, "update") ? button("edit", c.edit) : ""}
      ${kind === "divisions" && data.session?.capabilities?.cost_center_catalog?.available && permissions.includes("costing.cost_center.read") ? button("cost-centers", costCenterCopy[lang === "en" ? "en" : "es"].title) : ""}
      ${kind !== "fiscal-issuers" && item.status === "active" && permissions.includes("admin.setting.read") ? button("configuration", configurationCopy[lang === "en" ? "en" : "es"].title) : ""}
      ${can(kind, "status") ? button(item.status === "active" ? "deactivate" : "activate", c[item.status === "active" ? "deactivate" : "activate"]) : ""}
      </div></article>`).join("") : `<p>${c.empty}</p>`;
    root.querySelector("[data-org-count]").textContent = c.count.replace("{total}", total);
  }
  async function load(successMessage = "") {
    requestController?.abort(); requestController = new AbortController();
    const current = ++version; pending = true; controls(); messageText(c.loading);
    try {
      const response = await listOrganization(kind, { q, status, limit: 25, offset }, requestController.signal);
      if (!root.isConnected || current !== version) return;
      items = response.data; total = response.meta.total; codeMode = response.meta.code_mode || "managed";
      renderList(); messageText(successMessage);
    } catch (error) {
      if (root.isConnected && current === version) messageText(apiError(error), true);
    } finally { if (current === version) { pending = false; controls(); } }
  }
  function closeEditor() { parentController?.abort(); editing = false; editor.replaceChildren(); controls(); }
  function openEditor(item = null) {
    editing = true; messageText(""); controls();
    const parent = parentKind(), relation = parentField();
    const maySelect = parent && can(parent, "read");
    const currencies = data.commercialCatalogs?.currencies || [];
    const mayReadCurrency = permissions.includes("admin.catalog.read");
    const currencyOptions = currencies.filter(row => row.status === "active" || row.code === item?.base_currency);
    if (item?.base_currency && !currencyOptions.some(row => row.code === item.base_currency)) currencyOptions.push({ code: item.base_currency, name_es: item.base_currency, name_en: item.base_currency });
    const fields = kind === "fiscal-issuers" ? fiscalFields : kind === "divisions" ? ["name", "address", "phone"] : ["name"];
    const parentValue = item?.[kind === "societies" ? "issuer_name" : "society_name"] || "";
    editor.innerHTML = `<form class="admin-form org-form" data-form="organization-${kind}"><h4 class="org-wide">${item ? c.edit : c.create}: ${c[kind]}</h4>
      ${input(c, "code", item?.code || (codeMode === "manual" ? "" : c.automatic), { readonly: Boolean(item) || codeMode !== "manual", required: !item && codeMode === "manual" })}
      ${fields.map(field => input(c, field, item?.[field], { required: ["name", "legal_name"].includes(field) })).join("")}
      ${parent ? `<div class="org-wide"><label class="entity-select-lookup"><span>${c[relation]} *</span><input name="parent_search" data-error-path="${relation}" value="${escape(parentValue)}" placeholder="${c.select}" autocomplete="off" ${maySelect ? "" : "disabled"} required><input type="hidden" name="${relation}" value="${escape(item?.[relation] || "")}"></label><div class="org-results" data-org-results></div><p data-org-parent-message role="status">${maySelect ? "" : c.parentPermission}</p></div>` : ""}
      ${kind === "societies" ? `<label><span>${c.base_currency} *</span><select name="base_currency" required ${mayReadCurrency ? "" : "disabled"}><option value="">—</option>${currencyOptions.map(row => `<option value="${escape(row.code)}" ${row.code === (item?.base_currency || "MXN") ? "selected" : ""}>${escape(row.code)} · ${escape(row[lang === "en" ? "name_en" : "name_es"] || row.code)}</option>`).join("")}</select></label><p class="org-wide">${mayReadCurrency ? c.currencyHint : c.currencyPermission}</p>` : ""}
      ${kind === "fiscal-issuers" ? `<p class="org-wide">${c.fiscalHint}</p>` : ""}
      <div class="org-actions org-wide"><button class="primary-action" type="submit" ${!item && ((parent && !maySelect) || (kind === "societies" && !mayReadCurrency)) ? "disabled" : ""}>${c.save}</button>${button("cancel", c.cancel)}</div>
    </form>`;
    const form = editor.querySelector("form");
    const parentSearch = form.elements.parent_search;
    let searchVersion = 0, debounce;
    if (maySelect) {
      const searchParents = async () => {
        if (!form.isConnected) return;
        const current = ++searchVersion;
        parentController?.abort(); parentController = new AbortController();
        const results = form.querySelector("[data-org-results]"), notice = form.querySelector("[data-org-parent-message]");
        results.replaceChildren(); notice.textContent = c.loading;
        try {
          const response = await listOrganization(parent, { q: parentSearch.value, status: "active", limit: 10 }, parentController.signal);
          if (!form.isConnected || current !== searchVersion) return;
          notice.textContent = response.data.length ? "" : c.empty;
          response.data.forEach(row => {
            const node = document.createElement("button"); node.type = "button"; node.className = "secondary-action";
            node.textContent = `${row.code} · ${row.legal_name || row.name}`; node.title = row.id;
            node.addEventListener("click", () => { form.elements[relation].value = row.id; parentSearch.value = node.textContent; parentSearch.setCustomValidity(""); parentSearch.dispatchEvent(new Event("change", { bubbles: true })); results.replaceChildren(); notice.textContent = ""; });
            results.append(node);
          });
        } catch (error) { if (form.isConnected && current === searchVersion) notice.textContent = apiError(error); }
      };
      parentSearch.addEventListener("input", () => { searchVersion++; parentController?.abort(); form.elements[relation].value = ""; parentSearch.setCustomValidity(c.selectResult); clearTimeout(debounce); debounce = setTimeout(searchParents, 220); });
      parentSearch.addEventListener("focus", () => { if (!form.elements[relation].value) searchParents(); });
      if (!item) parentSearch.setCustomValidity(c.selectResult);
    }
    let requestKey, fingerprint;
    form.addEventListener("submit", async event => {
      event.preventDefault(); if (pending) return;
      const errors = [];
      if (parent && !form.elements[relation].value) errors.push({ control: parentSearch, message: c.selectResult });
      if (errors.length) { renderFormFeedback(form, errors, { lang }); return; }
      const payload = Object.fromEntries(fields.map(field => [field, form.elements[field].value.trim() || null]));
      if (payload.country_code) payload.country_code = payload.country_code.toUpperCase();
      if (!item && codeMode === "manual") payload.code = form.elements.code.value.trim();
      if (parent && (!item || form.elements[relation].value !== item[relation])) payload[relation] = form.elements[relation].value;
      if (kind === "societies" && (!item || form.elements.base_currency.value !== item.base_currency)) payload.base_currency = form.elements.base_currency.value;
      const serialized = JSON.stringify(payload);
      if (serialized !== fingerprint) { fingerprint = serialized; requestKey = `org-${crypto.randomUUID()}`; }
      pending = true; controls();
      searchVersion++; parentController?.abort();
      const enabled = [...form.elements].filter(node => !node.disabled); enabled.forEach(node => { node.disabled = true; });
      try {
        await saveOrganization(kind, { id: item?.id, payload, key: requestKey });
        if (!form.isConnected) return;
        pending = false; closeEditor(); await load(c.saved);
      } catch (error) {
        enabled.forEach(node => { node.disabled = false; });
        if (!form.isConnected) return;
        const path = error.details?.field;
        if (path && [...fields, "code", relation, "base_currency"].includes(path)) renderFormFeedback(form, [{ field: path, message: apiError(error) }], { lang });
        else renderFormFeedback(form, [error], { lang });
      } finally { pending = false; if (form.isConnected) enabled.forEach(node => { node.disabled = false; }); controls(); }
    });
    form.querySelector("input:not([readonly]):not([disabled])")?.focus();
  }
  root.querySelector("[data-org-search]").addEventListener("submit", event => {
    event.preventDefault(); if (pending || editing) return;
    q = event.currentTarget.elements.q.value.trim(); status = event.currentTarget.elements.status.value; offset = 0; load();
  });
  const statusKeys = new Map();
  root.addEventListener("click", async event => {
    const tab = event.target.closest("[data-org-kind]");
    if (tab && !pending && !editing) { kind = tab.dataset.orgKind; offset = 0; items = []; renderList(); load(); return; }
    const node = event.target.closest("[data-org-action]"); if (!node || node.disabled || pending) return;
    const action = node.dataset.orgAction;
    if (action === "cancel") { closeEditor(); return; }
    if (editing) return;
    if (action === "create") { openEditor(); return; }
    if (["previous", "next"].includes(action)) { offset += action === "next" ? 25 : -25; load(); return; }
    const item = items.find(row => row.id === node.closest("[data-org-id]")?.dataset.orgId); if (!item) return;
    if (action === "cost-centers") { editing = true; controls(); mountCostCenters(editor, item, permissions, lang, closeEditor); return; }
    if (action === "configuration") { editing = true; controls(); await mountScopedConfiguration(editor, kind === "societies" ? "society" : "division", item, permissions, lang, closeEditor); return; }
    if (action === "edit") { openEditor(item); return; }
    if (!["activate", "deactivate"].includes(action)) return;
    const target = `${kind}:${item.id}:${action}`;
    if (!statusKeys.has(target)) statusKeys.set(target, `org-${crypto.randomUUID()}`);
    pending = true; controls();
    try {
      await saveOrganization(kind, { id: item.id, action, key: statusKeys.get(target) });
      statusKeys.delete(target); await load(c.saved);
    } catch (error) { messageText(apiError(error), true); }
    finally { pending = false; controls(); }
  });
  load();
}
