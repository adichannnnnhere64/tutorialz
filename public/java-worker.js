// Isolated worker: no Dioxus/native bridge is passed into this realm.
let load, compiler;
let diagnostics=[];
const javaString = s => JSON.stringify(s).replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
function inputSource(source) {
    // Replace standard input references outside strings/comments. TeaVM has no System.setIn.
    return source.replace(/"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\/\/[^\n]*|\/\*[\s\S]*?\*\/|\b(?:java\s*\.\s*lang\s*\.\s*)?System\s*\.\s*in\b/g, token => /^(?:java|System)\b/.test(token) ? 'TutorialzInput.in' : token);
}
const scanner = `public class TutorialzScanner {
 private final String input; private int pos;
 public TutorialzScanner(java.io.InputStream stream) { StringBuilder b=new StringBuilder();try{int c;while((c=stream.read())!=-1)b.append((char)c);}catch(java.io.IOException e){throw new RuntimeException(e);}input=b.toString(); }
 public TutorialzScanner(String text) { input=text; }
 public boolean hasNext(){int i=pos;while(i<input.length()&&Character.isWhitespace(input.charAt(i)))i++;return i<input.length();}
 public String next(){while(pos<input.length()&&Character.isWhitespace(input.charAt(pos)))pos++;if(pos==input.length())throw new java.util.NoSuchElementException();int start=pos;while(pos<input.length()&&!Character.isWhitespace(input.charAt(pos)))pos++;return input.substring(start,pos);}
 public int nextInt(){return Integer.parseInt(next());} public long nextLong(){return Long.parseLong(next());} public double nextDouble(){return Double.parseDouble(next());}
 public String nextLine(){if(pos==input.length())throw new java.util.NoSuchElementException();int start=pos;while(pos<input.length()&&input.charAt(pos)!=10&&input.charAt(pos)!=13)pos++;String s=input.substring(start,pos);if(pos<input.length()&&input.charAt(pos)==13)pos++;if(pos<input.length()&&input.charAt(pos)==10)pos++;return s;}
 public void close(){}
}`;
self.onmessage = async ({data}) => {
 try {
    if(data.command==='init') {
        ({load}=await import(data.runtime));
        const lib=await load(data.compiler, {noAutoImports:true});
        compiler=lib.exports.createCompiler();
        compiler.onDiagnostic(d=>diagnostics.push(`${d.fileName || ""}:${d.lineNumber || ""} ${d.message}`));
        compiler.setSdk(new Int8Array(data.sdk)); compiler.setTeaVMClasslib(new Int8Array(data.classlib));
        // Submitted code cannot access networking or the host's persistent stores.
        for(const name of ['fetch','indexedDB','caches','WebSocket','XMLHttpRequest','importScripts','BroadcastChannel']) {
            Object.defineProperty(self,name,{value:undefined,configurable:false});
        }
        postMessage({type:'ready'}); return;
    }
    const {source, test, style, template}=data;
    diagnostics=[];
    compiler.clearSourceFiles(); compiler.clearOutputFiles();
    const answer=style==='snippet'?template.replace('{{answer}}',()=>source):source;
    if(/\b(package|native)\s|\b(?:org\.teavm|sun\.|jdk\.)/.test(answer)) throw Error('Packages, native code and runtime interop are outside the offline Java subset.');
    compiler.addSourceFile('Main.java',inputSource(answer).replace(/import\s+java\.util\.Scanner\s*;/g,'').replace(/"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\/\/[^\n]*|\/\*[\s\S]*?\*\/|\b(?:java\.util\.)?Scanner\b/g, token=>token.endsWith('Scanner')?'TutorialzScanner':token));
    compiler.addSourceFile('TutorialzScanner.java',scanner);
    compiler.addSourceFile('TutorialzInput.java',`public class TutorialzInput { public static java.io.InputStream in = new java.io.ByteArrayInputStream(new byte[]{${[...new TextEncoder().encode(test.stdin)].map(n=>n>127?n-256:n).join(",")}}); }`);
    compiler.addSourceFile('TutorialzRunner.java',`public class TutorialzRunner { public static void main(String[] args) throws Exception { ${test.harness || 'Main.main(args);'} } }`);
    let ok=compiler.compile(); if(ok)ok=compiler.generateWebAssembly({outputName:'answer',mainClass:'TutorialzRunner'});
    
    if(!ok) { postMessage({type:'result',passed:false,kind:'compile_error',output:'',diagnostics});return; }
    postMessage({type:'executing'});
    let output='',stderr='',bytes=0;
    const append=(ch,error)=> {bytes+=ch<128?1:ch<2048?2:3;if(bytes>65536)throw Error('Output limit exceeded (64 KiB).');if(error)stderr+=String.fromCharCode(ch);else output+=String.fromCharCode(ch);};
    try {
        const module=await load(compiler.getWebAssemblyOutputFile('answer.wasm'),{noAutoImports:true,installImports(i){i.teavmConsole.putcharStdout=ch=>append(ch,false);i.teavmConsole.putcharStderr=ch=>append(ch,true);}});
        module.exports.main([]);
        const normalize=s=>s.replace(/\r\n?/g,'\n').replace(/\n$/,'');
        postMessage({type:'result',passed:normalize(output)===normalize(test.expected),kind:'executed',output,stderr,diagnostics});
    } catch(e) {postMessage({type:'result',passed:false,kind:'runtime_error',output,diagnostics:[...diagnostics,String(e)]});}
 } catch(e) {postMessage({type:'error',message:String(e)});}
};
