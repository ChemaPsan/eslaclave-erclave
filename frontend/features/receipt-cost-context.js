/** Receipt cost conversion is explicit; warehouse/organization remain authorities. */
const receiptDrafts = new WeakMap();
export function receiptCommand(form, payload) {
  const { received_at, ...capture } = payload;
  const signature = JSON.stringify(capture);
  let command = receiptDrafts.get(form);
  if (!command || command.signature !== signature) {
    command = { signature, payload: { ...capture, received_at }, key: `receipt-${crypto.randomUUID()}` };
    receiptDrafts.set(form, command);
  }
  return command;
}

export function mountReceiptCostContext(form, { lang = 'es', orders, warehouses, scope }) {
  if (!form) return;
  const en = lang === 'en';
  const panel = document.createElement('label');
  panel.className = 'preview-field wide-field';
  panel.innerHTML = `<span>${en ? 'Exchange rate to Society currency' : 'Tipo de cambio a moneda de la Sociedad'}</span><input name="cost_exchange_rate" type="number" min="0.000001" max="999999999999.999999" step="0.000001" inputmode="decimal" aria-describedby="receipt-cost-help"><small id="receipt-cost-help"></small>`;
  const grid = form.querySelector('.form-grid') || form;
  grid.insertBefore(panel, grid.querySelector('.inline-actions'));
  const input = panel.querySelector('input'), help = panel.querySelector('small');
  const contextLabel=document.createElement('p');contextLabel.dataset.receiptOrganizationContext='';panel.before(contextLabel);
  let previousPair = '';
  function update() {
    const order = orders.find(value => value.id === form.elements.purchase_order_id.value);
    const context=order?.organization_context;
    contextLabel.textContent=context?`${en?'Division':'División'}: ${context.division_code||context.division_ref_id} · ${context.division_name||''} · ${en?'Society':'Sociedad'}: ${context.society_ref_id}`:'';
    const physical = order?.lines?.some(line => line.line_type === 'inventory_item');
    panel.hidden = !physical;
    input.disabled = !physical;
    input.required = false;
    if (!physical) { input.value = ''; previousPair = ''; return; }
    const currencies = new Set();
    for (const row of form.querySelectorAll('[data-receipt-line]')) {
      if (!(Number(row.querySelector('[name="quantity"]').value) > 0)) continue;
      const warehouse = warehouses.find(value => value.id === row.querySelector('[name="warehouse_id"]').value);
      const division = scope?.divisions?.find(value => value.id === warehouse?.division_ref_id);
      const society = scope?.societies?.find(value => value.id === division?.society_id);
      const frozen=order?.organization_context;
      if(frozen){
        if(warehouse?.division_ref_id===frozen.division_ref_id&&frozen.cost_currency)currencies.add(frozen.cost_currency);
      }else if (society?.base_currency) currencies.add(society.base_currency);
    }
    const target = currencies.size === 1 ? [...currencies][0] : '';
    const destinations=[...form.querySelectorAll('[name="warehouse_id"]')].map(control=>control.value).join(',');
    const pair = `${order?.id || ''}/${order?.currency || ''}/${target}/${destinations}`;
    if (previousPair && previousPair !== pair) input.value = '';
    previousPair = pair;
    input.readOnly = Boolean(target && target === order?.currency);
    if (input.readOnly) input.value = '1';
    input.required = Boolean(target && target !== order?.currency);
    help.textContent = target
      ? (en ? `1 ${order.currency} = this amount in ${target}. The original order price is preserved.` : `1 ${order.currency} = este importe en ${target}. Se conserva el precio original de la orden.`)
      : (en ? 'Select destination warehouses. Use an explicit rate when the order and Society currencies differ; the same currency uses 1. Separate receipts with different cost currencies.' : 'Selecciona los almacenes destino. Captura la tasa si la moneda de la orden difiere de la Sociedad; la misma moneda usa 1. Separa recepciones con distintas monedas de costo.');
  }
  form.addEventListener('change', event => { if (event.target !== input) update(); });
  form.addEventListener('input', event => { if (event.target.name === 'quantity') update(); });
  update();
}
