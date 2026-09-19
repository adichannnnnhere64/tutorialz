import { chromium } from 'playwright';
import fs from 'node:fs/promises';
const browser=await chromium.launch({executablePath:process.env.CHROME_BIN || '/etc/profiles/per-user/adrian/bin/google-chrome-stable',headless:true,args:['--no-sandbox']});
const page=await browser.newPage();page.on('pageerror',e=>console.error('PAGE ERROR',e));
await page.goto(process.env.TEST_URL || 'http://127.0.0.1:8765/tests/runtime.html');
const result=await page.evaluate(async()=>{
 const {runJava}=await import('../public/java-runner.js');
 const names=['compiler.wasm','compiler.wasm-runtime.js','compile-classlib-teavm.bin','runtime-classlib-teavm.bin'];const files={};
 for(const name of names) files[name]=await (await fetch('../public/java-pack/'+name)).arrayBuffer();
 const worker=await (await fetch('../public/java-worker.js')).text();
 const courses=await(await fetch('../content/samples.json')).json();const results=[];
 for(const q of courses[0].tests[0].questions.filter(q=>q.type==='java')){const start=performance.now();results.push({id:q.id,result:await runJava(q,q.reference,files,worker),ms:performance.now()-start});}
 return results;
});console.log(JSON.stringify(result,null,2));await browser.close();if(result.some(r=>!r.result.passed))process.exitCode=1;
