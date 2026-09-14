import { saveProductionServiceEvidence, downloadProductionServiceEvidence } from "../api/production.js";

export function hasServiceEvidence(order,phase){return Boolean(order.serviceEvidence?.some(item=>item.phase===phase));}
export function serviceEvidenceFields(phase,t){
  return `<fieldset data-service-evidence-phase="${phase}" class="service-evidence-fields"><legend>${t(phase==='start'?'serviceEvidenceStart':'serviceEvidenceFinish')}</legend>
    <label class="preview-field"><span>${t(phase==='start'?'serviceEvidenceStartDescription':'serviceEvidenceFinishDescription')}</span><textarea name="${phase}Description" minlength="3" maxlength="4000" rows="3"></textarea></label>
    <label class="preview-field"><span>${t('serviceEvidenceAttachments')}</span><input name="${phase}Files" type="file" multiple accept=".jpg,.jpeg,.png,.webp,.heic,.heif,.bmp,.tif,.tiff,.pdf,.txt,.docx,.xlsx"><small>${t('serviceEvidenceLimits')}</small></label>
    <p class="helper-copy">${t('serviceEvidenceRetention')}</p></fieldset>`;
}
export function toggleServiceEvidence(form,phase,needed){
  const box=form.querySelector(`[data-service-evidence-phase="${phase}"]`);if(!box)return;
  box.hidden=!needed;
  box.querySelector('textarea').required=needed;
  box.querySelectorAll('input,textarea').forEach(control=>control.disabled=!needed);
}
export async function saveServiceEvidenceFromForm(form,order,phase,t){
  if(hasServiceEvidence(order,phase))return;
  const description=form.querySelector(`[name="${phase}Description"]`),input=form.querySelector(`[name="${phase}Files"]`);
  if(!description)return;
  const files=[...input.files];
  const error=message=>{throw {field:`${phase}Files`,message};};
  if(files.length>3)error(t('serviceEvidenceLimits'));
  const photo=/\.(jpe?g|png|webp|hei[cf]|bmp|tiff?)$/i;
  if(files.some(file=>file.size>(photo.test(file.name)?5:2)*1024*1024))error(t('serviceEvidenceLimits'));
  const encoded=await Promise.all(files.map(file=>new Promise((resolve,reject)=>{
    const reader=new FileReader();reader.onload=()=>resolve({filename:file.name,content_base64:String(reader.result).split(',')[1]});reader.onerror=()=>reject({field:`${phase}Files`,message:t('serviceEvidenceReadFailed')});reader.readAsDataURL(file);
  })));
  const bindings={description,files:input};encoded.forEach((_,i)=>{bindings[`files.${i}.filename`]=input;bindings[`files.${i}.content_base64`]=input;});
  form.formFeedbackBindings=bindings;
  try{
    order.serviceEvidence=await saveProductionServiceEvidence(order.id,phase,{description:description.value.trim(),files:encoded});
    description.readOnly=true;input.disabled=true;
  }catch(error){error.formContext={form,bindings};throw error;}
}
export function serviceEvidenceHistory(order,t,escape){
  return ['start','finish'].map(phase=>{
    const entry=order.serviceEvidence?.find(value=>value.phase===phase);
    return `<section class="service-evidence-fields"><h3>${t(phase==='start'?'serviceEvidenceStart':'serviceEvidenceFinish')}</h3>${entry?`<p class="service-evidence-description">${escape(entry.description)}</p><small>${escape(entry.created_at)}</small><ul>${entry.files.map(file=>`<li>${file.expired?`${escape(file.filename)} — ${t('serviceEvidenceExpired')}`:`<button type="button" class="secondary-action" data-evidence-download="${escape(file.id)}">${escape(file.filename)}</button> <small>${Math.ceil(file.size_bytes/1024)} KB · ${t('serviceEvidenceExpires')} ${escape(file.expires_at.slice(0,10))}</small>`}</li>`).join('')}</ul>`:`<p>${t('serviceEvidenceNotRecorded')}</p>`}</section>`;
  }).join('');
}
export async function downloadServiceEvidence(orderId,fileId){
  const result=await downloadProductionServiceEvidence(orderId,fileId);
  if(!result.blob)return;
  const url=URL.createObjectURL(result.blob),anchor=document.createElement('a');anchor.href=url;anchor.download=result.filename||'evidence';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
