import {_android} from 'playwright';import assert from 'node:assert/strict';
const [device]=await _android.devices();if(!device)throw Error('No Android device');
try{
 const webview=await device.webView({pkg:'dev.tutorialz.learner'});const page=await webview.page();page.setDefaultTimeout(30000);console.log('WebView',await page.evaluate(()=>({url:location.href,secure:isSecureContext,crypto:!!crypto.subtle}))); page.on('pageerror',e=>console.error(e));await page.getByRole('button',{name:'Settings & backups',exact:false}).waitFor();
 await page.getByRole('button',{name:'Settings & backups',exact:false}).click();await page.getByLabel('Java pack directory URL').fill('http://10.0.2.2:8767/public/java-pack/');await page.getByRole('button',{name:'Download / verify pack'}).click();await page.getByText('Java pack installed. Code practice is ready offline.').waitFor({timeout:60000});
 const result=await page.evaluate(async()=>{const courses=await(await fetch('http://10.0.2.2:8767/content/samples.json')).json();const out=[];for(const q of courses[0].tests[0].questions.filter(q=>q.type==='java'))out.push(await window.tutorialz.java({question:q,source:q.reference}));return out;});assert(result.every(r=>r.passed));
 await page.getByRole('button',{name:'Export progress',exact:true}).click();
 await page.screenshot({path:'/tmp/tutorialz-android.png',fullPage:true});
 console.log('PASS: native Android UI, Java pack install, both Java exercise styles, export clicked');
}finally{await device.close();}
