import {chromium} from 'playwright';import assert from 'node:assert/strict';import fs from 'node:fs/promises';
const browser=await chromium.launch({executablePath:process.env.CHROME_BIN||'/etc/profiles/per-user/adrian/bin/google-chrome-stable',args:['--no-sandbox']});
const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const base=process.env.APP_URL||'http://127.0.0.1:8766/';
await page.route('https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json',route=>route.fulfill({path:'content/enterprise/catalog.json',contentType:'application/json'}));
try{
 await page.goto(base);await page.getByRole('heading',{name:'Small steps. Stronger skills.'}).waitFor();
 await page.getByLabel('Search questions and topics').fill('optimistic locking');
 await page.getByRole('heading',{name:'Question results'}).waitFor();
 assert(await page.getByRole('button',{name:'Practice this question'}).count()>0);
 for(const topic of ['Type inference with var','Covariant return']){
  await page.getByLabel('Search questions and topics').fill(topic);
  await page.getByRole('heading',{name:'Question results'}).waitFor();
  assert(await page.getByRole('button',{name:'Practice this question'}).count()>0,`No result for ${topic}`);
 }
 await page.getByLabel('Search questions and topics').fill('');
 await page.screenshot({path:'/tmp/tutorialz-library.png',fullPage:true});
 await page.getByRole('button',{name:'Start practicing'}).click();
 await page.getByLabel('Platform practice').first().check();
 await page.getByLabel('Number of questions').fill('2');await page.getByRole('button',{name:'Start session'}).click();
 await page.getByRole('button',{name:'Check answer'}).waitFor();
 await page.waitForFunction(async()=>{const s=await window.tutorialz.load('learner-state');return s&&JSON.parse(s).progress.active?.questions?.length===2;});
 const session=JSON.parse(await page.evaluate(()=>window.tutorialz.load('learner-state'))).progress.active;
 await page.getByRole('radio').nth(session.questions[0].correct[0]).check();
 await page.getByRole('button',{name:'Check answer'}).click();await page.getByText("That's correct",{exact:false}).waitFor();
 await page.reload();await page.getByRole('button',{name:'Session & results',exact:false}).click();await page.getByRole('button',{name:'Next question'}).waitFor();await page.getByRole('button',{name:'Next question'}).click();
 await page.getByRole('radio').nth(session.questions[1].correct[0]).check();
 await page.getByRole('button',{name:'Check answer'}).click();await page.getByRole('button',{name:'View results'}).click();await page.getByRole('heading',{name:'Every attempt counts.'}).waitFor();
 await page.getByRole('button',{name:'Finish session',exact:true}).click();
 await page.getByRole('button',{name:'Settings & backups',exact:false}).click();
 await page.getByRole('button',{name:'Sync questions now'}).click();
 await page.getByText('Questions are up to date.',{exact:false}).waitFor();
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export progress',exact:true}).click();const download=await downloadPromise;const backup=JSON.parse(await fs.readFile(await download.path(),'utf8'));assert.equal(backup.attempts.length,2);assert(backup.attempts.every(a=>a.correct));
 await page.getByLabel('Java pack directory URL').fill(base+'java-pack/');await page.getByRole('button',{name:'Download / verify pack'}).click();await page.getByText('Java pack installed. Code practice is ready offline.').waitFor();
 await page.evaluate(()=>navigator.serviceWorker.ready);await context.setOffline(true);await page.reload();await page.getByRole('heading',{name:'Small steps. Stronger skills.'}).waitFor();
 const sample=JSON.parse(await fs.readFile('content/samples.json','utf8'));
 const javaQuestion=sample[0].tests[0].questions.find(q=>q.type==='java');
 const javaResult=await page.evaluate(async q=>window.tutorialz.java({question:q,source:q.reference}),javaQuestion);assert(javaResult.passed);await context.setOffline(false);
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/tmp/tutorialz-mobile.png',fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.goto(base+'author/');await page.getByRole('heading',{name:'Good questions start here.'}).waitFor();await page.getByRole('button',{name:'Tests',exact:true}).click();await page.getByRole('button',{name:'1. Which type stores a true/false value?',exact:true}).click();await page.getByRole('button',{name:'Preview question',exact:true}).click();
 await page.getByRole('button',{name:'Check preview answer'}).waitFor();
 await page.screenshot({path:'/tmp/tutorialz-author.png',fullPage:true});
 console.log('PASS: learner grading, reload/resume, results, progress export, offline shell + Java, mobile layout, authoring preview');
 assert.deepEqual(errors,[]);
}finally{await browser.close();}
