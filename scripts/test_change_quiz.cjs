// Browser checks use the shipped fictional template and temporary copies only.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
(async () => {
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'dasync-quiz-'));
  const source = path.resolve(__dirname, '../packages/templates/change-quiz/quiz.html');
  const url = pathToFileURL(source).href;
  const browser = await chromium.launch({executablePath:process.env.BROWSER_EXECUTABLE_PATH});
  const audits = [];
  try {
    const page = await browser.newPage({viewport:{width:1280,height:900}, reducedMotion:'reduce'});
    const errors = [], requests = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => { if (!request.url().startsWith('file:')) requests.push(request.url()); });
    await page.goto(url);
    const question = page.locator('#sample-v2-identity');
    const feedback = question.locator('[data-quiz-feedback]');
    const progress = page.locator('#sample-v2 [data-quiz-progress]');
    const history = page.locator('#quiz-history');
    assert.equal(await feedback.isVisible(), false);
    assert.equal(await history.evaluate(node => node.open), false);
    assert.equal(await progress.innerText(), '0 of 2 questions answered');
    for (const [value, expected] of [['a','Correct answer: C'],['b','Correct answer: C'],['c','Correct —'],['d','Correct answer: C']]) {
      await question.locator('input[value="'+value+'"]').check();
      assert.equal(await feedback.locator('[data-explanation]:visible').count(), 4);
      assert((await question.locator('[data-quiz-result]').innerText()).includes(expected));
      assert.equal(await progress.innerText(), '1 of 2 questions answered');
      assert.equal(await page.locator('#sample-v1 [data-quiz-progress]').textContent(), '0 of 1 questions answered');
    }
    await page.locator('#sample-v2-retry input[value="b"]').check();
    await question.locator('[data-quiz-retry]').click();
    assert.equal(await question.locator('input:checked').count(), 0);
    assert.equal(await feedback.isVisible(), false);
    assert.equal(await progress.innerText(), '1 of 2 questions answered');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'sample-v2-identity-a');
    await page.keyboard.press('Space');
    assert.equal(await feedback.isVisible(), true);
    await page.keyboard.press('ArrowRight');
    assert.equal(await question.locator('input:checked').inputValue(), 'b');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'sample-v2-identity-b');
    await page.keyboard.press('Tab');
    assert(await page.evaluate(() => document.activeElement.hasAttribute('data-quiz-retry')));
    await history.locator('summary').focus(); await page.keyboard.press('Enter');
    await page.locator('#sample-v1 input[value="a"]').check();
    assert.equal(await page.locator('#sample-v1 [data-quiz-progress]').innerText(), '1 of 1 questions answered');
    assert.equal(await progress.innerText(), '2 of 2 questions answered');
    await history.locator('summary').click();
    await question.locator('[data-quiz-retry]').click();
    for (let i=0; i<2; i++) {
      await page.evaluate(() => { window.dispatchEvent(new Event('beforeprint')); window.dispatchEvent(new Event('beforeprint')); });
      assert.equal(await page.locator('[data-quiz-feedback][hidden]').count(), 0);
      assert.equal(await page.locator('details:not([open])').count(), 0);
      await page.emulateMedia({media:'print'});
      await page.pdf({path:path.join(out,'quiz-'+i+'.pdf'),format:'A4',printBackground:true});
      await page.emulateMedia({media:'screen'});
      await page.evaluate(() => window.dispatchEvent(new Event('afterprint')));
      assert.equal(await history.evaluate(node => node.open), false);
      assert.equal(await feedback.isVisible(), false);
    }
    await page.goto(url+'#sample-v1-retry');
    assert.equal(await history.evaluate(node => node.open), true);
    await page.goto(url);
    assert.equal(await page.locator('input:checked').count(), 0);
    await question.locator('input[value="c"]').check();
    for (const theme of ['light','dark']) {
      await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
      if (process.env.AXE_PATH) {
        await page.addScriptTag({path:process.env.AXE_PATH});
        const audit = await page.evaluate(async () => axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}));
        assert.deepEqual(audit.violations.map(v => ({id:v.id,nodes:v.nodes.map(n => n.target)})), []);
        audits.push({theme,axe:audit.testEngine.version,violations:0});
      }
      await page.evaluate(() => { window.scrollTo(0,0); document.activeElement.blur(); });
      await page.screenshot({path:path.join(out,theme+'-desktop.png'),fullPage:true});
      for (const width of [320,390,640]) {
        await page.setViewportSize({width,height:844});
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'overflow '+width);
      }
      await page.evaluate(() => window.scrollTo(0,0));
      await page.screenshot({path:path.join(out,theme+'-mobile.png'),fullPage:true});
      await page.screenshot({path:path.join(out,theme+'-mobile-viewport.png')});
      await page.setViewportSize({width:1280,height:900});
    }
    await page.evaluate(() => { document.documentElement.style.fontSize = '30px'; });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'text zoom overflow');
    const ids = await page.locator('[id]').evaluateAll(nodes => nodes.map(n => n.id));
    assert.equal(new Set(ids).size, ids.length);
    assert.deepEqual(requests, []); assert.deepEqual(errors, []);
    const staticPage = await browser.newPage({javaScriptEnabled:false,viewport:{width:320,height:844}});
    await staticPage.goto(url);
    assert.equal(await staticPage.locator('[data-quiz-feedback]:visible').count(), 2);
    await staticPage.locator('#quiz-history > summary').click();
    assert.equal(await staticPage.locator('[data-quiz-feedback]:visible').count(), 3);
    assert.equal(await staticPage.locator('[data-quiz-retry]:visible').count(), 0);
    assert(await staticPage.locator('noscript').isVisible());
    const broken = path.join(out,'invalid.html');
    fs.writeFileSync(broken,fs.readFileSync(source,'utf8').replace('value="a" data-correct="false"','value="a" data-correct="true"'));
    await page.goto(pathToFileURL(broken).href);
    assert.equal(await question.locator('input:disabled').count(), 4);
    assert.equal(await question.locator('[data-quiz-error]').count(), 1);
    assert.equal(await feedback.isVisible(), true);
    // Prepend a third snapshot while preserving pristine earlier markup in one history.
    const original = fs.readFileSync(source,'utf8');
    const start = original.indexOf('<section class="quiz-snapshot"');
    const end = original.indexOf('<details class="disclosure quiz-history"');
    const prior = original.slice(start,end);
    const next = prior.replaceAll('sample-v2','sample-v3').replaceAll('fictional-v2','fictional-v3');
    const updated = path.join(out,'updated.html');
    const historyBody = original.indexOf('<div class="detail-body">',end)+'<div class="detail-body">'.length;
    fs.writeFileSync(updated,original.slice(0,start)+next+original.slice(end,historyBody).replace('History · 1 earlier snapshot','History · 2 earlier snapshots')+prior+original.slice(historyBody));
    await page.goto(pathToFileURL(updated).href);
    assert.equal(await page.locator('[data-quiz-snapshot]').count(),3);
    assert.equal(await history.count(),1);
    assert.equal(await history.locator('[data-quiz-question]').count(),3);
    assert.equal(await page.locator('[data-quiz-error]').count(),0);
    await page.locator('#sample-v3 input[value="c"]').first().check();
    assert.equal(await page.locator('#sample-v3 [data-quiz-progress]').innerText(),'1 of 2 questions answered');
    assert.equal(await progress.textContent(),'0 of 2 questions answered');
    assert.equal(await history.evaluate(node => node.open),false);
    fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({checks:'selection, feedback, retry, keyboard, independent history, hash, print, no-JS, themes, reflow, text zoom, invalid shape, third snapshot, no network',browser:browser.version(),accessibility:audits},null,2));
    console.log('Quiz browser checks passed. Evidence: '+out);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
