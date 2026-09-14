const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
(async()=>{
 const browser=await chromium.launch();
 try {
  const page=await browser.newPage({viewport:{width:1280,height:800},reducedMotion:'no-preference'});
  await page.goto(pathToFileURL(path.resolve(__dirname,'../packages/templates/pitch-deck/deck.html')).href);
  await page.locator('[data-next]').click();
  await page.waitForTimeout(800);
  console.log('After Next:',await page.locator('progress').getAttribute('value'));
  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(800);
  console.log('After ArrowRight with Next focused:',await page.locator('progress').getAttribute('value'));
  assert.equal(await page.locator('progress').getAttribute('value'),'3');
  const count=await page.locator('.slide').count();
  for(let i=3;i<count;i++){await page.keyboard.press('ArrowRight');}
  await page.waitForTimeout(800);
  assert.equal(Number(await page.locator('progress').getAttribute('value')),count);
  for(let i=count;i>1;i--){await page.keyboard.press('ArrowLeft');}
  await page.waitForTimeout(800);
  assert.equal(await page.locator('progress').getAttribute('value'),'1');
  await page.locator('#slide-choice').selectOption('5');
  assert(await page.locator('#contract').isVisible());
  await page.screenshot({path:path.join(require('node:os').tmpdir(), 'dasync-dense-slide-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(require('node:os').tmpdir(), 'dasync-dense-slide-mobile.png'),fullPage:true});
  await page.locator('[data-deck-view]').click();
  assert.equal(await page.locator('.slide[hidden]').count(),0);
  console.log('Sequential and rapid keyboard traversal passed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
