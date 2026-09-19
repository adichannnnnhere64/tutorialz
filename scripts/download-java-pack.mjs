import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../public/java-pack/',import.meta.url);
const manifest=JSON.parse(await fs.readFile(new URL('manifest.json',root)));
for(const file of manifest.files){
 const response=await fetch(`https://teavm.org/playground/${file.path}`);if(!response.ok)throw Error(`${response.status}: ${file.path}`);
 const bytes=Buffer.from(await response.arrayBuffer());
 if(createHash('sha256').update(bytes).digest('hex')!==file.sha256)throw Error(`Upstream changed ${file.path}; review before updating pinned hashes.`);
 await fs.writeFile(new URL(file.path,root),bytes);console.log(`${file.path}: ${bytes.length} bytes verified`);
}
