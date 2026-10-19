import {findMaintenanceDivisions,findMaintenanceWorkers,getMaintenanceMachineDivision,transitionMaintenanceOrder,createMaintenanceTime} from '../api/maintenance.js';
import {getLocalizedErrorMessage} from '../i18n/api-errors.js';
import {renderFormFeedback,showFormApiError} from './form-feedback.js';
const states=new WeakMap(),commands=new WeakMap();
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const copy=lang=>lang==='en'?{division:'Division',society:'Society',currency:'Currency',search:'Search',choose:'Choose',previous:'Previous',next:'Next',worker:'Eligible technician',rate:'Confirmed hourly rate',pending:'Confirm the organizational context and eligible references before continuing.',legacy:'Historical order without confirmed organizational context. Review its data before further operations.',unavailable:'No confirmed rate is available for this technician in the order Division.'}:{division:'División',society:'Sociedad',currency:'Moneda',search:'Buscar',choose:'Seleccionar',previous:'Anterior',next:'Siguiente',worker:'Técnico elegible',rate:'Tarifa por hora confirmada',pending:'Confirma el contexto organizativo y las referencias elegibles antes de continuar.',legacy:'Orden histórica sin contexto organizativo confirmado. Revisa sus datos antes de nuevas operaciones.',unavailable:'No hay tarifa confirmada para este técnico en la División de la orden.'};
export function maintenanceContextSummary(order,lang='es'){
 const c=copy(lang),x=order?.organization_context;
 const times=(order?.time_entries||[]).map(entry=>entry.labor_cost_snapshot).filter(Boolean);
 return x?`<p data-maintenance-context>${c.division}: ${esc(x.division_code||x.division_ref_id)} · ${esc(x.division_name||'')} · ${c.society}: ${esc(x.society_ref_id||'')} · ${c.currency}: ${esc(x.cost_currency||'')}</p>${times.map(rate=>`<p data-maintenance-time-snapshot>${c.rate}: ${esc(rate.hourly_cost)} ${esc(rate.currency)} · ${lang==='en'?'Recorded labor cost':'Costo de mano de obra registrado'}: ${esc(rate.labor_cost)} ${esc(rate.currency)}</p>`).join('')}`:`<p data-maintenance-history>${c.legacy}</p>`;
}
function stateFor(form,lang,valid){const state={pending:0,failed:new Set(),busy:false,valid};states.set(form,state);form.addEventListener('submit',event=>{if(state.pending||state.failed.size||state.busy||!state.valid()){event.preventDefault();event.stopImmediatePropagation();if(!state.busy)renderFormFeedback(form,[copy(lang).pending],{lang});}},true);return state;}
function lookup(root,{name,label,lang,state,load,pick,initial=null}){
 const c=copy(lang);root.classList.add('maintenance-context-lookup');root.innerHTML=`<span>${esc(label)}</span><input type="search" data-maintenance-query maxlength="240" aria-label="${esc(c.search+' '+label)}"><div class="maintenance-lookup-actions"><button type="button" data-search>${c.search}</button><button type="button" data-prev>${c.previous}</button><button type="button" data-next>${c.next}</button></div><select name="${esc(name)}" required><option value="">${c.choose}</option></select><small role="status"></small>`;
 const select=root.querySelector('select'),query=root.querySelector('input'),status=root.querySelector('small');let version=0,offset=0,total=0,rows=[],selected=initial;
 const labelFor=row=>`${row.code||row.employee_number||''} · ${row.name||row.full_name||row.id}`;
 if(initial){select.add(new Option(labelFor(initial),initial.id));select.value=initial.id;}
 function buttons(){root.querySelector('[data-prev]').disabled=offset===0;root.querySelector('[data-next]').disabled=offset+20>=total;}
 async function search(){const request=++version;state.pending++;select.disabled=true;try{const result=await load(query.value.trim(),offset);if(request!==version||!root.isConnected)return;state.failed.delete(root);rows=result.data||[];total=result.meta?.total||0;select.replaceChildren(new Option(c.choose,''));if(selected&&!rows.some(row=>row.id===selected.id))select.add(new Option(labelFor(selected),selected.id));rows.forEach(row=>select.add(new Option(labelFor(row),row.id)));select.value=selected?.id||'';status.textContent='';status.setAttribute('role','status');buttons();}catch(error){if(request===version&&root.isConnected){state.failed.add(root);status.textContent=getLocalizedErrorMessage(error,{lang});status.setAttribute('role','alert');}}finally{state.pending--;if(request===version&&root.isConnected)select.disabled=root.hidden;}}
 select.onchange=()=>{selected=rows.find(row=>row.id===select.value)||(selected?.id===select.value?selected:null);pick(selected);};
 root.querySelector('[data-search]').onclick=()=>{offset=0;search();};query.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();offset=0;search();}};root.querySelector('[data-prev]').onclick=()=>{offset=Math.max(0,offset-20);search();};root.querySelector('[data-next]').onclick=()=>{offset+=20;search();};buttons();
 return {search,select,clear(){version++;state.failed.delete(root);offset=0;selected=null;rows=[];select.replaceChildren(new Option(c.choose,''));select.disabled=false;query.value='';status.textContent='';buttons();}};
}
export function maintenanceCommand(form,payload,kind='command'){
 const state=states.get(form);if(state&&(state.pending||state.failed.size||state.busy||!state.valid()))return null;
 let entries=commands.get(form);if(!entries){entries=new Map();commands.set(form,entries);}const signature=JSON.stringify(payload);let command=entries.get(kind);if(!command||command.signature!==signature){command={signature,key:`maintenance-${crypto.randomUUID()}`};entries.set(kind,command);}if(state)state.busy=true;const submit=form.querySelector('[type=submit]');if(submit)submit.disabled=true;return {...command,finish(){if(state)state.busy=false;if(form.isConnected&&submit)submit.disabled=false;}};
}
export function mountMaintenanceOrderContext(form,{lang='es',orders=[],scope}={}){
 if(!form)return;const c=copy(lang);let division=null,derived=null,version=0;
 const state=stateFor(form,lang,()=>Boolean(derived||division));const panel=document.createElement('label');panel.className='preview-field wide-field';form.prepend(panel);const summary=document.createElement('div');summary.className='wide-field';panel.after(summary);
 const choice=lookup(panel,{name:'division_ref_id',label:c.division,lang,state,load:findMaintenanceDivisions,pick:value=>{division=value;summary.innerHTML=value?maintenanceContextSummary({organization_context:{division_ref_id:value.id,division_code:value.code,division_name:value.name,society_ref_id:value.society_id,cost_currency:value.cost_currency}},lang):'';}});choice.search();
 async function refresh(){const request=++version,source=orders.find(row=>row.id===form.elements.source_production_order_id.value),machine=form.elements.production_machine_id.value;derived=null;const inherited=Boolean(source||machine);panel.hidden=inherited;choice.select.disabled=inherited;choice.select.required=!inherited;
  if(source){form.elements.target_type.value='production_machine';const resource=source.resources?.find(row=>row.resource_type==='machine');if(resource)form.elements.production_machine_id.value=resource.resource_ref_id;derived=source.organization_context;summary.innerHTML=maintenanceContextSummary(source,lang);return;}
  if(!machine){summary.innerHTML=division?maintenanceContextSummary({organization_context:{division_ref_id:division.id,division_name:division.name,society_ref_id:division.society_id,cost_currency:division.cost_currency}},lang):'';return;}
  state.pending++;try{const assignment=await getMaintenanceMachineDivision(machine);if(request!==version||!form.isConnected)return;state.failed.delete(summary);const row=scope?.divisions?.find(value=>value.id===assignment.division_ref_id);derived=assignment.division_ref_id?{division_ref_id:assignment.division_ref_id,division_code:row?.code,division_name:row?.name,society_ref_id:row?.society_id}:null;summary.innerHTML=maintenanceContextSummary({organization_context:derived},lang);}catch(error){if(request===version){state.failed.add(summary);summary.textContent=getLocalizedErrorMessage(error,{lang});}}finally{state.pending--;}
 }
 form.addEventListener('change',event=>{if(['source_production_order_id','production_machine_id'].includes(event.target.name)){state.failed.delete(summary);refresh();}});refresh();
}
function rateMarkup(row,lang){const c=copy(lang);return row?`<p data-maintenance-rate>${c.rate}: ${esc(row.hourly_cost)} ${esc(row.hourly_cost_currency_code)} · ${esc(row.position_name)}</p>`:`<p data-maintenance-rate>${c.unavailable}</p>`;}
export function mountMaintenanceTimeContext(form,{lang='es',order=null,orders=[]}={}){
 if(!form)return;const c=copy(lang),orderControl=form.elements.order_id;let current=order||orders.find(row=>row.id===orderControl?.value),worker=null,version=0;
 const state=stateFor(form,lang,()=>Boolean(current?.organization_context&&worker?.position_assignment_revision));state.rateRevision=()=>worker?.position_assignment_revision;
 const panel=document.createElement('div');panel.className='wide-field maintenance-time-context';const actions=form.querySelector('.modal-actions');if(actions)actions.before(panel);else form.prepend(panel);
 const host=document.createElement('label');host.className='preview-field';const display=document.createElement('div');panel.append(display);
 const old=form.elements.worker_id;let choice;
 if(old){old.closest('label').replaceWith(host);choice=lookup(host,{name:'worker_id',label:c.worker,lang,state,load:(q,offset)=>current?.organization_context?findMaintenanceWorkers(current.organization_context.division_ref_id,q,offset):Promise.resolve({data:[],meta:{total:0}}),pick:row=>{worker=row;display.innerHTML=maintenanceContextSummary(current,lang)+rateMarkup(worker,lang);}});}
 async function refresh(){const request=++version;worker=null;current=order||orders.find(row=>row.id===orderControl?.value);display.innerHTML=maintenanceContextSummary(current,lang)+rateMarkup(null,lang);if(choice){choice.clear();if(current?.organization_context)choice.search();return;}if(!current?.organization_context||!current.assigned_worker_id)return;
  state.pending++;try{const result=await findMaintenanceWorkers(current.organization_context.division_ref_id,'',0,current.assigned_worker_id);if(request!==version||!form.isConnected)return;state.failed.delete(panel);worker=(result.data||[]).find(row=>row.id===current.assigned_worker_id)||null;display.innerHTML=maintenanceContextSummary(current,lang)+rateMarkup(worker,lang);}catch(error){if(request===version){state.failed.add(panel);display.textContent=getLocalizedErrorMessage(error,{lang});}}finally{state.pending--;}
 }
 orderControl?.addEventListener('change',refresh);refresh();
}
export function maintenanceTimeRevision(form){return states.get(form)?.rateRevision?.();}
export async function saveMaintenanceTime(form,id,payload){
 const capture={...payload,expected_position_assignment_revision:maintenanceTimeRevision(form)},command=maintenanceCommand(form,capture,'time');
 if(!command)throw Object.assign(new Error('Maintenance context pending'),{code:'maintenance_document_context_required'});
 try{return await createMaintenanceTime(id,capture,command.key);}finally{command.finish();}
}
export function mountMaintenanceMaterials(form,{orders,warehouses,lang='es'}){
 if(!form)return;const select=form.elements.warehouse_id,summary=document.createElement('div');summary.className='wide-field';form.prepend(summary);
 const state=stateFor(form,lang,()=>Boolean(orders.find(row=>row.id===form.elements.order_id.value)?.organization_context));
 const update=()=>{const order=orders.find(row=>row.id===form.elements.order_id.value),selected=select.value;select.replaceChildren(new Option(copy(lang).choose,''));warehouses.filter(row=>order?.organization_context&&row.division_ref_id===order.organization_context.division_ref_id).forEach(row=>select.add(new Option(`${row.code} · ${row.name}`,row.id)));select.value=[...select.options].some(option=>option.value===selected)?selected:'';summary.innerHTML=maintenanceContextSummary(order,lang);};form.elements.order_id.addEventListener('change',update);update();return state;
}
export function mountMaintenanceAssignments(root,{orders,lang='es',onSaved=()=>{}}){
 for(const order of orders){const select=root.querySelector(`[data-maintenance-worker-for="${CSS.escape(order.id)}"]`),button=root.querySelector(`[data-maintenance-transition="assign"][data-order-id="${CSS.escape(order.id)}"]`);if(!select||!button)continue;
  const form=document.createElement('form');form.className='maintenance-assignment-form';form.id=`maintenance-assignment-${order.id}`;const host=select.closest('label');host.before(form);form.append(host,button);button.removeAttribute('data-maintenance-transition');button.type='submit';let worker=null;const state=stateFor(form,lang,()=>Boolean(order.organization_context&&worker));
  const choice=lookup(host,{name:'assigned_worker_id',label:copy(lang).worker,lang,state,load:(q,offset)=>findMaintenanceWorkers(order.organization_context.division_ref_id,q,offset),pick:row=>worker=row});if(order.organization_context)choice.search();else button.disabled=true;
  form.addEventListener('submit',async event=>{event.preventDefault();const payload={assigned_worker_id:worker.id},command=maintenanceCommand(form,payload);if(!command)return;state.busy=true;button.disabled=true;try{await transitionMaintenanceOrder(order.id,'assign',payload,command.key);await onSaved();}catch(error){if(!showFormApiError(error))renderFormFeedback(form,[getLocalizedErrorMessage(error,{lang})],{lang});}finally{command.finish();}});
 }
}
