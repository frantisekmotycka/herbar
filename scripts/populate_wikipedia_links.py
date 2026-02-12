#!/usr/bin/env python3
"""Check and populate `wikipedia_url` for herbs in data/herbs.json.

Behavior:
- Reads `data/herbs.json` and for each herb without `wikipedia_url` tries
  candidates on `cs.wikipedia.org` and `en.wikipedia.org` using HEAD (falls
  back to GET if HEAD not allowed).
- Respects `robots.txt` crawl-delay (defaults to 10s if not found).
- Backs up original file to `data/herbs.json.wiki.bak` and writes changes atomically.

Usage:
  python scripts/populate_wikipedia_links.py [--limit N] [--delay S]

Note: Running without `--limit` will check all herbs; obey crawl-delay which
may take ~10s per request (≈ 13 minutes for ~76 herbs).
"""
import argparse
from pathlib import Path
import json, shutil, time, re
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.wiki.bak'

WIKIPEDIA_HOSTS = [
    'https://cs.wikipedia.org/wiki/',
    'https://en.wikipedia.org/wiki/'
]

def get_crawl_delay(site='https://www.wikifood.cz'):
    try:
        r = requests.get(site.rstrip('/') + '/robots.txt', timeout=10)
        txt = r.text
        m = re.search(r'(?i)crawl-delay:\s*(\d+)', txt)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 10

def check_url_exists(session, url):
    try:
        r = session.head(url, allow_redirects=True, timeout=10)
        if r.status_code == 200:
            return True
        # some servers disallow HEAD; try GET for 405/501 or other
        if r.status_code in (405, 501, 400):
            r2 = session.get(url, allow_redirects=True, timeout=10)
            return r2.status_code == 200
        return False
    except requests.RequestException:
        return False

def candidates_for(herb):
    name = herb.get('name') or ''
    slug = herb.get('id') or ''
    def enc(s):
        return requests.utils.requote_uri(s.replace(' ', '_'))
    name_c = enc(name)
    slug_c = enc(slug)
    c = []
    c.append(('cs', WIKIPEDIA_HOSTS[0] + name_c))
    if slug_c != name_c:
        c.append(('cs', WIKIPEDIA_HOSTS[0] + slug_c))
    c.append(('en', WIKIPEDIA_HOSTS[1] + name_c))
    return c

def main(limit=None, override_delay=None):
    if not DATA.exists():
        print('data/herbs.json not found at', DATA)
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        herbs = json.load(f)

    session = requests.Session()
    crawl_delay = override_delay if override_delay is not None else get_crawl_delay()
    print('Using crawl-delay:', crawl_delay, 'seconds')

    to_check = [h for h in herbs if not h.get('wikipedia_url')]
    total = len(to_check)
    print(f'Total herbs to check: {total}')
    checked = 0

    for i, herb in enumerate(to_check):
        if limit and i >= limit:
            break
        candidates = candidates_for(herb)
        found = None
        for lang, url in candidates:
            print(f'Checking {herb.get("name")} -> {url}')
            ok = check_url_exists(session, url)
            if ok:
                found = url
                herb['wikipedia_url'] = url
                print('Found:', url)
                break
            else:
                print('Not found:', url)
            time.sleep(crawl_delay)
        if not found:
            print('No wikipedia page found for', herb.get('name'))
        checked += 1

    # write back
    with (DATA.with_suffix('.tmp')).open('w', encoding='utf-8') as f:
        json.dump(herbs, f, ensure_ascii=False, indent=2)
    (DATA.with_suffix('.tmp')).replace(DATA)
    print(f'Done. Checked {checked} herbs. Backup at {BACKUP}')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=None, help='Limit number of herbs to check')
    p.add_argument('--delay', type=int, default=None, help='Override crawl-delay in seconds')
    args = p.parse_args()
    main(limit=args.limit, override_delay=args.delay)
