/* Local authoring state is separate from the active pet, catalog and save. */
(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const roles = ['egg', 'baby', 'rookie', 'champion', 'ultimate'];
  const roleNames = {egg:'Huevo', baby:'Bebé', rookie:'Adulta I', champion:'Adulta II', ultimate:'Adulta III'};
  const actionNames = {idle:'Reposo', hatch:'Eclosión', walk:'Caminar', eat:'Comer', sleep:'Dormir',
    tired:'Cansancio', angry:'Enojo', evolution:'Evolución', punch:'Golpe', cast:'Especial',
    block:'Guardia', dodge:'Esquivar', hurt:'Daño', happy:'Alegría', sad:'Tristeza'};
  const visibleActions = role => role === 'egg' ? ['idle','hatch'] : role === 'baby' ?
    ['idle','walk','eat','sleep','tired','angry','evolution'] : Object.keys(actionNames).filter(a=>a!=='hatch');
  const form = el('creator-form');
  const defaults = ['HUEVO','BEBE','ETAPA1','ETAPA2','ETAPA3'];
  let project = {schema:1, identity:{name:'',id:'',version:'1.0.0',author:'',license:'CC-BY-4.0',description:''},
    stages:Object.fromEntries(roles.map((role,i)=>[role,{name:defaults[i],short_name:defaults[i],
      actions:{idle:{use:'upload',columns:1,rows:1,frames:1,interval_ms:100}}}])),
    resources:{reuse_day:true}};
  let step=0, role='egg', action='idle', revision=0, pending=0, busy=false, definition=null;
  let bitmap=null, previewToken=0, previewStart=0, playing=true, clock=0, lastTime=0;
  const urls = new Map();

  function changed() {
    revision++;
    definition=null;
    el('download-json').disabled=true;
    el('export-project').disabled=true;
    el('generated-json').textContent='';
    el('draft-state').textContent='Cambios en memoria · guarda un borrador para conservarlos';
    if(step===3) el('creator-report').textContent='Cambios pendientes de validar';
  }
  function message(text) { el('creator-error').textContent=text; }
  function refreshButtons() {
    el('check-project').disabled=busy||pending>0;
    el('export-project').disabled=!definition||busy||pending>0;
    el('download-json').disabled=!definition||busy||pending>0;
    el('save-draft').disabled=busy||pending>0;
  }
  function saveBlob(blob,name) {
    const url=URL.createObjectURL(blob), a=document.createElement('a');
    a.href=url; a.download=name; a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function fileBlob(asset) {
    const binary=atob(asset.data), bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));
    return new Blob([bytes],{type:'image/png'});
  }
  async function readPNG(file) {
    if(file.size>4*1024*1024) throw Error('Cada PNG puede pesar hasta 4 MiB.');
    const bytes=new Uint8Array(await file.arrayBuffer());
    const signature=[137,80,78,71,13,10,26,10];
    if(!signature.every((b,i)=>bytes[i]===b)) throw Error('Selecciona un archivo PNG válido.');
    const image=await createImageBitmap(file);
    const width=image.width, height=image.height;
    image.close();
    if(width>4096||height>4096||width*height>8*1024*1024) throw Error('Máximo 4096 px por lado y 8 megapíxeles.');
    const data=await new Promise((resolve,reject)=>{
      const reader=new FileReader();
      reader.onload=()=>resolve(reader.result.split(',')[1]);
      reader.onerror=()=>reject(Error('No se pudo leer el PNG.'));
      reader.readAsDataURL(file);
    });
    return {data,filename:file.name,width,height};
  }
  async function upload(file,assign) {
    if(!file)return;
    pending++;refreshButtons();message('');
    try { const asset=await readPNG(file);assign(asset);changed(); }
    catch(error) { message(error.message); }
    finally { pending--;refreshButtons(); }
  }
  function thumbnail(id,asset) {
    if(urls.has(id)){URL.revokeObjectURL(urls.get(id));urls.delete(id);}
    const image=el(id);image.hidden=!asset;
    if(!asset){image.removeAttribute('src');return;}
    try {const url=URL.createObjectURL(fileBlob(asset));urls.set(id,url);image.src=url;}
    catch { image.hidden=true; }
  }
  function getSpec() { return project.stages[role].actions[action]||{use:'idle'}; }
  function updateActionList() {
    el('creator-actions').replaceChildren(...visibleActions(role).map(key=>{
      const button=document.createElement('button');button.type='button';
      button.dataset.creatorAction=key;
      button.setAttribute('aria-pressed',String(key===action));
      const title=document.createElement('span');title.textContent=actionNames[key];
      const state=document.createElement('span');state.className='action-state';
      const spec=project.stages[role].actions[key];
      state.textContent=spec?.use==='upload'?(spec.asset?'PNG':'Falta PNG'):'Reutiliza';
      button.append(title,state);button.onclick=()=>{action=key;renderEditor();};return button;
    }));
  }
  function selectRole(nextRole) {
    role=nextRole;action='idle';
    el('stage-name').value=project.stages[role].name;
    el('stage-short').value=project.stages[role].short_name;
    document.querySelectorAll('[data-creator-role]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.creatorRole===role)));
    renderEditor();
  }
  function renderEditor() {
    const spec=getSpec();
    updateActionList();
    el('animation-title').textContent=actionNames[action];
    const options=[new Option('PNG propio','upload')];
    if(action!=='idle') for(const target of visibleActions(role)) {
      if(target!==action&&project.stages[role].actions[target]?.use==='upload')
        options.push(new Option('Reutilizar '+actionNames[target].toLowerCase(),target));
    }
    el('animation-use').replaceChildren(...options);
    el('animation-use').value=spec.use;
    el('upload-settings').hidden=spec.use!=='upload';
    el('animation-file').value='';
    el('animation-filename').textContent=spec.asset?`${spec.asset.filename} · ${spec.asset.width} × ${spec.asset.height}`:'Sin archivo';
    for(const [field,key] of [['columns','columns'],['rows','rows'],['frames','frames'],['interval','interval_ms']])
      el('animation-'+field).value=spec[key]??(field==='interval'?100:1);
    el('sleep-loop').hidden=action!=='sleep';
    el('loop-first').value=(spec.loop?.[0]??0)+1;
    el('loop-last').value=(spec.loop?.[1]??((spec.frames||1)-1))+1;
    loadPreview();
  }
  async function loadPreview() {
    const token=++previewToken;
    if(bitmap){bitmap.close();bitmap=null;}
    el('animation-error').textContent='';
    el('preview-empty').hidden=false;
    const current=getSpec();
    const spec=current.use==='upload'?current:project.stages[role].actions[current.use];
    if(!spec?.asset){el('preview-empty').textContent='Sin animación';return;}
    try {
      const image=await createImageBitmap(fileBlob(spec.asset));
      if(token!==previewToken){image.close();return;}
      const columns=spec.columns, rows=spec.rows, count=spec.frames;
      if(!Number.isInteger(columns)||!Number.isInteger(rows)||columns<1||rows<1||columns>64||rows>64||
        image.width%columns||image.height%rows||image.width/columns!==image.height/rows||
        image.width/columns>512||!Number.isInteger(count)||count<1||count>64||count>columns*rows||
        !Number.isInteger(spec.interval_ms)||spec.interval_ms<10||spec.interval_ms>1000) {
        image.close();throw Error('Revisa la cuadrícula: celdas cuadradas hasta 512 px, 1–64 cuadros e intervalo de 10–1000 ms.');
      }
      const cell=image.width/columns;
      const source=document.createElement('canvas');source.width=image.width;source.height=image.height;
      const sourceContext=source.getContext('2d',{willReadFrequently:true});
      sourceContext.drawImage(image,0,0);
      const pixels=sourceContext.getImageData(0,0,image.width,image.height).data;
      const bounds=[cell,cell,0,0];
      for(let frame=0;frame<count;frame++) {
        let visible=false;
        const ox=(frame%columns)*cell, oy=Math.floor(frame/columns)*cell;
        for(let y=0;y<cell;y++)for(let x=0;x<cell;x++) {
          if(pixels[((oy+y)*image.width+ox+x)*4+3]>=128) {
            visible=true;bounds[0]=Math.min(bounds[0],x);bounds[1]=Math.min(bounds[1],y);
            bounds[2]=Math.max(bounds[2],x+1);bounds[3]=Math.max(bounds[3],y+1);
          }
        }
        if(!visible){image.close();throw Error(`El cuadro ${frame+1} está completamente transparente.`);}
      }
      const width=bounds[2]-bounds[0], height=bounds[3]-bounds[1], scale=Math.min(84/width,84/height);
      const dw=Math.max(1,Math.round(width*scale)), dh=Math.max(1,Math.round(height*scale));
      const strip=document.createElement('canvas');strip.width=88*count;strip.height=88;
      const ctx=strip.getContext('2d');ctx.imageSmoothingEnabled=false;
      for(let frame=0;frame<count;frame++)ctx.drawImage(image,
        (frame%columns)*cell+bounds[0],Math.floor(frame/columns)*cell+bounds[1],width,height,
        frame*88+Math.floor((88-dw)/2),86-dh,dw,dh);
      image.close();
      const normalized=await createImageBitmap(strip);
      if(token!==previewToken){normalized.close();return;}
      bitmap=normalized;previewStart=clock;
      el('preview-empty').hidden=true;
    } catch(error) { el('animation-error').textContent=error.message; }
  }
  function animate(now) {
    if(playing&&lastTime)clock+=Math.min(now-lastTime,100);
    lastTime=now;
    const canvas=el('creator-canvas'),ctx=canvas.getContext('2d');
    ctx.clearRect(0,0,264,264);
    if(bitmap&&!el('create').hidden&&step===1) {
      const current=getSpec();
      const spec=current.use==='upload'?current:project.stages[role].actions[current.use];
      const total=spec.frames;
      const elapsed=Math.floor((clock-previewStart)/spec.interval_ms);
      let frame=elapsed%total;
      if(action==='sleep'&&spec.loop&&elapsed>=total) {
        const [first,last]=spec.loop;
        if(first>=0&&last>=first&&last<total)frame=first+(elapsed-total)%(last-first+1);
      }
      ctx.imageSmoothingEnabled=false;
      ctx.drawImage(bitmap,frame*88,0,88,88,22,22,220,220);
      el('frame-status').textContent=`Cuadro ${frame+1} / ${total}`;
    }
    requestAnimationFrame(animate);
  }
  function identityFromForm() {
    for(const key of Object.keys(project.identity))project.identity[key]=form.elements.namedItem(key).value;
  }
  function setStep(next) {
    step=next;
    document.querySelectorAll('[data-pane]').forEach(p=>p.hidden=Number(p.dataset.pane)!==step);
    document.querySelectorAll('[data-step]').forEach(b=>{
      if(Number(b.dataset.step)===step)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');
    });
    el('creator-back').disabled=step===0;
    el('creator-next').hidden=step===3;
    el('creator-progress').textContent=`Paso ${step+1} de 4`;
    if(step===3)checkProject();
  }
  async function checkProject() {
    if(busy||pending){message('Espera a que terminen las cargas.');return;}
    identityFromForm();
    const expectedRevision=revision;
    busy=true;refreshButtons();message('');
    el('creator-report').className='';el('creator-report').textContent='Validando gráficos y definición…';
    definition=null;
    try {
      const response=await fetch('/api/creator/check',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(project),signal:AbortSignal.timeout(60000)});
      const report=await response.json();
      if(!response.ok)throw Error(report.error);
      if(expectedRevision!==revision)throw Error('El proyecto cambió durante la revisión. Valídalo de nuevo.');
      const target=el('creator-report');target.replaceChildren();target.className=report.valid?'good':'bad';
      const title=document.createElement('h3');title.textContent=report.valid?'Proyecto válido para exportar':'Faltan recursos o hay datos por corregir';target.append(title);
      for(const messages of [report.errors||[],report.warnings||[]]) {
        const list=document.createElement('ul');
        messages.forEach(text=>{const item=document.createElement('li');item.textContent=text;list.append(item);});target.append(list);
      }
      if(report.valid) {
        definition=report.definition;
        const text=document.createElement('p');text.textContent=`${report.file_count} recursos · ${(report.source_bytes/1048576).toFixed(2)} MiB PNG · ${(report.prepared_bytes/1048576).toFixed(2)} MiB preparados. No representa el espacio final en placa.`;target.append(text);
        el('generated-json').textContent=JSON.stringify(definition,null,2);
      } else el('generated-json').textContent='La definición estará disponible al corregir los errores.';
    }catch(error){message(error.message);el('creator-report').textContent='No se pudo completar la validación.';}
    finally{busy=false;refreshButtons();}
  }
  for(const button of document.querySelectorAll('[data-step]'))button.onclick=()=>setStep(Number(button.dataset.step));
  form.onsubmit=event=>event.preventDefault();
  for(const key of Object.keys(project.identity))form.elements.namedItem(key).addEventListener('input',()=>{identityFromForm();changed();});
  el('creator-back').onclick=()=>setStep(Math.max(0,step-1));
  el('creator-next').onclick=()=>{
    const fields=[...document.querySelectorAll(`[data-pane="${step}"] input:not([type=file]),[data-pane="${step}"] textarea`)];
    const invalid=fields.find(input=>!input.disabled&&!input.checkValidity());
    if(invalid){invalid.reportValidity();return;}setStep(Math.min(3,step+1));
  };
  for(const name of ['name','short'])el('stage-'+name).oninput=()=>{
    project.stages[role][name==='short'?'short_name':'name']=el('stage-'+name).value;changed();
  };
  for(const key of roles) {
    const button=document.createElement('button');button.type='button';button.textContent=roleNames[key];
    button.dataset.creatorRole=key;button.onclick=()=>selectRole(key);el('creator-stages').append(button);
    const label=document.createElement('label');label.className='portrait-slot';label.append(document.createTextNode(roleNames[key]+' · retrato'));
    const input=document.createElement('input');input.type='file';input.accept='image/png';input.id='portrait-'+key;
    const image=document.createElement('img');image.id='portrait-preview-'+key;image.alt='Retrato de '+roleNames[key];image.hidden=true;
    input.onchange=()=>upload(input.files[0],asset=>{project.stages[key].portrait=asset;thumbnail(image.id,asset);});
    label.append(input,image);el('portrait-fields').append(label);
  }
  el('animation-use').onchange=()=>{
    const value=el('animation-use').value;
    project.stages[role].actions[action]=value==='upload'?{use:'upload',columns:1,rows:1,frames:1,interval_ms:100}:{use:value};
    changed();renderEditor();
  };
  el('animation-file').onchange=()=>{
    const selectedRole=role,selectedAction=action;
    upload(el('animation-file').files[0],asset=>{
      const spec=project.stages[selectedRole].actions[selectedAction];
      if(spec?.use!=='upload')return;
      spec.asset=asset;
      if(asset.width%asset.height===0&&asset.width/asset.height<=64&&asset.height<=512) {
        spec.columns=asset.width/asset.height;spec.rows=1;spec.frames=spec.columns;
      } else if(asset.width===asset.height&&asset.width>512&&asset.width%5===0&&asset.width/5<=512) {
        spec.columns=5;spec.rows=5;spec.frames=25;
      }
      if(role===selectedRole&&action===selectedAction)renderEditor();
    });
  };
  for(const [field,key] of [['columns','columns'],['rows','rows'],['frames','frames'],['interval','interval_ms']])
    el('animation-'+field).oninput=()=>{const spec=getSpec();spec[key]=Number(el('animation-'+field).value);changed();loadPreview();};
  for(const id of ['loop-first','loop-last'])el(id).oninput=()=>{
    getSpec().loop=[Number(el('loop-first').value)-1,Number(el('loop-last').value)-1];changed();loadPreview();
  };
  el('creator-play').onclick=()=>{playing=!playing;el('creator-play').textContent=playing?'Pausar':'Reanudar';el('creator-play').setAttribute('aria-pressed',String(!playing));};
  for(const [inputId,key,imageId] of [['background-day','day','day-thumbnail'],['background-night','night','night-thumbnail'],['cover-file','cover','cover-thumbnail']])
    el(inputId).onchange=()=>upload(el(inputId).files[0],asset=>{project.resources[key]=asset;thumbnail(imageId,asset);});
  el('reuse-background').onchange=()=>{project.resources.reuse_day=el('reuse-background').checked;el('night-field').hidden=project.resources.reuse_day;changed();};
  el('check-project').onclick=checkProject;
  el('download-json').onclick=()=>{if(definition)saveBlob(new Blob([JSON.stringify(definition,null,2)],{type:'application/json'}),'content.json');};
  el('export-project').onclick=async()=>{
    if(!definition||busy||pending)return;
    busy=true;refreshButtons();message('');
    try {
      const response=await fetch('/api/creator/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(project),signal:AbortSignal.timeout(60000)});
      if(!response.ok)throw Error((await response.json()).error);
      saveBlob(await response.blob(),project.identity.id+'-'+project.identity.version+'-project.zip');
      el('draft-state').textContent='Proyecto ZIP exportado · no se ha publicado ni instalado';
    }catch(error){message(error.message);}finally{busy=false;refreshButtons();}
  };
  el('save-draft').onclick=()=>{
    identityFromForm();
    saveBlob(new Blob([JSON.stringify(project)],{type:'application/json'}),'vpet-borrador.json');
    el('draft-state').textContent='Borrador descargado con sus PNG';
  };
  el('open-draft').onchange=async()=>{
    const file=el('open-draft').files[0];if(!file)return;
    if(pending||busy){message('Espera a que terminen las operaciones actuales.');return;}
    try {
      if(file.size>24*1024*1024)throw Error('Borrador mayor de 24 MiB.');
      const candidate=JSON.parse(await file.text());
      if(candidate?.schema!==1||!candidate.identity||!candidate.stages||!candidate.resources||
        !roles.every(key=>candidate.stages[key]&&typeof candidate.stages[key].name==='string'&&
          typeof candidate.stages[key].short_name==='string'&&candidate.stages[key].actions?.idle?.use==='upload'))
        throw Error('No es un borrador del asistente.');
      for(const stage of Object.values(candidate.stages))for(const [key,spec] of Object.entries(stage.actions))
        if(![...Object.keys(actionNames),'hit','hit_react'].includes(key)||!spec||typeof spec.use!=='string')throw Error('Acciones de borrador no válidas.');
      if(!Object.keys(project.identity).every(key=>typeof candidate.identity[key]==='string'))throw Error('Identidad no válida.');
      project=candidate;changed();
      for(const key of Object.keys(project.identity))if(form.elements.namedItem(key))form.elements.namedItem(key).value=project.identity[key];
      for(const key of roles){el('portrait-'+key).value='';thumbnail('portrait-preview-'+key,project.stages[key].portrait);}
      for(const [key,id] of [['day','day-thumbnail'],['night','night-thumbnail'],['cover','cover-thumbnail']])thumbnail(id,project.resources[key]);
      el('reuse-background').checked=!!project.resources.reuse_day;el('night-field').hidden=!!project.resources.reuse_day;
      selectRole('egg');setStep(0);message('');el('draft-state').textContent='Borrador abierto · revisión pendiente';
    }catch(error){message(error.message);}
    el('open-draft').value='';
  };
  selectRole('egg');setStep(0);requestAnimationFrame(animate);
})();
