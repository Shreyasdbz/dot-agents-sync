// Behavioral checks for the shipped visual examples, not a model-quality evaluation.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
(async()=>{
  const out=path.resolve(process.argv[2] || path.join(require('node:os').tmpdir(),'dasync-visual-browser'));
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({executablePath:process.env.BROWSER_EXECUTABLE_PATH});
  const url=name=>pathToFileURL(path.resolve(__dirname,'../packages/templates',name)).href;
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    const settle=()=>page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));
    await page.goto(url('pitch-deck/deck.html'));
    const contrastResults=[];
    for (const theme of ['light','dark']) {
      await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
      const contrasts=await page.evaluate(()=>{
        const style=getComputedStyle(document.documentElement);
        const rgb=name=>{
          const probe=document.createElement('span');probe.style.color=style.getPropertyValue('--'+name);document.body.append(probe);
          const value=getComputedStyle(probe).color.match(/[\d.]+/g).slice(0,3).map(Number);probe.remove();return value;
        };
        const luminance=name=>rgb(name).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((sum,x,i)=>sum+x*[.2126,.7152,.0722][i],0);
        const pairs=[['ink','bg',4.5],['muted','bg',4.5],['ink','surface',4.5],['muted','surface',4.5],['accent','tint',4.5],['store','store-tint',4.5],['external','external-tint',4.5],['uncertain','uncertain-tint',4.5],['ink','store-tint',4.5],['ink','external-tint',4.5],['muted','tint',4.5],['accent','surface',3],['store','surface',3],['external','surface',3]];
        return pairs.map(([foreground,background,minimum])=>{const a=luminance(foreground),b=luminance(background);return{foreground,background,minimum,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};});
      });
      for (const pair of contrasts) assert(pair.ratio>=pair.minimum,theme+': '+JSON.stringify(pair));
      contrastResults.push({theme,pairs:contrasts});
      await page.locator('#slide-choice').selectOption('2');await settle();
      await page.screenshot({path:path.join(out,'flow-'+theme+'.png'),fullPage:true});
    }
    await page.evaluate(()=>document.documentElement.dataset.theme='light');
    await page.locator('#slide-choice').selectOption('2');
    await settle();
    await page.screenshot({path:path.join(out,'flow-desktop.png'),fullPage:true});
    await page.locator('#slide-choice').selectOption('4');
    const sequence=page.locator('[data-sequence]');
    const actor=()=>sequence.locator('[data-scene-active=true] strong').innerText();
    assert.equal(await actor(),'Operation store');
    await sequence.locator('[data-step-next]').click();assert.equal(await actor(),'Provider');
    assert.equal(await sequence.getAttribute('data-scene-index'),'1');
    assert((await sequence.locator('[data-scene-readout]').innerText()).startsWith('Send'));
    assert(await sequence.locator('[data-identity-token]').evaluate(n=>n.getAnimations().length>0),'key moves along the path in normal motion');
    // Rapid reversal must cancel the old path and commit the newly selected endpoint.
    await sequence.locator('[data-step-back]').click();await settle();
    assert.equal(await sequence.getAttribute('data-scene-index'),'0');
    assert.equal(await sequence.locator('[data-identity-token]').evaluate(n=>getComputedStyle(n).transform),'matrix(1, 0, 0, 1, 150, 70)');
    await sequence.locator('[data-step-next]').click();
    assert.equal(await sequence.locator('[aria-current=step] strong').innerText(),'2. Send');
    await sequence.locator('[data-step-next]').click();assert.equal(await actor(),'Recovery worker');
    await settle();
    await page.evaluate(()=>{window.scrollTo(0,0);document.activeElement.blur();});
    await page.screenshot({path:path.join(out,'sequence-desktop.png')});
    await sequence.locator('[data-step-next]').click();assert.equal(await actor(),'Operation store');
    const movingFrame=await sequence.locator('[data-identity-token]').evaluate(n=>{
      const animation=n.getAnimations()[0];animation.pause();animation.currentTime=360;
      return getComputedStyle(n).transform;
    });
    assert.notEqual(movingFrame,'matrix(1, 0, 0, 1, 150, 70)','intermediate recovery frame follows the return lane');
    await page.screenshot({path:path.join(out,'record-mid-motion.png')});
    await sequence.locator('[data-identity-token]').evaluate(n=>n.getAnimations().forEach(a=>a.finish()));
    assert(await sequence.locator('[data-step-next]').isDisabled());
    await sequence.locator('[data-play]').click();
    assert.equal(await sequence.locator('[aria-current=step] strong').innerText(),'1. Persist','terminal replay starts at first step');
    await sequence.locator('[data-play]').click();assert.equal(await sequence.locator('[data-play]').getAttribute('aria-pressed'),'false');
    await sequence.locator('[data-play]').click();
    await page.locator('#slide-choice').selectOption('3');
    assert.equal(await sequence.locator('[data-play]').getAttribute('aria-pressed'),'false','hidden scene stops playback');
    // Rapid reversals must select the requested state and leave at most one running entrance.
    await page.evaluate(()=>{const next=document.querySelector('[data-next]'),prev=document.querySelector('[data-prev]');for(let i=0;i<20;i++){next.click();prev.click();}});
    assert.equal(await page.locator('#slide-choice').inputValue(),'3');
    assert(await page.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length<=1));
    await page.evaluate(()=>{window.visualEntrance=document.querySelector('.slide:not([hidden])').getAnimations()[0];});
    assert(await page.evaluate(()=>Boolean(window.visualEntrance)),'normal motion has an entrance to cancel');
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.waitForFunction(()=>window.visualEntrance.playState==='idle');
    assert.equal(await page.evaluate(()=>document.getAnimations().length),0,'preference change cancels running entrance');
    await page.locator('#slide-choice').selectOption('4');
    assert.equal(await page.evaluate(()=>document.getAnimations().length),0,'reduced motion skips entrances');
    await sequence.locator('[data-step-next]').click();assert.equal(await actor(),'Provider');
    assert.equal(await sequence.locator('.mechanism-actor').first().evaluate(n=>getComputedStyle(n).transitionDuration),'0s');
    await sequence.locator('[data-play]').click();
    await page.waitForFunction(()=>document.querySelector('[data-step-next]').disabled && document.querySelector('[data-play]').getAttribute('aria-pressed')==='false');
    assert.equal(await actor(),'Operation store','play stops at terminal step');
    await page.setViewportSize({width:320,height:800});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(out,'sequence-mobile.png'),fullPage:true});
    // A 640px layout viewport approximates desktop reflow at 200% browser zoom.
    await page.setViewportSize({width:640,height:400});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));
    await page.emulateMedia({media:'print'});
    assert.equal(await page.locator('.slide:visible').count(),8);
    assert.equal(await sequence.locator('[data-step]:visible').count(),4);
    assert.equal(await sequence.locator('.actor-selection:visible').count(),0);
    await page.pdf({path:path.join(out,'visual-deck.pdf'),format:'A4',printBackground:true});
    await page.emulateMedia({media:'screen'});
    await page.evaluate(()=>window.dispatchEvent(new Event('afterprint')));
    await page.goto(url('design-proposal/proposal.html'));
    const disclosure=page.locator('details').filter({has:page.locator('[data-sequence]')});
    await disclosure.locator('summary').click();
    await page.locator('[data-play]').click();
    await disclosure.locator('summary').click();
    await page.waitForFunction(()=>document.querySelector('[data-play]').getAttribute('aria-pressed')==='false');
    assert.deepEqual(errors,[]);
    const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:320,height:800}});
    const staticPage=await context.newPage();await staticPage.goto(url('pitch-deck/deck.html'));
    assert.equal(await staticPage.locator('.slide:visible').count(),8);
    assert.equal(await staticPage.locator('[data-step]:visible').count(),4);
    assert.equal(await staticPage.locator('[data-sequence-controls]:visible').count(),0);
    assert(await staticPage.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await context.close();
    const result={browser:browser.version(),status:'passed',contrast:contrastResults,checks:['light/dark semantic contrast','identity path motion and reversal','actor/step synchronization','manual steps','pause/replay/end','hidden scene/disclosure stop','rapid reversal','dynamic reduced motion','320px and zoom-equivalent reflow','print all steps','no JavaScript'],limitations:['Chromium only','zoom-equivalent viewport is not a browser zoom action','not a behavioral model evaluation']};
    fs.writeFileSync(path.join(out,'visual-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
