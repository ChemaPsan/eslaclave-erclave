import { quoteContextCopy } from "../i18n/quote-context.js";
const escape=value=>String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
export function renderOrderContext(fields,lang="es"){
 if(!fields?.divisionRefId)return "";
 const c=quoteContextCopy[lang==="en"?"en":"es"],snapshot=fields.commercialTermsSnapshot;
 return `<section class="commercial-organization-panel" data-order-context><strong>${c.title}</strong><p>${c.division}: ${escape(snapshot?.division?.code)} · ${escape(snapshot?.division?.name)}</p><p>${c.society}: ${escape(fields.societyRefId)}</p><p>${c.currency}: ${escape(snapshot?.values?.currency)} · ${c.payment}: ${escape(snapshot?.values?.payment_terms)}</p><p>${c.credit}: ${escape(snapshot?.values?.credit_limit)}</p><p>${c.revision}: ${escape(snapshot?.terms_revision)}</p>${fields.costCurrency?`<p>${lang==="en"?"Original cost currency":"Moneda del costo original"}: ${escape(fields.costCurrency)} · 1 ${escape(fields.costCurrency)} = ${escape(fields.costExchangeRate)} ${escape(fields.currency)}</p>`:""}<p>${c.downstream}</p></section>`;
}
