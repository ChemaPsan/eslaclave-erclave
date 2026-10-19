const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const excluded = new Set(['.git', 'node_modules', '.venv', '.venv.broken-20260826', '__pycache__', '.local', '.pytest_cache', 'dist', 'test-results', 'playwright-report', '.obsidian']);
function inventory(base = root, relative = '') {
  return fs.readdirSync(base, {withFileTypes:true}).flatMap(entry => {
    if (excluded.has(entry.name)) return [];
    const next = path.join(base, entry.name), rel = path.posix.join(relative, entry.name);
    return entry.isDirectory() ? inventory(next, rel) : /\.(md|docx|drawio|canvas)$/i.test(entry.name) ? [rel] : [];
  }).sort();
}
function render(entries) {
  let out = '# Índice documental completo\n\nGenerado desde [registro](documentacion-registro.json) con npm run docs:index. No editar esta tabla a mano. Volver al [portal](INICIO.md).\n\nVigente significa fuente mantenida; no certifica despliegue ni pruebas. Diseño describe intención, historia conserva evidencia y exportación pendiente no es autoridad.\n';
  for (const status of ['vigente','diseno','historico','exportacion-pendiente']) {
    out += '\n## ' + status + '\n\n| Documento | Custodio | Autoridad para consultar |\n|---|---|---|\n';
    for (const e of entries.filter(e=>e.status===status).sort((a,b)=>a.path.localeCompare(b.path,'en'))) {
      const link = p => path.posix.relative('docs',p).split('/').map(encodeURIComponent).join('/');
      out += '| ['+e.path+']('+link(e.path)+') | '+e.owner+' | [Fuente]('+link(e.authority)+') |\n';
    }
  }
  return out;
}
function validate(entries, files, exists, read) {
  const safe = p => typeof p === "string" && p.length > 0 && !p.includes("\\") && !path.posix.isAbsolute(p) && !/^[A-Za-z]:/.test(p) && path.posix.normalize(p) === p && !p.split("/").includes("..");
  const errors=[], seen=new Set(), allowed=new Set(['vigente','diseno','historico','exportacion-pendiente']);
  for (const e of entries) {
    for (const key of ["path","authority",...(e.source ? ["source"] : [])]) if (!safe(e[key])) errors.push("Ruta fuera del registro permitido: "+key+" "+e[key]);
    if (seen.has(e.path)) errors.push('Registro duplicado: '+e.path);
    seen.add(e.path);
    if (!files.includes(e.path)) errors.push('Documento eliminado o fuera de alcance: '+e.path);
    if (!allowed.has(e.status) || !e.owner || !e.authority) errors.push('Clasificación incompleta: '+e.path);
    if (!exists(e.authority)) errors.push('Autoridad inexistente: '+e.path+' -> '+e.authority);
    if (safe(e.path) && files.includes(e.path) && e.status==='historico' && /\.md$/.test(e.path) && !/Evidencia hist[oó]rica/i.test(read(e.path).slice(0,1200))) errors.push('Historia sin aviso visible: '+e.path);
    if (e.status==='exportacion-pendiente' && (!e.source || !exists(e.source))) errors.push('Exportación sin fuente: '+e.path);
  }
  for (const file of files) if (!seen.has(file)) errors.push('Documento sin clasificar: '+file);
  for (const e of entries) if (e.status==='historico') {
    const authority=entries.find(x=>x.path===e.authority);
    if (!authority || authority.status!=='vigente') errors.push('Historia debe enlazar autoridad vigente: '+e.path);
  }
  for (const e of entries) if (e.status==='exportacion-pendiente') {
    const source=entries.find(x=>x.path===e.source);
    if (!source || source.status!=='vigente') errors.push("Exportación requiere fuente registrada vigente: "+e.path);
  }
  return errors;
}
function localLinks(file, source, exists) {
  const errors=[];
  const text=source.replace(/^\x60\x60\x60[^\n]*\n[\s\S]*?^\x60\x60\x60\s*$/gm,'');
  const links=[...text.matchAll(/\[[^\]\n]*\]\(([^)\n]+)\)/g)].map(m=>m[1].trim());
  links.push(...[...text.matchAll(/^\s{0,3}\[[^\]\n]+\]:\s*(<[^>]+>|\S+)/gm)].map(m=>m[1]));
  for (let target of links) {
    if (/^(?:[a-z]+:|#|\/v1\/)/i.test(target)) continue;
    target=target.replace(/^<([^>]+)>.*$/,'$1').replace(/\s+["'][^"']*["']$/,'').split('#')[0];
    try { target=decodeURIComponent(target); } catch { errors.push('URL inválida: '+file); continue; }
    if (target && !exists(path.posix.normalize(path.posix.join(path.posix.dirname(file),target)))) errors.push('Enlace roto: '+file+' -> '+target);
  }
  for (const match of text.matchAll(/\[\[([^\]\n]+)\]\]/g)) {
    const target=match[1].split('|')[0].split('#')[0];
    if (!target) continue;
    const p=/\.[a-z]+$/i.test(target)?target:target+'.md';
    if (!exists(p) && !exists(path.posix.join(path.posix.dirname(file),p))) errors.push('Wikilink no resoluble (usar ruta explícita): '+file+' -> '+target);
  }
  return errors;
}
function main() {
  const registry=JSON.parse(fs.readFileSync(path.join(root,'docs/documentacion-registro.json'),'utf8'));
  const files=inventory();
  const exists=p=>!!p && fs.existsSync(path.resolve(root,p));
  const read=p=>fs.readFileSync(path.resolve(root,p),'utf8');
  const errors=validate(registry.documents,files,exists,read);
  for (const file of files.filter(f=>f.endsWith('.md'))) errors.push(...localLinks(file,read(file),exists));
  for (const entry of registry.documents.filter(e=>e.status==='exportacion-pendiente')) {
    for (const [file,key] of [[entry.source,'sourceSha256'],[entry.path,'artifactSha256']]) {
      if (!file || !files.includes(file)) continue;
      const digest=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex');
      if (entry[key]!==digest) errors.push('Paridad documental requiere nueva revisión: '+file+' ('+key+'). Regenerar, comprobar texto y actualizar registro; no sólo copiar hash.');
    }
  }
  const expected=render(registry.documents);
  if (process.argv.includes('--write') && !errors.length) fs.writeFileSync(path.join(root,'docs/INDICE_DOCUMENTAL.md'),expected);
  else if (read('docs/INDICE_DOCUMENTAL.md')!==expected) errors.push('Índice desactualizado: ejecutar npm run docs:index después de clasificar cambios.');
  if (errors.length) { console.error(errors.join('\n')); process.exitCode=1; }
  else console.log('Documentación clasificada y enlazada: '+files.length+' archivos. Semántica y Word visual requieren revisión humana/agentes.');
}
module.exports={inventory,render,validate,localLinks};
if (require.main===module) main();
