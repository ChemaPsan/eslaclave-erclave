import { findServiceWorkers } from "../api/sales.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
export function mountServiceWorkerLookup(select,id,lang="es"){
 if(!select)return;
 select.removeAttribute("data-entity-selector");
 const en=lang==="en",panel=document.createElement("div");panel.className="wide-field commercial-assignment-actions";
 panel.innerHTML=`<label class="preview-field"><span>${en?"Find workers in this Division":"Buscar trabajadores en esta División"}</span><input type="search" maxlength="240" data-worker-query></label><button type="button" data-worker-find>${en?"Search":"Buscar"}</button><button type="button" data-worker-prev>${en?"Previous":"Anterior"}</button><button type="button" data-worker-next>${en?"Next":"Siguiente"}</button><p role="status" data-worker-feedback></p>`;
 select.closest("label").before(panel);let offset=0,q="",busy=false,hasMore=false;
 const controls=()=>{panel.querySelectorAll('button,input').forEach(n=>n.disabled=busy);panel.querySelector('[data-worker-prev]').disabled=busy||offset===0;panel.querySelector('[data-worker-next]').disabled=busy||!hasMore;};
 async function search(){if(busy)return;busy=true;controls();const message=panel.querySelector('[data-worker-feedback]');message.textContent="";try{
  const result=await findServiceWorkers(id,q,offset);if(!panel.isConnected)return;
  const selected=select.value,old=Array.from(select.options).find(n=>n.value===selected);
  select.replaceChildren(new Option(en?"Choose":"Seleccionar",""));
  if(old&&selected&&!result.data.some(row=>row.id===selected))select.add(new Option(old.textContent,selected));
  result.data.forEach(row=>select.add(new Option(`${row.employee_number} · ${row.full_name} · ${row.position_name}`,row.id)));
  select.value=selected;hasMore=result.has_more;
  message.setAttribute('role','status');if(!result.data.length)message.textContent=en?"No eligible workers found.":"No hay trabajadores disponibles.";
 }catch(error){if(panel.isConnected){message.setAttribute('role','alert');message.textContent=getLocalizedErrorMessage(error,{lang});}}finally{busy=false;controls();}}
 panel.querySelector('[data-worker-find]').onclick=()=>{q=panel.querySelector('input').value.trim();offset=0;search();};
 panel.querySelector('input').onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();panel.querySelector('[data-worker-find]').click();}};
 panel.querySelector('[data-worker-prev]').onclick=()=>{offset=Math.max(0,offset-20);search();};panel.querySelector('[data-worker-next]').onclick=()=>{offset+=20;search();};search();
}
