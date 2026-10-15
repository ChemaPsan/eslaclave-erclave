import { findStockOptions, configureSalesOrderFulfillment } from "../api/sales.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape=value=>String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));

export function mountScopedStockFulfillment(container,order,{lang="es",onSaved,onError}={}){
 const en=lang==="en",lines=(order.fields?.lines||[]).filter(line=>line.productServiceType==="product"&&line.fulfillmentMode==="pending"),currency=order.fields?.currency;
 if(!lines.length)return;
 const form=document.createElement("form");form.className="recipe-form";form.dataset.scopedStock="";form.dataset.form="scoped-stock-fulfillment";
 form.innerHTML=`<h3>${en?"Supply from stock in this Division":"Surtir desde existencias de esta División"}</h3><p>${en?"Stock costs keep their original currency. Choose stock or manufacturing for each pending line.":"Los costos de existencias conservan su moneda original. Elige existencias o fabricación para cada partida pendiente."}</p>${lines.map((line,index)=>`<fieldset data-stock-line="${index}"><legend>${escape(line.productServiceName)} · ${escape(line.quantity-line.deliveredQuantity)} ${escape(line.unit)}</legend><p data-item-label></p><label class="preview-field"><span>${en?"Find warehouse":"Buscar almacén"}</span><input type="search" maxlength="240" data-stock-query></label><div class="commercial-assignment-actions"><button type="button" data-find>${en?"Search":"Buscar"}</button><button type="button" data-prev disabled>${en?"Previous":"Anterior"}</button><button type="button" data-next disabled>${en?"Next":"Siguiente"}</button></div><label class="preview-field"><span>${en?"Warehouse in this Division":"Almacén de esta División"}</span><select name="lines[${index}].allocations[0].warehouse_id" required><option value="">${en?"Choose":"Seleccionar"}</option></select></label><p role="status" data-lookup-status></p></fieldset>`).join("")}<p data-cost-currency></p><label class="preview-field" data-rate-field hidden><span data-rate-label></span><input name="cost_exchange_rate" type="number" min="0.000000000001" step="0.000000000001" inputmode="decimal"></label><div role="alert" data-stock-error></div><button type="submit" class="primary-action" disabled>${en?"Reserve stock":"Reservar existencias"}</button>`;
 container.append(form);const items=new Map();let key=null,fingerprint=null,busy=false;
 const submit=form.querySelector('[type=submit]'),rate=form.elements.cost_exchange_rate;
 function ready(){
  const currencies=new Set(Array.from(items.values(),row=>row.cost_currency));
  const loaded=items.size===lines.length&&currencies.size===1,original=loaded?[...currencies][0]:null;
  submit.disabled=busy||!loaded;form.querySelector('[data-cost-currency]').textContent=original?`${en?"Inventory cost currency":"Moneda del costo de Inventarios"}: ${original}. ${en?"Order currency":"Moneda del pedido"}: ${currency}.`:"";
  const different=Boolean(original&&original!==currency);form.querySelector('[data-rate-field]').hidden=!different;rate.required=different;rate.disabled=!different||busy;
  form.querySelector('[data-rate-label]').textContent=`${en?"Exchange rate":"Tipo de cambio"}: 1 ${original||""} = … ${currency||""}`;
 }
 lines.forEach((line,index)=>{
  const panel=form.querySelector(`[data-stock-line="${index}"]`),select=panel.querySelector('select'),status=panel.querySelector('[data-lookup-status]');let offset=0,q="",loading=false,hasMore=false;
  function controls(){panel.querySelectorAll('button,input').forEach(node=>node.disabled=loading||busy);panel.querySelector('[data-prev]').disabled=loading||busy||offset===0;panel.querySelector('[data-next]').disabled=loading||busy||!hasMore;}
  async function search(){if(loading||busy)return;loading=true;controls();status.textContent="";try{
   const result=await findStockOptions(order.id,line.id,q,offset);if(!form.isConnected)return;
   const selected=select.value,old=Array.from(select.options).find(option=>option.value===selected);
   select.replaceChildren(new Option(en?"Choose":"Seleccionar",""));if(old&&selected&&!result.warehouses.some(row=>row.warehouse_id===selected))select.add(new Option(old.textContent,selected));
   result.warehouses.forEach(row=>select.add(new Option(`${row.warehouse_code} · ${row.warehouse_name} · ${en?"Available":"Disponible"}: ${row.available_quantity} ${result.unit}`,row.warehouse_id)));
   select.value=selected;items.set(line.id,result);hasMore=result.has_more;
   panel.querySelector('[data-item-label]').textContent=`${result.item_code} · ${result.item_name}`;status.setAttribute('role','status');if(!result.warehouses.length)status.textContent=en?"No eligible warehouses found.":"No hay almacenes disponibles.";ready();
  }catch(error){if(form.isConnected){status.setAttribute('role','alert');status.textContent=getLocalizedErrorMessage(error,{lang});}}finally{loading=false;controls();}}
  panel.querySelector('[data-find]').onclick=()=>{q=panel.querySelector('input').value.trim();offset=0;search();};panel.querySelector('input').onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();panel.querySelector('[data-find]').click();}};
  panel.querySelector('[data-prev]').onclick=()=>{offset=Math.max(0,offset-20);search();};panel.querySelector('[data-next]').onclick=()=>{offset+=20;search();};search();
 });
 form.onsubmit=async event=>{event.preventDefault();if(busy||submit.disabled||!form.reportValidity())return;
  const payload={lines:lines.map((line,index)=>({order_line_id:line.id,mode:"stock",allocations:[{inventory_item_id:items.get(line.id).inventory_item_id,warehouse_id:form.elements[`lines[${index}].allocations[0].warehouse_id`].value,quantity:String(line.quantity-line.deliveredQuantity)}]}))};
  if(rate.required)payload.cost_exchange_rate=rate.value;
  const capture=JSON.stringify(payload);if(capture!==fingerprint){fingerprint=capture;key=`stock-${crypto.randomUUID()}`;}
  busy=true;const states=Array.from(form.elements,control=>[control,control.disabled]);states.forEach(([control])=>control.disabled=true);form.querySelector('[data-stock-error]').textContent="";
  try{await configureSalesOrderFulfillment(order.id,payload,key);if(form.isConnected)await onSaved?.();}catch(error){if(form.isConnected){form.querySelector('[data-stock-error]').textContent=getLocalizedErrorMessage(error,{lang});states.forEach(([control,disabled])=>control.disabled=disabled);renderFormFeedback(form,[error],{lang});}}finally{busy=false;states.forEach(([control,disabled])=>control.disabled=disabled);ready();}
 };
}
