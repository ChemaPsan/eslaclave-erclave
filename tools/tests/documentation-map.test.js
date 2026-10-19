const assert = require('node:assert/strict');
const { validate, localLinks, render } = require('../documentation-map');
const files = ['docs/live.md', 'docs/old.md'];
const entries = [
 {path:files[0],status:'vigente',owner:'Arquitectura',authority:files[0]},
 {path:files[1],status:'historico',owner:'QA',authority:files[0]}
];
const exists = p => files.includes(p);
const read = () => '# Corte\n\nEvidencia histórica';
assert.deepEqual(validate(entries,files,exists,read),[]);
assert(validate(entries,[...files,'docs/new.md'],exists,read).some(x=>x.includes('sin clasificar')));
assert(validate([...entries,entries[0]],files,exists,read).some(x=>x.includes('duplicado')));
assert(validate(entries,files,exists,()=> '# Sin aviso').some(x=>x.includes('sin aviso')));
assert(validate(entries.map(e=>({...e,authority:'missing.md'})),files,exists,read).some(x=>x.includes('inexistente')));
assert(localLinks('docs/live.md','[roto](missing.md)',exists).length===1);
assert.deepEqual(localLinks('docs/live.md','[válido](old.md#corte) [[docs/old|Anterior]]',exists),[]);
assert(localLinks('docs/live.md','[[missing]]',exists).length===1);
assert(render(entries).includes('[docs/old.md](old.md)'));
assert.notEqual(render(entries),render(entries.slice(0,1)));
assert(validate(entries.map(e=>e.status==='historico'?{...e,authority:'secret.txt'}:e),files,()=>true,read).some(x=>x.includes('autoridad vigente')));
assert(validate([{...entries[0],authority:'../../outside.md'}],[files[0]],()=>true,read).some(x=>x.includes('Ruta fuera')));
assert(localLinks('docs/live.md','[missing]: missing.md',exists).length===1);
console.log('documentation-map: 13 casos de clasificación, enlaces e índice aprobados');
