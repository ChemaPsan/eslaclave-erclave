import { readQuoteContext,findQuoteDivisions,saveQuoteContext } from "../api/quote-context.js";
import { quoteContextCopy } from "../i18n/quote-context.js";
import { renderFormFeedback } from "./form-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
const escape=value=>String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
export async function mountQuoteContext(root,id,session,lang="es",close=()=>{},changed=()=>{}){
 const c=quoteContextCopy[lang==="en"?"en":"es"],editable=session.permissions?.includes("sales.quote.update");
 root.innerHTML=`<section class="commercial-organization-panel"><h2>${c.title}</h2><p>${c.hint}</p><p>${c.fixed}</p><p>${c.downstream}</p><div data-quote-snapshot></div><form data-form="quote-context"><div data-quote-search></div><p data-quote-division>${c.pending}</p><label class="preview-field"><span>${c.costRate}</span><input name="cost_exchange_rate" type="number" min="0.000000000001" step="any" inputmode="decimal" aria-describedby="quoteCostRateHelp"><small id="quoteCostRateHelp">${c.costRateHelp}</small></label>${editable?`<button type="submit" class="primary-action">${c.save}</button>`:""}</form><p data-quote-message role="status"></p><div class="commercial-assignment-actions"><button type="button" class="secondary-action" data-quote-reload>${c.reload}</button><button type="button" class="secondary-action" data-quote-close>${c.close}</button></div></section>`;
 const panel=root.firstElementChild,form=panel.querySelector("form"),lookup=panel.querySelector("[data-quote-search]"),message=panel.querySelector("[data-quote-message]");
 let quote=null,division=null,busy=false,key,fingerprint,offset=0,q="";
 const costCurrency=()=>session.scope?.societies?.find(row=>row.id===(division?.society_id||quote?.society_ref_id))?.base_currency||quote?.estimated_cost_snapshot?.cost_currency||null;
 const rateInput=form.querySelector('[name=cost_exchange_rate]');
 const syncRate=()=>{const same=costCurrency()&&costCurrency()===quote?.currency;rateInput.value=same?"1":division?.id===quote?.division_ref_id?quote?.estimated_cost_snapshot?.cost_exchange_rate??"":"";rateInput.closest("label").querySelector("small").textContent=same?c.sameCurrencyRate:c.costRateHelp;};
 const controls=()=>{panel.querySelectorAll("button,input").forEach(node=>{node.disabled=busy||node.hasAttribute("data-unavailable")||node===rateInput&&(!editable||quote?.status!=="draft");});form.querySelector('[type=submit]')?.toggleAttribute('disabled',busy||!quote||quote.status!=="draft");};
 const error=value=>{message.textContent=getLocalizedErrorMessage(value,{lang});message.setAttribute("role","alert");};
 function display(){
  const snapshot=quote.commercial_terms_snapshot,v=snapshot?.values;
  const estimate=quote.estimated_cost_snapshot;
  panel.querySelector("[data-quote-snapshot]").innerHTML=`<strong>${escape(quote.code)}</strong>${v?`<p>${c.division}: ${escape(snapshot.division.code)} &middot; ${escape(snapshot.division.name)}</p><p>${c.society}: ${escape(quote.society_ref_id)}</p><p>${c.currency}: ${escape(v.currency)} &middot; ${c.payment}: ${escape(v.payment_terms)}</p><p>${c.credit}: ${escape(v.credit_limit)} &middot; ${c.revision}: ${escape(snapshot.terms_revision)}</p>`:`<p>${c.pending}</p>`}<p>${c.estimatedCost}: ${quote.estimated_cost==null?c.estimatePending:`${escape(quote.estimated_cost)} ${escape(quote.currency)}${quote.division_ref_id&&!estimate?` (${c.estimateHistorical})`:""}`}</p><p>${c.costCurrency}: ${escape(estimate?.cost_currency||costCurrency()||c.estimatePending)} &middot; ${c.costRate}: ${escape(estimate?.cost_exchange_rate??c.estimatePending)}</p>`;
  panel.querySelector("[data-quote-division]").textContent=division?`${c.division}: ${division.code} · ${division.name}`:c.pending;
 }
 async function search(){
  busy=true;controls();try{const result=await findQuoteDivisions(q,offset);if(!panel.isConnected)return;
   lookup.innerHTML=`<label><span>${c.division}</span><input name="division_ref_id" type="search" value="${escape(q)}" maxlength="240"></label><button type="button" class="secondary-action" data-search>${c.find}</button><div data-results>${result.data.map((row,i)=>`<button type="button" class="secondary-action" data-pick="${i}">${escape(row.code)} · ${escape(row.name)}</button>`).join("")||c.empty}</div><div class="commercial-assignment-actions"><button type="button" data-prev ${offset===0?'data-unavailable':''}>${c.previous}</button><button type="button" data-next ${offset+20>=result.meta.total?'data-unavailable':''}>${c.next}</button></div>`;
   lookup.querySelector('[data-search]').onclick=()=>{q=lookup.querySelector('input').value.trim();offset=0;search();};lookup.querySelector('input').onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();lookup.querySelector('[data-search]').click();}};
   lookup.querySelector('[data-prev]').onclick=()=>{offset=Math.max(0,offset-20);search();};lookup.querySelector('[data-next]').onclick=()=>{offset+=20;search();};
   lookup.querySelectorAll('[data-pick]').forEach(button=>{button.onclick=()=>{division=result.data[Number(button.dataset.pick)];key=null;fingerprint=null;renderFormFeedback(form,[],{lang});syncRate();display();};});
  }catch(value){error(value);}finally{busy=false;controls();}
 }
 async function load(){busy=true;controls();try{const result=await readQuoteContext(id);if(!panel.isConnected)return;quote=result;division=quote.commercial_terms_snapshot?.division||null;key=null;fingerprint=null;lookup.replaceChildren();renderFormFeedback(form,[],{lang});syncRate();display();if(editable&&quote.status==='draft'&&!quote.division_ref_id)await search();}catch(value){error(value);}finally{busy=false;controls();}}
 form.onsubmit=async event=>{event.preventDefault();if(busy||!editable||quote?.status!=='draft')return;if(!division){renderFormFeedback(form,[c.choose],{lang});return;}
  const rateText=rateInput.value.trim();const rate=rateText?Number(rateText):null;
  if(rateText&&(!Number.isFinite(rate)||rate<=0||costCurrency()===quote.currency&&rate!==1)){renderFormFeedback(form,[{field:"cost_exchange_rate",message:c.invalidCostRate}],{lang});return;}
  const payload={division_ref_id:division.id,expected_revision:quote.organization_revision,...(rateText?{cost_exchange_rate:rateText}:{})},serialized=JSON.stringify(payload);if(fingerprint!==serialized){fingerprint=serialized;key=`quote-context-${crypto.randomUUID()}`;}
  message.textContent="";busy=true;controls();try{const saved=await saveQuoteContext(id,payload,key);if(!panel.isConnected)return;quote=saved;division=saved.commercial_terms_snapshot.division;key=null;fingerprint=null;lookup.replaceChildren();renderFormFeedback(form,[],{lang});syncRate();display();message.setAttribute('role','status');message.textContent=c.saved;await changed();}catch(value){if(panel.isConnected){busy=false;controls();renderFormFeedback(form,[value],{lang});}}finally{busy=false;controls();}
 };
 panel.querySelector('[data-quote-reload]').onclick=load;panel.querySelector('[data-quote-close]').onclick=close;await load();
}
