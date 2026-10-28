const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const HUB_URL = process.env.HUB_URL || 'http://127.0.0.1:8765';

(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const request = page.request;
  assert.equal((await request.get(HUB_URL+'/README.md')).status(),404);
  assert.equal((await request.get(HUB_URL+'/api/preview?role=bad&action=idle')).status(),400);
  assert.equal((await request.post(HUB_URL+'/api/validate',
    {data:'x'.repeat(65537)})).status(),413);
  assert.equal((await request.post(HUB_URL+'/api/validate',
    {headers:{Origin:'https://untrusted.example'},data:'{}'})).status(),403);
  for (const width of [1280,390]) {
    await page.setViewportSize({width,height:900});
    await page.goto(HUB_URL);
    await page.waitForFunction(()=>document.querySelectorAll('[data-role]').length===5);
    for(const role of ['egg','baby','rookie','champion','ultimate']) {
      await page.locator(`[data-role=${role}]`).click();
      await page.waitForTimeout(200);
      assert(await page.locator(`[data-role=${role}]`).getAttribute('aria-pressed')==='true');
    }
    await page.waitForFunction(()=>{
      const data=document.querySelector('canvas').getContext('2d').getImageData(0,0,320,240).data;
      return data.some((v,i)=>i%4===3&&v>0);
    });
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:`out/hub-${width}.png`,fullPage:true});
    await page.locator('[data-tab=import]').click();
    await page.locator('#file').setInputFiles('src/data/content/firemon.json');
    await page.getByRole('heading',{name:'Definición válida'}).waitFor();
    await page.locator('#file').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{}')});
    await page.locator('#import-result.bad').waitFor();
    await page.locator('[data-tab=device]').click();
    assert(await page.getByRole('button',{name:'Conectar placa'}).isDisabled());
  }
  assert.deepEqual(errors,[]);
  await browser.close();
  console.log('PASS: desktop/mobile, 5 stages, nonblank canvas, import valid/invalid, disabled USB, no overflow or JS errors');
})().catch(e=>{console.error(e);process.exit(1);});
