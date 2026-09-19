import {_android} from 'playwright';
const [device]=await _android.devices();if(!device)throw Error('No Android emulator/device.');
console.log('Android:',device.model(),device.serial());
await device.shell('am force-stop com.android.chrome');
const context=await device.launchBrowser({args:['--no-first-run','--disable-fre']});
const page=await context.newPage();
await page.goto('http://10.0.2.2:8765/tests/runtime.html');
const result=await page.evaluate(async()=>{
 const {runJava}=await import('../public/java-runner.js');const manifest=await(await fetch('../public/java-pack/manifest.json')).json();const files={};for(const f of manifest.files)files[f.path]=await(await fetch('../public/java-pack/'+f.path)).arrayBuffer();
 const worker=await(await fetch('../public/java-worker.js')).text();const courses=await(await fetch('../content/samples.json')).json();const results=[];for(const q of courses[0].tests[0].questions.filter(q=>q.type==='java'))results.push({id:q.id,result:await runJava(q,q.reference,files,worker)});return results;
});console.log(JSON.stringify(result,null,2));await context.close();await device.close();if(result.some(r=>!r.result.passed))process.exitCode=1;
