import { findPurchasingDocumentDivisions, findPurchasingDocumentSuppliers, findPurchasingDivisionItems } from '../api/purchasing.js';
import { getLocalizedErrorMessage } from '../i18n/api-errors.js';
import { renderFormFeedback } from './form-feedback.js';

const escape=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const drafts=new WeakMap();
const contexts=new WeakMap();
const copy=lang=>lang==='en'?{division:'Division',society:'Society',currency:'Currency',payment:'Payment terms',lead:'Lead time (days)',search:'Search',previous:'Previous',next:'Next',choose:'Choose',empty:'No eligible results.',legacy:'Historical document without confirmed organizational context. Review its data before creating further operations.',fixed:'The document keeps its original Division and commercial conditions.',supplier:'Supplier in this Division',item:'Item in this Division',pending:'Choose a Division and eligible references before saving.',terms:'Confirmed commercial conditions',unavailable:'No confirmed commercial conditions are available for this selection.'}:{division:'División',society:'Sociedad',currency:'Moneda',payment:'Condiciones de pago',lead:'Plazo de entrega (días)',search:'Buscar',previous:'Anterior',next:'Siguiente',choose:'Seleccionar',empty:'Sin resultados elegibles.',legacy:'Documento histórico sin contexto organizativo confirmado. Revisa sus datos antes de crear nuevas operaciones.',fixed:'El documento conserva su División y condiciones comerciales originales.',supplier:'Proveedor de esta División',item:'Artículo de esta División',pending:'Selecciona una División y referencias elegibles antes de guardar.',terms:'Condiciones comerciales confirmadas',unavailable:'No hay condiciones comerciales confirmadas para esta selección.'};

export function purchasingContextSummary(record,lang='es'){
  const c=copy(lang),context=record?.organization_context,snapshot=record?.commercial_terms_snapshot;
  if(!context)return `<p class="helper-copy" data-purchasing-history>${c.legacy}</p>`;
  return `<p data-purchasing-context>${c.division}: ${escape(context.division_code)} · ${escape(context.division_name)} · ${c.society}: ${escape(context.society_ref_id)}</p>${snapshot?.values?`<p data-purchasing-terms>${c.currency}: ${escape(snapshot.values.currency)} · ${c.payment}: ${escape(snapshot.values.payment_terms)} · ${c.lead}: ${escape(snapshot.values.lead_time_days)}</p>`:''}`;
}

function guard(form,state,lang){
  state.failures=new Set();
  contexts.set(form,state);
  form.addEventListener('submit',event=>{
    for(const root of state.failures)if(!root.isConnected)state.failures.delete(root);
    if(state.busy||state.pending>0||state.failures.size||!state.valid()){
      event.preventDefault();event.stopImmediatePropagation();
      if(!state.busy)renderFormFeedback(form,[copy(lang).pending],{lang});
    }
  },true);
}

/** Search is bounded by the owning service. Old responses cannot change a new context. */
function lookup(root,{name,label,lang,load,pick,initial=null,state}){
  const c=copy(lang);
  root.innerHTML=`<span>${escape(label)}</span><input type="search" data-purchasing-query maxlength="240" aria-label="${escape(c.search+' '+label)}"><div class="commercial-assignment-actions"><button type="button" data-purchasing-search>${c.search}</button><button type="button" data-purchasing-prev>${c.previous}</button><button type="button" data-purchasing-next>${c.next}</button></div><select name="${escape(name)}" required><option value="">${c.choose}</option></select><small role="status" data-purchasing-lookup-status></small>`;
  const select=root.querySelector('select'),query=root.querySelector('input'),status=root.querySelector('[role=status]');
  let offset=0,total=0,version=0,selected=initial,rows=[];
  if(initial){select.add(new Option(`${initial.code||''} · ${initial.name||initial.id}`,initial.id));select.value=initial.id;}
  function buttons(){root.querySelector('[data-purchasing-prev]').disabled=offset===0;root.querySelector('[data-purchasing-next]').disabled=offset+20>=total;}
  async function search(){
    const request=++version;state.pending++;select.disabled=true;status.textContent='';
    try{
      const result=await load(query.value.trim(),offset);
      if(request!==version||!root.isConnected)return;
      state.failures.delete(root);
      rows=result.data||[];total=result.meta?.total||0;
      select.replaceChildren(new Option(c.choose,''));
      if(selected&&!rows.some(row=>row.id===selected.id))select.add(new Option(`${selected.code||''} · ${selected.name||selected.id}`,selected.id));
      rows.forEach(row=>select.add(new Option(`${row.code} · ${row.name}`,row.id)));
      select.value=selected?.id||'';status.textContent=rows.length?'':c.empty;status.setAttribute('role','status');buttons();
    }catch(error){if(request===version&&root.isConnected){state.failures.add(root);status.textContent=getLocalizedErrorMessage(error,{lang});status.setAttribute('role','alert');}}
    finally{state.pending--;if(request===version&&root.isConnected)select.disabled=false;}
  }
  select.addEventListener('change',()=>{selected=rows.find(row=>row.id===select.value)||(selected?.id===select.value?selected:null);pick(selected);});
  root.querySelector('[data-purchasing-search]').onclick=()=>{offset=0;search();};
  query.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();offset=0;search();}};
  root.querySelector('[data-purchasing-prev]').onclick=()=>{offset=Math.max(0,offset-20);search();};
  root.querySelector('[data-purchasing-next]').onclick=()=>{offset+=20;search();};buttons();
  return {search,clear(){state.failures.delete(root);version++;offset=0;selected=null;rows=[];query.value='';select.replaceChildren(new Option(c.choose,''));select.disabled=false;status.textContent='';buttons();},selected:()=>selected};
}

export function mountPurchasingRequisitionContext(form,{record=null,lang='es',items=[],onItem=()=>{}}={}){
  if(!form)return;
  const c=copy(lang),frozen=record?.organization_context;
  let division=frozen?{id:frozen.division_ref_id,code:frozen.division_code,name:frozen.division_name,society_id:frozen.society_ref_id,cost_currency:frozen.cost_currency}:null;
  const state={busy:false,pending:0,valid:()=>Boolean(division)&&(!record||Boolean(frozen))};guard(form,state,lang);
  const panel=document.createElement('div');panel.className='preview-field wide-field';panel.dataset.purchasingDivision='';form.prepend(panel);
  const summary=document.createElement('p');summary.dataset.purchasingSociety='';panel.after(summary);
  const lineLookups=new Map();
  const display=()=>{summary.textContent=division?`${c.society}: ${division.society_id} · ${c.currency}: ${division.cost_currency||''}`:record?c.legacy:c.pending;};
  function refreshItems(clear=false){
    for(const row of form.querySelectorAll('[data-requisition-line]')){
      if(row.querySelector('[name=line_type]')?.value==='service')continue;
      const select=row.querySelector('select[name=inventory_item_id]');if(!select)continue;
      let current=lineLookups.get(select);
      if(!current){
        const original=items.find(item=>item.id===select.value),host=select.closest('label');
        current=lookup(host,{name:'inventory_item_id',label:c.item,lang,state,initial:original||null,load:(q,offset)=>division?findPurchasingDivisionItems(division.id,q,offset):Promise.resolve({data:[],meta:{total:0}}),pick:item=>{if(item)onItem(item);}});
        lineLookups.set(host.querySelector('select'),current);
      }
      if(clear)current.clear();if(division)current.search();
    }
  }
  if(record){
    panel.innerHTML=`<span>${c.division}</span><input name="division_ref_id" readonly value="${escape(division?.id||'')}"><small>${escape(division?division.code+' · '+division.name:c.legacy)}</small>`;
    if(!frozen)form.querySelector('[type=submit]')?.setAttribute('disabled','');
  }else{
    const choice=lookup(panel,{name:'division_ref_id',label:c.division,lang,state,load:findPurchasingDocumentDivisions,pick:value=>{division=value;display();refreshItems(true);}});choice.search();
  }
  display();refreshItems();
  const lineContainer=form.querySelector('#purchasingRequisitionLines');
  if(lineContainer){
    const observer=new MutationObserver(()=>{if(!form.isConnected){observer.disconnect();return;}refreshItems();});
    // Observe row additions/removals only; lookup options do not trigger a refresh loop.
    observer.observe(lineContainer,{childList:true});
  }
}

export function mountPurchasingOrderContext(form,{record=null,requisitions=[],lang='es'}={}){
  if(!form)return;
  const c=copy(lang),requisition=form.elements.requisition_id;
  const source=()=>requisitions.find(row=>row.id===(requisition?.value||record?.requisition_id));
  let context=record?.organization_context||source()?.organization_context,selected=null;
  const state={busy:false,pending:0,termsRevision:()=>selected?.commercial_terms?.revision,valid:()=>Boolean(context&&selected?.commercial_terms?.values&&!selected.commercial_terms.requires_confirmation)};guard(form,state,lang);
  const summary=document.createElement('div');summary.className='wide-field';summary.dataset.purchasingOrderContext='';form.prepend(summary);
  const terms=document.createElement('div');terms.className='wide-field';terms.dataset.purchasingOrderTerms='';form.querySelector('.inline-actions')?.before(terms);
  function display(){
    summary.innerHTML=purchasingContextSummary({organization_context:context},lang);
    const values=selected?.commercial_terms?.requires_confirmation?null:selected?.commercial_terms?.values;
    terms.innerHTML=values?`<strong>${c.terms}</strong><p>${c.currency}: ${escape(values.currency)} · ${c.payment}: ${escape(values.payment_terms)} · ${c.lead}: ${escape(values.lead_time_days)}</p>`:`<p>${c.unavailable}</p>`;
  }
  if(record?.commercial_terms_snapshot&&record.organization_context){selected={id:record.supplier_id,code:'',name:record.supplier_name_snapshot,commercial_terms:{values:record.commercial_terms_snapshot.values,revision:record.commercial_terms_snapshot.terms_revision}};}
  const host=form.elements.supplier_id.closest('label');
  const supplier=lookup(host,{name:'supplier_id',label:c.supplier,lang,state,initial:selected,load:(q,offset)=>context?findPurchasingDocumentSuppliers(context.division_ref_id,q,offset):Promise.resolve({data:[],meta:{total:0}}),pick:value=>{selected=value?.id===record?.supplier_id&&record.commercial_terms_snapshot?{...value,commercial_terms:{values:record.commercial_terms_snapshot.values,revision:record.commercial_terms_snapshot.terms_revision}}:value;display();}});
  requisition?.addEventListener('change',()=>{context=source()?.organization_context;selected=null;supplier.clear();display();if(context)supplier.search();});
  display();if(context)supplier.search();
  if(record&&!record.organization_context)form.querySelector('[type=submit]')?.setAttribute('disabled','');
}

/** One in-flight command and one key per exact draft; rejected capture is retained. */
export function purchasingOrderTermsRevision(form){return contexts.get(form)?.termsRevision?.();}
export function purchasingDraftCommand(form,payload){
  const state=contexts.get(form);if(state&&(state.busy||state.pending||state.failures.size||!state.valid()))return null;
  const fingerprint=JSON.stringify(payload);let command=drafts.get(form);
  if(!command||command.fingerprint!==fingerprint){command={fingerprint,key:`purchasing-${crypto.randomUUID()}`};drafts.set(form,command);}
  if(state)state.busy=true;const submit=form.querySelector('[type=submit]');if(submit)submit.disabled=true;
  return {...command,finish(){if(state)state.busy=false;if(form.isConnected&&submit)submit.disabled=false;}};
}
