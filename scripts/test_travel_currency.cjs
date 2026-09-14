// Focused offline conversion and expanded-day browser regression.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
  const html=fs.readFileSync(path.resolve(__dirname,'../packages/templates/trip-publish/trip.html'),'utf8');
  const browser=await chromium.launch({headless:true});
  try {
    const page=await browser.newPage({viewport:{width:390,height:844}});
    await page.setContent(html.replace('</select>','<option value="EUR" data-rate="0.9">EUR</option><option value="BAD" data-rate="0">Invalid</option></select>'));
    assert(await page.locator('option[value=BAD]').isDisabled());
    await page.locator('[data-currency]').selectOption('EUR');
    assert.equal(await page.locator('[data-money-usd]').first().innerText(),'EUR 10,800');
    for(let i=0;i<5;i++){
      await page.locator('[data-currency]').selectOption('JPY');
      await page.locator('[data-currency]').selectOption('USD');
    }
    assert.equal(await page.locator('[data-money-usd]').first().innerText(),'USD 12,000');
    await page.locator('[data-money-usd]').first().evaluate(n=>n.dataset.moneyUsd='0');
    await page.locator('[data-currency]').selectOption('JPY');
    assert.equal(await page.locator('[data-money-usd]').first().innerText(),'JPY 0');
    await page.locator('[data-money-usd]').first().evaluate(n=>n.dataset.moneyUsd='');
    await page.locator('[data-currency]').selectOption('USD');
    assert.equal(await page.locator('[data-money-usd]').first().innerText(),'Not yet priced');
    await page.setContent(html);
    const preview=page.locator('.trip-preview');
    assert(await preview.evaluate(n=>n.scrollWidth>n.clientWidth),'route scrolls inside its region');
    await preview.focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForFunction(()=>document.querySelector('.trip-preview').scrollLeft>0);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.emulateMedia({media:'print'});
    assert(await preview.evaluate(n=>n.scrollWidth<=n.clientWidth),'all route stops fit print width');
    await page.emulateMedia({media:'print',colorScheme:'dark'});
    assert.equal(await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor),'rgb(255, 255, 255)','system-dark printing uses paper colors');
    await page.emulateMedia({media:'screen'});
    await page.emulateMedia({colorScheme:'light'});
    assert.deepEqual(await page.locator('.date-tile small').allTextContents(),['tue','wed','thr','fri','sat','sun','mon','tue','wed']);
    await page.locator('#stay-tokyo>summary').click();
    // Controlled clipboard double: no writes to the user's system clipboard.
    await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedText=text;}}}));
    await page.locator('[data-copy-target=stay-reference]').click();
    assert.equal(await page.evaluate(()=>window.copiedText),'DEMO-NOT-A-BOOKING');
    assert.equal(await page.locator('.copy-feedback').innerText(),'Copied to clipboard.');
    await page.locator('[data-copy-target=stay-address]').click();
    assert.equal(await page.evaluate(()=>window.copiedText),'Replace with the full destination address');
    await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Denied');}}}));
    await page.locator('[data-copy-target=stay-reference]').click();
    assert((await page.locator('.copy-feedback').innerText()).startsWith('Copy unavailable.'));
    assert.equal(await page.evaluate(()=>getSelection().toString()),'DEMO-NOT-A-BOOKING');
    await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:undefined}));
    await page.locator('[data-copy-target=stay-address]').click();
    assert.equal(await page.evaluate(()=>getSelection().toString()),'Replace with the full destination address');
    await page.locator('#stay-tokyo>summary').click();
    await page.locator('#reservations').screenshot({path:'/private/tmp/dasync-travel-reservations.png'});
    await page.locator('[data-theme-toggle]').click();
    await page.locator('#at-a-glance').screenshot({path:'/private/tmp/dasync-travel-preview-dark.png'});
    await page.locator('[data-theme-toggle]').click();
    await page.locator('#itinerary-09>summary').click();
    await page.locator('#itinerary-09').screenshot({path:'/private/tmp/dasync-travel-day-mobile.png'});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.locator('[data-currency]').selectOption('JPY');
    await page.evaluate(()=>{window.dispatchEvent(new Event('beforeprint'));window.dispatchEvent(new Event('beforeprint'));});
    assert.equal(await page.locator('details:not([open])').count(),0);
    assert.equal(await page.locator('[data-money-usd]').first().innerText(),'JPY 1,800,000');
    await page.evaluate(()=>window.dispatchEvent(new Event('afterprint')));
    assert.equal(await page.locator('details[open]').count(),1);
    await page.setContent(html.replace('<option value="JPY" data-rate="150">JPY · Japanese yen</option>',''));
    assert.equal(await page.locator('[data-currency-control]:visible').count(),0);
    console.log('Passed: currency edge cases, print restoration, route scrolling/print fit, weekdays, copy success/denied/unavailable (clipboard double), expanded mobile day.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
