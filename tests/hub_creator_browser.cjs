const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const HUB_URL = process.env.HUB_URL || 'http://127.0.0.1:8765';

(async()=>{
  const browser=await chromium.launch({headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1280,height:950}});
    const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(HUB_URL);
    await page.locator('[data-tab=create]').click();
    await page.locator('[data-step="3"]').click();
    await page.getByRole('heading',{name:'Faltan recursos o hay datos por corregir'}).waitFor();
    assert(await page.locator('#export-project').isDisabled());
    await page.locator('[data-step="0"]').click();
    for(const [name,value] of Object.entries({name:'Aquamon',id:'test.aquamon',author:'Autor de prueba',description:'Proyecto de prueba con arte existente.'}))
      await page.locator(`[name="${name}"]`).fill(value);
    await page.locator('#creator-next').click();
    for(const role of ['egg','baby','rookie','champion','ultimate']) {
      await page.locator(`[data-creator-role=${role}]`).click();
      await page.locator('#animation-file').setInputFiles('assets/digimon/digimon1/baby/idle/sparkmon_idle.png');
      await page.waitForFunction(()=>!document.getElementById('save-draft').disabled);
      await page.waitForFunction(()=>{
        const canvas=document.getElementById('creator-canvas');
        return canvas.getContext('2d').getImageData(0,0,264,264).data.some((v,i)=>i%4===3&&v>0);
      });
      assert.equal(await page.locator('#animation-columns').inputValue(),'5');
    }
    await page.screenshot({path:'out/creator-animation-desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:900});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:'out/creator-animation-mobile.png',fullPage:true});
    await page.setViewportSize({width:1280,height:950});
    const images=await page.evaluate(async()=>{
      const response=await fetch('/api/preview?role=rookie&action=idle');
      const image=await createImageBitmap(await response.blob());
      const canvas=document.createElement('canvas');canvas.width=88;canvas.height=88;
      canvas.getContext('2d').drawImage(image,0,0,88,88,0,0,88,88);image.close();
      const portrait=canvas.toDataURL().split(',')[1];
      canvas.width=240;canvas.height=135;const ctx=canvas.getContext('2d');
      ctx.fillStyle='#b6d7ea';ctx.fillRect(0,0,240,135);ctx.fillStyle='#4c8c52';ctx.fillRect(0,95,240,40);
      return {portrait,background:canvas.toDataURL().split(',')[1]};
    });
    await page.locator('[data-step="2"]').click();
    for(const role of ['egg','baby','rookie','champion','ultimate']) {
      await page.locator('#portrait-'+role).setInputFiles({name:'portrait.png',mimeType:'image/png',buffer:Buffer.from(images.portrait,'base64')});
      await page.waitForFunction(()=>!document.getElementById('save-draft').disabled);
    }
    await page.locator('#background-day').setInputFiles({name:'day.png',mimeType:'image/png',buffer:Buffer.from(images.background,'base64')});
    await page.waitForFunction(()=>!document.getElementById('save-draft').disabled);
    await page.locator('#creator-next').click();
    await page.getByRole('heading',{name:'Proyecto válido para exportar'}).waitFor({timeout:60000});
    assert(!(await page.locator('#export-project').isDisabled()));
    for(const width of [1280,390]) {
      await page.setViewportSize({width,height:950});
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await page.screenshot({path:`out/creator-review-${width}.png`,fullPage:true});
    }
    const jsonDownload=page.waitForEvent('download');await page.locator('#download-json').click();
    await (await jsonDownload).saveAs('out/creator-content.json');
    assert.equal(JSON.parse(fs.readFileSync('out/creator-content.json')).id,'test.aquamon');
    const zipDownload=page.waitForEvent('download');await page.locator('#export-project').click();
    await (await zipDownload).saveAs('out/creator-project.zip');
    assert(fs.readFileSync('out/creator-project.zip').subarray(0,2).equals(Buffer.from('PK')));
    await page.waitForFunction(()=>!document.getElementById('save-draft').disabled);
    const draftDownload=page.waitForEvent('download');await page.locator('#save-draft').click();
    await (await draftDownload).saveAs('out/creator-draft.json');
    await page.reload();await page.locator('[data-tab=create]').click();
    await page.locator('#open-draft').setInputFiles('out/creator-draft.json');
    await page.getByText('Borrador abierto · revisión pendiente',{exact:true}).waitFor();
    assert.equal(await page.locator('[name=id]').inputValue(),'test.aquamon');
    await page.locator('[data-step="3"]').click();
    await page.getByRole('heading',{name:'Proyecto válido para exportar'}).waitFor({timeout:60000});
    assert.deepEqual(errors,[]);
    console.log('PASS: complete creator desktop/mobile, real PNGs, JSON/ZIP downloads, draft restore, incomplete project blocked, no JS errors/overflow');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
