// Browser acceptance tests. Supply Playwright through the host or NODE_PATH.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');

(async () => {
  const root = path.resolve(__dirname, '..');
  const out = path.resolve(process.argv[2] || '/private/tmp/dasync-template-browser');
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({headless:true});
  const results = [];
  const audit = async (page, name, state) => {
    if (!process.env.AXE_PATH) return {state,status:'not-run'};
    await page.addScriptTag({path:process.env.AXE_PATH});
    const result = await page.evaluate(async () => axe.run(document, {
      runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}
    }));
    assert.deepEqual(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],name+' accessibility '+state);
    return {state,status:'no-violations',axe:result.testEngine.version,incompleteRules:result.incomplete.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))};
  };
  try {
    for (const [name, file] of Object.entries({
      trip:'trip-publish/trip.html', proposal:'design-proposal/proposal.html',
      review:'pr-review/report.html', deck:'pitch-deck/deck.html'
    })) {
      const context = await browser.newContext({viewport:{width:1440,height:1000}, reducedMotion:'reduce'});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const url = pathToFileURL(path.join(root, 'packages/templates', file)).href;
      await page.goto(url);
      await page.locator('main').waitFor();
      assert.equal(await page.locator('h1').count(), 1);
      assert.equal(await page.locator('details[open]').count(), 0);
      assert(await page.locator('[data-theme-toggle]').isVisible());
      await page.locator('[data-theme-toggle]').click();
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
      assert.equal(await page.locator('[data-theme-toggle]').getAttribute('aria-pressed'), 'true');
      const accessibility = [await audit(page,name,'dark-collapsed')];
      await page.screenshot({path:path.join(out, name+'-dark.png'),fullPage:true});
      await page.locator('[data-theme-toggle]').click();
      const links = await page.evaluate(() => [...document.querySelectorAll('a[href^="#"]')].every(a => document.getElementById(a.hash.slice(1))));
      assert(links, name+' broken fragment link');
      const ids = await page.locator('[id]').evaluateAll(nodes => nodes.map(n=>n.id));
      assert.equal(new Set(ids).size, ids.length, name+' duplicate ids');
      const details = page.locator('details.disclosure');
      if (name==='deck') await page.locator('[data-deck-view]').click();
      if (await details.count()) {
        const summary = details.first().locator('summary');
        await summary.focus(); await page.keyboard.press('Space');
        assert(await details.first().evaluate(node=>node.open), name+' keyboard disclosure');
        await page.keyboard.press('Enter');
        assert.equal(await details.first().evaluate(node=>node.open), false);
        await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
        assert.equal(await page.locator('details:not([open])').count(),0);
        accessibility.push(await audit(page,name,'light-expanded'));
        await page.emulateMedia({media:'print'});
        await page.pdf({path:path.join(out,name+'.pdf'),format:'A4',printBackground:true});
        await page.emulateMedia({media:'screen'});
        await page.evaluate(() => window.dispatchEvent(new Event('afterprint')));
        assert.equal(await page.locator('details[open]').count(),0, 'print restoration');
      }
      if (name==='trip') {
        await page.goto(url+'#rail-kyoto');
        assert(await page.locator('#rail-kyoto').evaluate(node=>node.open),'deep link reveals event');
        await page.goto(url);
        assert.equal(await page.locator('[data-group-filter],[data-day-filter]').count(),0);
        assert.equal(await page.locator('.trip-preview li').count(),6);
        assert.equal(await page.locator('.date-tile small').count(),9);
        assert.equal(await page.locator('.day-card').count(),9);
        await page.locator('[data-currency]').selectOption('JPY');
        assert.equal(await page.locator('[data-money-usd]').first().innerText(),'JPY 1,800,000');
        await page.locator('[data-currency]').selectOption('USD');
        assert.equal(await page.locator('[data-money-usd]').first().innerText(),'USD 12,000');
        await page.locator('[data-currency]').selectOption('JPY');
        assert.equal(await page.locator('[data-money-usd]').first().innerText(),'JPY 1,800,000');
        await page.locator('[data-currency]').selectOption('USD');
        const amounts=await page.locator('[data-money-usd]').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.moneyUsd)));
        assert.equal(amounts[0],amounts.slice(1).reduce((a,b)=>a+b,0),'budget reconciles');
        await page.goto(url+'#itinerary-09');
        assert(await page.locator('#itinerary-09').evaluate(n=>n.open));
        await page.goto(url);
      }
      if (name==='review') {
        await page.getByLabel('Find in findings').fill('no-such-finding');
        assert(await page.locator('[data-empty]').isVisible());
        assert.equal(await page.locator('[data-finding]:visible').count(),0);
        await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
        assert.equal(await page.locator('[data-finding][hidden]').count(),0);
        await page.evaluate(() => window.dispatchEvent(new Event('afterprint')));
        assert.equal(await page.locator('[data-finding][hidden]').count(),1);
        await page.getByLabel('Find in findings').fill('zero');
        assert.equal(await page.locator('[data-finding]:visible').count(),1);
        await page.getByLabel('Find in findings').fill('');
      }
      if (name==='deck') {
        await page.locator('[data-deck-view]').click();
        assert(await page.getByRole('button',{name:'Previous',exact:true}).isDisabled());
        await page.locator('main').focus(); await page.keyboard.press('End');
        await page.waitForFunction(() => document.querySelector('[data-next]').disabled);
        assert.equal(Number(await page.locator('progress').getAttribute('value')),await page.locator('.slide').count());
        await page.locator('main').focus(); await page.keyboard.press('Home');
        await page.waitForFunction(() => document.querySelector('[data-prev]').disabled);
        await page.pdf({path:path.join(out,name+'.pdf'),format:'A4',printBackground:true});
        await page.locator('[data-deck-view]').click();
      }
      for (const width of [1440,390,320]) {
        await page.setViewportSize({width,height:1000});
        await page.evaluate(() => scrollTo(0,0));
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),name+' page overflow at '+width);
        await page.screenshot({path:path.join(out,name+'-'+width+'.png'),fullPage:true});
      }
      accessibility.push(await audit(page,name,'light-320'));
      if(name==='deck' || name==='proposal') {
        const sequence=page.locator('[data-sequence]').first();
        await sequence.evaluate(node=>{for(let p=node.parentElement;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}});
        await sequence.locator('[data-step-next]').click();
        assert.equal(await sequence.locator('[data-step][data-active=true]').innerText(),'2. Send\nThe provider accepts the payment; the worker crashes before recording completion.');
        await sequence.locator('[data-play]').click();
        assert.equal(await sequence.locator('[data-play]').getAttribute('aria-pressed'),'true');
        await sequence.locator('[data-play]').click();
        assert.equal(await sequence.locator('[data-play]').getAttribute('aria-pressed'),'false');
      }
      // Stress real reflow rather than testing only short sample titles.
      await page.locator('h1').evaluate(n=>{n.textContent+=' — A substantially longer decision with a verylongunbrokencustomeridentifier012345678901234567890123456789';});
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),name+' long-title overflow');
      assert.deepEqual(errors,[]);
      await context.close();
      const noJS = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
      const fallback = await noJS.newPage(); await fallback.goto(url);
      assert(await fallback.locator('h1').isVisible());
      assert.equal(await fallback.locator('[data-theme-toggle]:visible').count(),0);
      if (await fallback.locator('details').count()) {
        await fallback.locator('summary').first().click();
        assert(await fallback.locator('details').first().evaluate(n=>n.open));
      }
      await noJS.close();
      results.push({page:name,status:'passed',accessibility,checks:['light/dark','320/390/1440 reflow','long title','unique IDs','fragment links','no page errors','no-JavaScript fallback','applicable interactions and print']});
    }
    fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({browser:browser.version(),results},null,2));
    console.log(JSON.stringify({out,browser:browser.version(),results},null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
