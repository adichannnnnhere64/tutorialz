export function normalizeOutput(value) { return value.replace(/\r\n?/g,'\n').replace(/\n$/,''); }
export async function runJava(question, source, files, workerSource, signal, report=()=>{}) {
    if(!files)throw Error('Download the Java pack first.');
    const runtime=URL.createObjectURL(new Blob([files['compiler.wasm-runtime.js']],{type:'text/javascript'}));
    const workerUrl=URL.createObjectURL(new Blob([workerSource],{type:'text/javascript'}));
    let worker=new Worker(workerUrl,{type:'module'});
    let pending, timer;
    const fail=e=> {clearTimeout(timer);if(pending){pending.reject(e);pending=null;}};
    const timeout=ms=>{clearTimeout(timer);timer=setTimeout(()=>{worker.terminate();fail(Error(ms===3000?'Execution timed out (3 seconds).':'Compilation timed out (30 seconds).'));},ms);};
    worker.onerror=e=>fail(Error(e.message || 'Java worker failed.'));
    worker.onmessage=({data})=>{
        if(data.type==='executing'){timeout(3000);report('Running tests…');return;}
        if(data.type==='error'){fail(Error(data.message));return;}
        if(data.type==='ready'||data.type==='result'){clearTimeout(timer);const p=pending;pending=null;p?.resolve(data);}
    };
    const send=data=>new Promise((resolve,reject)=>{pending={resolve,reject};timeout(30000);worker.postMessage(data);});
    const cancel=()=>{worker.terminate();fail(Error('Execution cancelled.'));};
    signal?.addEventListener('abort',cancel,{once:true});
    try {
        if(signal?.aborted)throw Error('Execution cancelled.');
        report('Starting Java compiler…');
        await send({command:'init',runtime,compiler:files['compiler.wasm'],sdk:files['compile-classlib-teavm.bin'],classlib:files['runtime-classlib-teavm.bin']});
        const results=[];
        for(const test of question.cases){
            report(`Compiling: ${test.name}`);
            try{const result=await send({command:'run',source,test,style:question.style,template:question.template});results.push({name:test.name,...result});}
            catch(e){if(signal?.aborted)throw e;if(String(e).includes('Execution timed out')){results.push({name:test.name,passed:false,kind:'timeout',output:'',diagnostics:[String(e)]});break;}throw e;}
        }
        return {passed:results.length===question.cases.length&&results.every(r=>r.passed),results};
    } finally { clearTimeout(timer);worker.terminate();URL.revokeObjectURL(runtime);URL.revokeObjectURL(workerUrl);signal?.removeEventListener('abort',cancel); }
}
