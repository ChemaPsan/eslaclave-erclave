import { scopedTemplate } from "../api/scoped-configuration.js";
import { configurationCopy } from "../i18n/scoped-configuration.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
const generations = new WeakMap();
export async function mountScopedConfiguration(root, kind, item, permissions, lang = "es", close = () => {}) {
  const generation = Symbol(); generations.set(root, generation);
  const dismiss = () => { generations.delete(root); close(); };
  const c = configurationCopy[lang === "en" ? "en" : "es"];
  root.innerHTML = `<p role="status">${c.loading}</p><button type="button" data-config-close>${c.close}</button>`;
  root.querySelector("[data-config-close]").onclick = dismiss;
  let current;
  try { current = await scopedTemplate(kind, item.id); }
  catch (error) { if (root.isConnected && generations.get(root) === generation) root.insertAdjacentHTML("afterbegin", `<p role="alert">${escape(getLocalizedErrorMessage(error, { lang }))}</p>`); return; }
  if (!root.isConnected || generations.get(root) !== generation || !root.querySelector("[data-config-close]")) return;
  const canSave = permissions.includes("admin.setting.update");
  root.innerHTML = `<h4>${c.title}: ${escape(item.code)} · ${escape(item.name)}</h4><p>${c.hint}</p>
    <p data-config-origin></p><form class="admin-form org-form scoped-configuration-form" data-form="scoped-configuration">
    ${["primary_color", "accent_color", "text_color"].map(field => `<label><span>${c[field]}</span><input type="text" name="${field}" data-error-path="value.${field}" pattern="#[0-9a-fA-F]{6}" maxlength="7" required value="${escape(current.value[field])}" ${canSave ? "" : "disabled"}></label>`).join("")}
    <label><span>${c.footer_text}</span><input name="footer_text" data-error-path="value.footer_text" maxlength="300" value="${escape(current.value.footer_text)}" ${canSave ? "" : "disabled"}></label>
    <label><input type="checkbox" name="show_page_number" ${current.value.show_page_number ? "checked" : ""} ${canSave ? "" : "disabled"}>${c.show_page_number}</label>
    <button type="submit" class="primary-action" ${canSave ? "" : "disabled"}>${c.save}</button>
    <button type="button" class="secondary-action" data-config-reset ${canSave ? "" : "disabled"}>${c.reset}</button>
    <button type="button" class="secondary-action" data-config-close>${c.close}</button><p role="status" data-config-message></p></form>`;
  const form = root.querySelector("form");
  let pending = false, fingerprint, key;
  const showOrigin = () => { root.querySelector("[data-config-origin]").textContent = `${current.override ? c.own : c.inherited}: ${c[current.resolved_from_scope]}`; };
  showOrigin(); root.querySelector("[data-config-close]").onclick = dismiss;
  async function save(reset) {
    if (pending || !canSave) return;
    const value = reset ? null : { ...current.value,
      ...Object.fromEntries(["primary_color", "accent_color", "text_color", "footer_text"].map(name => [name, form.elements[name].value])),
      show_page_number: form.elements.show_page_number.checked };
    const payload = { expected_revision: current.revision, value }, serialized = JSON.stringify(payload);
    if (serialized !== fingerprint) { fingerprint = serialized; key = `config-${crypto.randomUUID()}`; }
    pending = true;
    const controls = [...form.elements].map(node => [node, node.disabled]); controls.forEach(([node]) => { node.disabled = true; });
    try {
      const response = await scopedTemplate(kind, item.id, payload, key);
      if (!form.isConnected) return;
      current = response; showOrigin(); renderFormFeedback(form, [], { lang });
      if (reset) { for (const name of ["primary_color", "accent_color", "text_color", "footer_text"]) form.elements[name].value = current.value[name] || ""; form.elements.show_page_number.checked = current.value.show_page_number; }
      form.querySelector("[data-config-message]").textContent = c.saved;
    } catch (error) {
      if (form.isConnected) renderFormFeedback(form, [error], { lang });
    } finally { pending = false; controls.forEach(([node, disabled]) => { node.disabled = disabled; }); }
  }
  form.addEventListener("submit", event => { event.preventDefault(); save(false); });
  form.querySelector("[data-config-reset]").onclick = () => save(true);
}
