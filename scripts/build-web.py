#!/usr/bin/env python3
"""Build both static applications, supporting GitHub Pages repository subpaths."""
import os, pathlib, subprocess, shutil, json, hashlib, gzip
root=pathlib.Path(__file__).resolve().parent.parent
os.chdir(root)
base=os.environ.get('SITE_BASE_PATH','').strip('/')
dx=os.environ.get('DX','dx')
os.environ['PATH']=str(root/'tools/bin')+os.pathsep+os.environ.get('PATH','')
if not shutil.which(dx):
    raise SystemExit('Dioxus CLI not found. Install dioxus-cli 0.7.10 or set DX=/path/to/dx.')
catalog=json.loads((root/'content/enterprise/catalog.json').read_text())
question_count=sum(len(test['questions']) for entry in catalog['courses']
                   for test in json.loads((root/'content/enterprise'/entry['path']).read_text())['tests'])
for app in ['learner','author']:
    path='/'.join(filter(None,[base,'author' if app=='author' else '']))
    subprocess.run([dx,'build','--web','--release','--package',f'tutorialz-{app}','--base-path',path],check=True)
    source=root/'target/dx'/f'tutorialz-{app}'/'release/web/public'
    dest=root/'dist'/('author' if app=='author' else '')
    dest.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,dest,dirs_exist_ok=True)
    index=dest/'index.html'
    html=index.read_text()
    if app=='learner':
        site_url='https://adichannnnnhere64.github.io/'+(base+'/' if base else '')
        metadata=(f'<meta name="description" content="Search {question_count:,} Java, OOP, and Jakarta EE questions and take free practice quizzes.">'
                  f'<link rel="canonical" href="{site_url}">'
                  f'<meta property="og:title" content="Tutorialz · Java and Jakarta EE quizzes">'
                  f'<meta property="og:description" content="Search {question_count:,} Java, OOP, and Jakarta EE practice questions.">'
                  f'<meta property="og:url" content="{site_url}">')
    else:
        metadata='<meta name="robots" content="noindex">'
    index.write_text(html.replace('</head>',metadata+'</head>',1))
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
site_url='https://adichannnnnhere64.github.io/'+(base+'/' if base else '')
(root/'dist/sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{site_url}</loc></url></urlset>\n')
(root/'dist/robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {site_url}sitemap.xml\n')
print('Serve dist/ using an HTTP server; do not open index.html as a file.')
