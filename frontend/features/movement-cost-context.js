import { getWarehouseOperationContext } from "../api/inventory.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";
export function mountMovementCostContext(form,lang="es"){
 const warehouse=form.elements.warehouseId;if(!warehouse)return;
 const en=lang==="en",panel=document.createElement('div');panel.className='wide-field';
 panel.innerHTML=`<p role="status" data-movement-currency></p><button type="button" data-retry-currency>${en?"Refresh currency":"Consultar moneda"}</button><label class="preview-field" hidden><span>${en?'Unit cost in Society currency':'Costo unitario en moneda de la Sociedad'}</span><input name="unitCost" type="number" min="0" step="0.000001" inputmode="decimal" disabled></label>`;
 form.querySelector('.form-grid').append(panel);const cost=form.elements.unitCost,submit=form.querySelector('[type=submit]');let serial=0,context=null,failed=false;
 function reflect(){const incoming=['entry','positiveAdjustment'].includes(form.elements.movementType.value);cost.closest('label').hidden=!(context&&incoming);cost.required=Boolean(context&&incoming);cost.disabled=!cost.required;submit.disabled=failed;}
 async function load(){const ticket=++serial;failed=true;submit.disabled=true;context=null;reflect();panel.querySelector('p').textContent=en?'Loading cost currency…':'Consultando moneda del costo…';try{const value=await getWarehouseOperationContext(warehouse.value);if(!form.isConnected||ticket!==serial)return;context=value;failed=false;panel.querySelector('p').setAttribute('role','status');panel.querySelector('p').textContent=value?`${value.division_code} · ${value.division_name} · ${en?'Cost currency':'Moneda del costo'}: ${value.cost_currency}`:'';reflect();}catch(error){if(form.isConnected&&ticket===serial){panel.querySelector('p').setAttribute('role','alert');panel.querySelector('p').textContent=getLocalizedErrorMessage(error,{lang});}}}
 panel.querySelector('[data-retry-currency]').onclick=load;
 warehouse.addEventListener('change',()=>{cost.value='';load();});form.elements.movementType.addEventListener('change',reflect);load();
}
