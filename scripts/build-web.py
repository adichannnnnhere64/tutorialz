#!/usr/bin/env python3
"""Build both static applications, supporting GitHub Pages repository subpaths."""
import os, pathlib, subprocess, shutil, json, hashlib, gzip
root=pathlib.Path(__file__).resolve().parent.parent
os.chdir(root)
base=os.environ.get('SITE_BASE_PATH','').strip('/')
dx=os.environ.get('DX','dx')
for app in ['learner','author']:
    path='/'.join(filter(None,[base,'author' if app=='author' else '']))
    subprocess.run([dx,'build','--web','--release','--package',f'tutorialz-{app}','--base-path',path],check=True)
    source=root/'target/dx'/f'tutorialz-{app}'/'release/web/public'
    dest=root/'dist'/('author' if app=='author' else '')
    dest.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,dest,dirs_exist_ok=True)
    # An exact build manifest avoids caching partial shells or stale assets.
    files=[p for p in source.rglob('*') if p.is_file()]
    names=['./'+str(p.relative_to(source)) for p in files]
    version=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(files))).hexdigest()[:16]
    sw=f"const CACHE='tutorialz-{app}-{version}';const FILES={json.dumps(names)};\n"+(root/'public/sw-template.js').read_text()
    (dest/'sw.js').write_text(sw)
    size=sum(p.stat().st_size for p in files)
    compressed=sum(len(gzip.compress(p.read_bytes())) for p in files)
    print(f'{app}: {size:,} bytes uncompressed; {compressed:,} bytes gzip (all build files)')
shutil.copytree(root/'public/java-pack',root/'dist/java-pack',dirs_exist_ok=True)
shutil.copytree(root/'content',root/'dist/content',dirs_exist_ok=True)
(root/'dist/.nojekyll').write_text('')
print('Serve dist/ using an HTTP server; do not open index.html as a file.')
