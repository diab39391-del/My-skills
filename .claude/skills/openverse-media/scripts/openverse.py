"""Search Openverse (openly licensed audio and images) and download picks with their credits.

usage:
  python3 openverse.py search audio "whoosh" [--license cc0] [--commercial] [--max-sec 3] [-n 20]
  python3 openverse.py search images "kids classroom illustration" --license cc0,by --commercial
  python3 openverse.py get audio ID [ID ...] --out sfx/          # downloads + appends sfx/CREDITS.md and credits.json

Anonymous API (rate-limited). Needs network access to api.openverse.org and to the file's host
(freesound, jamendo, wikimedia... the `url` field shows which).
"""
import argparse, json, os, sys, urllib.parse, urllib.request

API = 'https://api.openverse.org/v1'
UA = {'User-Agent': 'openverse-media-skill/1.0'}


def call(path, params=None):
    url = f'{API}/{path}' + ('?' + urllib.parse.urlencode(params) if params else '')
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def search(a):
    kind = 'images' if a.kind.startswith('image') else 'audio'
    p = {'q': a.query, 'page_size': a.n}
    if a.license: p['license'] = a.license
    if a.commercial: p['license_type'] = 'commercial'
    if kind == 'audio' and a.max_sec: p['length'] = 'shortest' if a.max_sec <= 30 else 'short'
    res = call(f'{kind}/', p).get('results', [])
    for r in res:
        dur = r.get('duration')
        if a.max_sec and dur and dur / 1000 > a.max_sec: continue
        d = f"{dur / 1000:5.1f}s" if dur else '     '
        print(f"{r['id']}  {d}  {r.get('license', '?'):6} {r.get('license_version') or '':4} {(r.get('title') or '')[:48]:48}  by {(r.get('creator') or '?')[:24]}  [{r.get('source')}]")
    if not res: print('no results')


def get(a):
    kind = 'images' if a.kind.startswith('image') else 'audio'
    os.makedirs(a.out, exist_ok=True)
    cj = os.path.join(a.out, 'credits.json')
    credits = json.load(open(cj)) if os.path.exists(cj) else []
    for i in a.ids:
        r = call(f'{kind}/{i}/')
        ext = (r.get('filetype') or os.path.splitext(urllib.parse.urlparse(r['url']).path)[1].lstrip('.') or 'bin')
        name = f"{(r.get('title') or i)[:40]}".strip().replace('/', '_').replace(' ', '_') + f'_{i[:8]}.{ext}'
        dst = os.path.join(a.out, name)
        with urllib.request.urlopen(urllib.request.Request(r['url'], headers=UA), timeout=60) as src, open(dst, 'wb') as f:
            f.write(src.read())
        entry = {'file': name, 'id': i, 'title': r.get('title'), 'creator': r.get('creator'), 'license': r.get('license'),
                 'license_version': r.get('license_version'), 'license_url': r.get('license_url'),
                 'landing': r.get('foreign_landing_url'), 'attribution': r.get('attribution')}
        credits = [c for c in credits if c.get('id') != i] + [entry]
        print('saved', dst, '|', r.get('license'), r.get('license_version') or '')
    json.dump(credits, open(cj, 'w'), ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'CREDITS.md'), 'w') as f:
        f.write('# Credits\n\n')
        for c in credits:
            f.write(f"- {c['file']}: {c.get('attribution') or (str(c.get('title')) + ' by ' + str(c.get('creator')))}\n")
    print('credits ->', os.path.join(a.out, 'CREDITS.md'))


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest='cmd', required=True)
s = sp.add_parser('search'); s.add_argument('kind'); s.add_argument('query')
s.add_argument('--license', default='cc0'); s.add_argument('--commercial', action='store_true')
s.add_argument('--max-sec', type=float, default=0); s.add_argument('-n', type=int, default=20)
g = sp.add_parser('get'); g.add_argument('kind'); g.add_argument('ids', nargs='+'); g.add_argument('--out', default='media')
a = ap.parse_args()
try:
    search(a) if a.cmd == 'search' else get(a)
except OSError as e:
    sys.exit(f'network error: {e}. Is api.openverse.org (and the file host) allowed in this environment?')
