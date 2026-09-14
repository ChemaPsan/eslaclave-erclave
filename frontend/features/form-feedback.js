import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
import { captureFormBindings } from "./form-bindings.js";
import { FORM_BUSINESS_ERRORS, VALIDATION_RULES } from "../i18n/form-business-errors.js";

// Request ownership is captured synchronously, before auth/HTTP awaits. Never
// persist drafts or infer a field from a translated diagnostic message.
export const FORM_REQUEST_EVENT = "erclave:form-request";
export const FORM_ERROR_EVENT = "erclave:form-error";
export const FORM_COMPLETE_EVENT = "erclave:form-complete";
const records = new WeakMap();
const handled = new WeakSet();
let activeForm = null;
let language = () => "es";
let sequence = 0;
const pendingRequests = new WeakMap();
function finishInteraction(form) {
  setTimeout(() => { if(activeForm === form && !pendingRequests.get(form))activeForm = null; }, 0);
}
const copy = {
  es: { title: "Revisa lo siguiente para continuar:", general: "Revisa el requisito indicado antes de continuar.", required: "Completa este campo.", select: "Selecciona un resultado de la lista.", invalid: "Revisa el formato de este campo.", short: "Escribe al menos {limit} caracteres.", long: "Usa como máximo {limit} caracteres.", min: "El valor debe ser mayor o igual a {limit}.", gt: "El valor debe ser mayor que {limit}.", max: "El valor debe ser menor o igual a {limit}.", lt: "El valor debe ser menor que {limit}.", number: "Escribe un número válido.", date: "Escribe una fecha válida.", email: "Escribe un correo electrónico válido.", step: "Usa un valor válido para el incremento permitido.", unknown: "La solicitud contiene un dato que este formulario no permite corregir. Contacta a soporte si el problema continúa.", reference: "Referencia para soporte", row: "Partida" },
  en: { title: "Review the following to continue:", general: "Review the indicated requirement before continuing.", required: "Complete this field.", select: "Select a result from the list.", invalid: "Check this field's format.", short: "Enter at least {limit} characters.", long: "Use no more than {limit} characters.", min: "The value must be at least {limit}.", gt: "The value must be greater than {limit}.", max: "The value must be at most {limit}.", lt: "The value must be less than {limit}.", number: "Enter a valid number.", date: "Enter a valid date.", email: "Enter a valid email address.", step: "Use a valid value for the permitted increment.", unknown: "The request contains a value that cannot be corrected in this form. Contact support if the problem persists.", reference: "Support reference", row: "Line" }
};
const aliases = {
  movement_type: "movementType", inventory_item_id: "itemId", warehouse_id: "warehouseId", destination_warehouse_id: "destinationWarehouseId", "source.id": "sourceDocument", occurred_at: "movementDate",
  business_center: "businessCenter", inventory_policy: "policy", base_unit: "unit", suggested_warehouse_id: "defaultWarehouseId", minimum_stock: "minStock", maximum_stock: "maxStock", default_unit_cost: "defaultUnitCost", use_in_recipe: "useInRecipe",
  "primary_contact.name": "contactName", "primary_contact.email": "contactEmail", "primary_contact.phone": "contactPhone", legal_name: "billingLegalName", "billing_address.exterior_number": "billingExterior", "billing_address.interior_number": "billingInterior", "billing_address.postal_code": "billingZipCode",
  labor_area_id: "areaId", recipe_name: "name", resource_quantity: "quantity", area_ref_id: "areaId", available_minutes_per_day: "available", cost_per_minute: "cost", responsible_area: "owner", cost_center: "center", promised_delivery_date: "deliveryPromise", valid_until: "validUntil", scheduled_date: "deliveryDate", recipient_name: "recipient", evidence_reference: "deliveryReference"
};
const businessFields = {
  item_base_unit_locked_by_movements: ["base_unit"],
  movement_unit_must_match_item_base_unit: ["unit"], movement_reference_invalid: ["inventory_item_id", "warehouse_id"], movement_reference_inactive: ["inventory_item_id", "warehouse_id"], insufficient_available_stock: ["quantity"], insufficient_stock: ["quantity"], unit_not_found: ["unit"], unit_inactive: ["unit"], warehouse_conflict: ["code"], item_conflict: ["code"], transfer_destination_required: ["destination_warehouse_id"], maximum_stock_must_be_greater_than_or_equal_to_minimum_stock: ["maximum_stock"]
};
function strings(lang) { return copy[lang === "en" ? "en" : "es"]; }
function interpolate(value, limit) { return value.replace("{limit}", String(limit)); }
function elements(form) { return [...form.querySelectorAll("input,select,textarea")]; }
function visibleControl(control) {
  if (!control) return null;
  const label = control.closest("label,.preview-field,.field");
  if (control.type === "hidden" || control.hidden || getComputedStyle(control).display === "none") {
    control = label?.querySelector('input:not([type="hidden"]):not([hidden])') || null;
  }
  return control && !control.disabled && !control.closest("[hidden]") && control.getClientRects().length ? control : null;
}
function field(form, path, context) {
  const key = path.filter(x => !["body", "query", "path"].includes(x)).join(".");
  const explicit = elements(form).filter(x => (x.dataset.errorPath || "").split(/\s+/).includes(key));
  if(explicit.length === 1)return visibleControl(explicit[0]);
  // Explicit bindings take precedence and support row identities after filtering.
  const binding = context?.bindings?.[key] || form.formFeedbackBindings?.[key];
  if (binding) return visibleControl(typeof binding === "string" ? form.querySelector(binding) : binding);
  if (path.some(x => typeof x === "number" || /^\d+$/.test(String(x)))) return null;
  const names = [key, aliases[key], key.replace(/_([a-z])/g, (_,c) => c.toUpperCase())].filter(Boolean);
  const matches = elements(form).filter(x => names.includes(x.name));
  return matches.length === 1 ? visibleControl(matches[0]) : null;
}
function ruleControls(form, paths, context) {
  const controls=[];
  for(const path of paths){
    if(path.includes("*")){
      const parts=path.split(".");
      for(const [key,control] of Object.entries(context?.bindings||{})){
        const actual=key.split(".");
        if(actual.length===parts.length&&parts.every((part,i)=>part===actual[i]||(part==="*"&&/^\d+$/.test(actual[i]))))controls.push(visibleControl(control));
      }
    }else controls.push(field(form,[path],context));
  }
  return [...new Set(controls.filter(Boolean))];
}
function changedSinceRequest(context) {
  if (!context?.values) return false;
  const current = elements(context.form).filter(control => control.type !== "password" && control.type !== "file");
  return current.length !== context.values.size || current.some(control => !context.values.has(control)) ||
    [...context.values].some(([control, snapshot]) => !control.isConnected || control.value !== snapshot.value || control.checked !== snapshot.checked);
}
function label(control) {
  const owner = control.closest("label,.preview-field,.field");
  return owner?.querySelector("span,strong")?.textContent?.trim() || control.labels?.[0]?.textContent?.trim() || control.getAttribute("aria-label") || "";
}
function issueMessage(issue, lang) {
  const c = strings(lang), t = String(issue.type || ""), ctx = issue.ctx || {};
  if (t === "missing" || t === "value_error.missing") return c.required;
  for (const [type, key, constraint] of [["string_too_short","short","min_length"],["string_too_long","long","max_length"],["greater_than_equal","min","ge"],["greater_than","gt","gt"],["less_than_equal","max","le"],["less_than","lt","lt"]]) {
    if(t === type && Number.isFinite(Number(ctx[constraint]))) return interpolate(c[key],ctx[constraint]);
  }
  if (/date|time/.test(t)) return c.date;
  if (/float|int_|decimal|finite_number/.test(t)) return c.number;
  return c.invalid;
}
function nativeIssue(control, lang) {
  const c = strings(lang), v = control.validity;
  if (v.valueMissing) return c.required;
  if (v.typeMismatch) return control.type === "email" ? c.email : c.invalid;
  if (v.tooShort) return interpolate(c.short,control.minLength);
  if (v.tooLong) return interpolate(c.long,control.maxLength);
  if (v.rangeUnderflow) return interpolate(c.min,control.min);
  if (v.rangeOverflow) return interpolate(c.max,control.max);
  if (v.badInput) return c.number;
  if (v.stepMismatch) return c.step;
  if (v.customError && control.closest(".entity-select-lookup")) return c.select;
  return c.invalid;
}
function reset(form) {
  const previous = records.get(form);
  previous?.entries.forEach(({control,id}) => {
    if(!control) return;
    control.removeAttribute("aria-invalid");
    const descriptions=(control.getAttribute("aria-describedby")||"").split(/\s+/).filter(x=>x&&x!==id);
    if(descriptions.length)control.setAttribute("aria-describedby",descriptions.join(" "));else control.removeAttribute("aria-describedby");
  });
  form.querySelectorAll("[data-field-error]").forEach(x=>x.remove());
}
function renderEntries(form, entries, lang, focus = true) {
  if(!form?.isConnected) return false;
  reset(form);
  let box=form.querySelector("[data-form-feedback],#formErrors");
  if(!box){box=document.createElement("div");form.append(box);}
  box.dataset.formFeedback="";box.classList.add("form-errors","form-feedback");
  box.setAttribute("role","alert");box.setAttribute("aria-live","assertive");box.tabIndex=-1;
  box.replaceChildren();box.hidden=!entries.length;
  const unique=entries.filter((entry,index)=>entries.findIndex(x=>x.control===entry.control&&x.message===entry.message)===index);
  const record={entries:unique,lang};records.set(form,record);
  if(!unique.length)return true;
  const heading=document.createElement("p");heading.textContent=strings(lang).title;box.append(heading);
  const list=document.createElement("ul");box.append(list);
  unique.forEach(entry=>{
    const li=document.createElement("li");list.append(li);
    if(entry.control){
      const control=entry.control;entry.id=`field-error-${++sequence}`;
      const inline=document.createElement("span");inline.id=entry.id;inline.dataset.fieldError="";inline.className="field-error";inline.textContent=entry.message;
      control.setAttribute("aria-invalid","true");control.setAttribute("aria-describedby",[control.getAttribute("aria-describedby"),entry.id].filter(Boolean).join(" "));
      control.insertAdjacentElement("afterend",inline);
      const link=document.createElement("button");link.type="button";link.className="form-error-link";link.textContent=[label(control),entry.message].filter(Boolean).join(": ");
      link.addEventListener("click",()=>control.focus());li.append(link);
    }else li.textContent=entry.message;
  });
  if(focus)(unique.find(x=>x.control)?.control||box).focus();
  return true;
}
export function renderFormFeedback(form, errors, options = {}) {
  if(!form)return false;
  const lang=options.lang||language();const entries=[];
  for(const error of errors){
    if(typeof error==="string"){entries.push({message:error,control:null});continue;}
    if(error?.control && form.contains(error.control)){entries.push({message:error.message,control:visibleControl(error.control)});continue;}
    if(error?.field){entries.push({message:error.message,control:field(form,[error.field],error.formContext)});continue;}
    if(!error)continue;
    const details=error.details||error.payload?.error?.details||{};
    const issues=details.issues||error.payload?.detail||[];
    const context=error.formContext;
    if(Number(error.status)===422&&changedSinceRequest(context)){
      entries.push({control:null,message:lang==="en"?"This response refers to earlier values. Your current edits were kept. Review them before submitting again.":"Esta respuesta corresponde a valores anteriores. Conservamos tus cambios actuales. Revísalos antes de volver a enviar."});
      handled.add(error);continue;
    }
    if(Array.isArray(issues)&&issues.length){
      for(const issue of issues){
        const location=Array.isArray(issue.loc)?issue.loc:[];
        // Transitional FastAPI ValueErrors are recognized by an exact finite
        // allowlist; diagnostic strings and their arbitrary contents never render.
        const literal=typeof issue.msg==="string"?issue.msg.replace(/^Value error, /,""):"";
        const rule=issue.type==="value_error"&&Object.hasOwn(VALIDATION_RULES,literal)?VALIDATION_RULES[literal]:null;
        const controls=rule?.fields.length?ruleControls(form,rule.fields.map(name=>{
          const prefix=location.filter(x=>x!=="body");
          if(prefix.at(-1)===name)prefix.pop();
          return [...prefix,name].join(".");
        }),context):[field(form,location,context)].filter(Boolean);
        if(rule){
          const message=getLocalizedErrorMessage({name:"ErclaveApiError",code:rule.code,status:422},{lang});
          if(controls.length)controls.forEach(control=>entries.push({control,message}));else entries.push({control:null,message});
          continue;
        }
        const control=controls[0];
        const reference=error.correlationId||error.payload?.error?.correlation_id;
        entries.push({control,message:control?issueMessage(issue,lang):strings(lang).unknown+(reference?` ${strings(lang).reference}: ${reference}.`:"")});
      }
    }else{
      const code=error.code||error.payload?.error?.code;
      const paths=Object.hasOwn(businessFields,code)?businessFields[code]:Object.hasOwn(FORM_BUSINESS_ERRORS,code)?FORM_BUSINESS_ERRORS[code].fields||[]:[];
      const controls=ruleControls(form,paths,context);
      const message=getLocalizedErrorMessage(error,{lang});
      if(controls.length)controls.forEach(control=>entries.push({control,message}));else entries.push({control:null,message});
    }
    handled.add(error);
  }
  return renderEntries(form,entries,lang);
}
export function showFormApiError(error) {
  if(handled.has(error))return true;
  return error?.formContext?.form?.isConnected ? renderFormFeedback(error.formContext.form,[error]) : false;
}
export function installFormFeedback({getLanguage} = {}) {
  if(document.documentElement.dataset.formFeedbackInstalled)return;
  document.documentElement.dataset.formFeedbackInstalled="true";language=getLanguage||language;
  document.addEventListener("click",event=>{activeForm=event.target.closest?.("form")||null;if(activeForm)finishInteraction(activeForm);},true);
  document.addEventListener("submit",event=>{
    activeForm=event.target;
    finishInteraction(activeForm);
    renderEntries(activeForm,[],language(),false);
    const invalid=elements(activeForm).filter(x=>x.willValidate&&!x.validity.valid&&visibleControl(x));
    if(invalid.length){event.preventDefault();event.stopImmediatePropagation();renderEntries(activeForm,invalid.map(control=>({control,message:nativeIssue(control,language())})),language());}
  },true);
  // Invalid does not bubble. Capture all native validation failures, then focus
  // once after the browser has inspected every control in the form.
  const pending=new Set();
  document.addEventListener("invalid",event=>{
    const form=event.target.form;if(!form)return;event.preventDefault();activeForm=form;finishInteraction(form);
    if(pending.has(form))return;pending.add(form);
    queueMicrotask(()=>{pending.delete(form);renderEntries(form,elements(form).filter(x=>x.willValidate&&!x.validity.valid&&visibleControl(x)).map(control=>({control,message:nativeIssue(control,language())})),language());});
  },true);
  for(const eventName of ["input","change"])document.addEventListener(eventName,event=>{
    const form=event.target.form;const record=records.get(form);if(!record)return;
    const remaining=record.entries.filter(x=>x.control!==event.target);
    if(remaining.length!==record.entries.length)renderEntries(form,remaining,record.lang,false);
  });
  window.addEventListener(FORM_REQUEST_EVENT,event=>{
    if(activeForm?.isConnected){
      pendingRequests.set(activeForm,(pendingRequests.get(activeForm)||0)+1);
      event.detail.context={form:activeForm,bindings:{...captureFormBindings(activeForm,event.detail),...activeForm.formFeedbackBindings},values:new Map(elements(activeForm).filter(control=>control.type!=="password"&&control.type!=="file").map(control=>[control,{value:control.value,checked:control.checked}]))};
    }
  });
  window.addEventListener(FORM_ERROR_EVENT,event=>showFormApiError(event.detail));
  window.addEventListener(FORM_COMPLETE_EVENT,event=>{
    const form=event.detail?.form;if(!form)return;
    pendingRequests.set(form,Math.max(0,(pendingRequests.get(form)||0)-1));finishInteraction(form);
  });
}

export function getActiveFeedbackForm() { return activeForm?.isConnected ? activeForm : null; }
