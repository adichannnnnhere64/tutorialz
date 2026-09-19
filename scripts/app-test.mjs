import {chromium} from 'playwright';import assert from 'node:assert/strict';import fs from 'node:fs/promises';
const browser=await chromium.launch({executablePath:process.env.CHROME_BIN||'/etc/profiles/per-user/adrian/bin/google-chrome-stable',args:['--no-sandbox']});
const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const base=process.env.APP_URL||'http://127.0.0.1:8766/';
try{
 await page.goto(base);await page.getByRole('heading',{name:'Small steps. Stronger skills.'}).waitFor();
 await page.screenshot({path:'/tmp/tutorialz-library.png',fullPage:true});
 await page.getByRole('button',{name:'Start practicing'}).click();
 await page.getByLabel('Everyday algebra practice').check();
 await page.getByLabel('Number of questions').fill('2');await page.getByRole('button',{name:'Start session'}).click();
 await page.getByRole('button',{name:'Check answer'}).waitFor();
 if(await page.getByRole('radio').count())await page.getByText('56',{exact:true}).click();else await page.getByLabel('x',{exact:true}).fill('4');
 await page.getByRole('button',{name:'Check answer'}).click();await page.getByText("That's correct",{exact:false}).waitFor();
 await page.reload();await page.getByRole('button',{name:'Session & results',exact:false}).click();await page.getByRole('button',{name:'Next question'}).waitFor();await page.getByRole('button',{name:'Next question'}).click();
 if(await page.getByRole('radio').count())await page.getByText('56',{exact:true}).click();else await page.getByLabel('x',{exact:true}).fill('4');
 await page.getByRole('button',{name:'Check answer'}).click();await page.getByRole('button',{name:'View results'}).click();await page.getByRole('heading',{name:'Every attempt counts.'}).waitFor();
 await page.getByRole('button',{name:'Finish session',exact:true}).click();
 await page.getByRole('button',{name:'Settings & backups',exact:false}).click();
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export progress',exact:true}).click();const download=await downloadPromise;const backup=JSON.parse(await fs.readFile(await download.path(),'utf8'));assert.equal(backup.attempts.length,2);assert(backup.attempts.every(a=>a.correct));
 await page.getByLabel('Java pack directory URL').fill(base+'java-pack/');await page.getByRole('button',{name:'Download / verify pack'}).click();await page.getByText('Java pack installed. Code practice is ready offline.').waitFor();
 await page.evaluate(()=>navigator.serviceWorker.ready);await context.setOffline(true);await page.reload();await page.getByRole('heading',{name:'Small steps. Stronger skills.'}).waitFor();
 const javaResult=await page.evaluate(async()=>{const state=JSON.parse(await window.tutorialz.load('learner-state'));const q=state.courses[0].tests[0].questions.find(q=>q.type==='java');return window.tutorialz.java({question:q,source:q.reference});});assert(javaResult.passed);await context.setOffline(false);
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/tmp/tutorialz-mobile.png',fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.goto(base+'author/');await page.getByRole('heading',{name:'Good questions start here.'}).waitFor();await page.getByRole('button',{name:'Tests',exact:true}).click();await page.getByRole('button',{name:'1. Which type stores a true/false value?',exact:true}).click();await page.getByRole('button',{name:'Preview question',exact:true}).click();
 await page.getByRole('button',{name:'Check preview answer'}).waitFor();
 await page.screenshot({path:'/tmp/tutorialz-author.png',fullPage:true});
 console.log('PASS: learner grading, reload/resume, results, progress export, offline shell + Java, mobile layout, authoring preview');
 assert.deepEqual(errors,[]);
}finally{await browser.close();}
