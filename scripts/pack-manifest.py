from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent.parent/'public/java-pack'
names=['compiler.wasm','compiler.wasm-runtime.js','compile-classlib-teavm.bin','runtime-classlib-teavm.bin']
files=[dict(path=n,size=(root/n).stat().st_size,sha256=hashlib.sha256((root/n).read_bytes()).hexdigest()) for n in names]
(root/'manifest.json').write_text(json.dumps(dict(version='teavm-playground-2025-06-15',files=files),indent=2)+'\n')
