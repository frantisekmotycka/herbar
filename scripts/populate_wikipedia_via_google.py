#!/usr/bin/env python3
"""Populate `wikipedia_url` in data/herbs.json by using Google search "<name> wiki".

Behavior:
- For each herb without `wikipedia_url`, query Google search page for "{name} wiki".
- Parse the first 5 results and choose the first Wikipedia link (cs or en).
- If none of the first 5 are Wikipedia, leaves the field empty.
- Adds a backup `data/herbs.json.google.bak` and writes changes atomically.

Usage:
  python scripts/populate_wikipedia_via_google.py --limit 10 --delay 1

Notes:
- This scrapes Google search HTML and tries to mimic a browser. If Google blocks requests
  (captcha, unusual traffic), the script will stop and report the issue.
"""
from pathlib import Path
import time, json, shutil, argparse, re
import requests
from urllib.parse import quote_plus, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.google.bak'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36'

def extract_google_results(html, max_results=5):
    # Google search result links appear as /url?q=<URL>&sa=...
    pattern = re.compile(r'/url\?q=(https?://[^&"\']+)', re.I)
    found = pattern.findall(html)
    out = []
    for u in found:
        u = unquote(u)
        out.append(u)
        if len(out) >= max_results:
            break
    return out

def is_wikipedia_url(url):
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        return host.endswith('wikipedia.org')
    except Exception:
        return False

def find_wikipedia_in_google(session, query, delay=1):
    q = quote_plus(query + ' wiki')
    url = f'https://www.google.com/search?q={q}&num=5'
    headers = {'User-Agent': UA, 'Accept-Language': 'cs,en;q=0.9'}
    try:
        r = session.get(url, headers=headers, timeout=10)
    except Exception as e:
        return {'error': str(e), 'found': None}

    html = r.text
    # quick check for blocking
    if 'Our systems have detected unusual traffic' in html or 'detected unusual traffic' in html:
        return {'error': 'Google blocked automated requests (captcha)', 'found': None}

    results = extract_google_results(html, max_results=5)
    for u in results:
        if is_wikipedia_url(u):
            return {'error': None, 'found': u}

    return {'error': None, 'found': None}

def main(limit=None, delay=1):
    if not DATA.exists():
        print('data/herbs.json not found at', DATA)
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        herbs = json.load(f)

    session = requests.Session()
    processed = 0
    to_check = [h for h in herbs if not h.get('wikipedia_url')]
    print('Total to check via Google:', len(to_check))

    for i, herb in enumerate(to_check):
        if limit and i >= limit:
            break
        name = herb.get('name') or herb.get('id') or ''
        print(f'[{i+1}] Searching Google for: {name}')
        res = find_wikipedia_in_google(session, name, delay=delay)
        if res['error']:
            print('Error:', res['error'])
            print('Stopping to avoid further blocking.')
            break
        if res['found']:
            print('Found Wikipedia link:', res['found'])
            herb['wikipedia_url'] = res['found']
        else:
            print('No Wikipedia in first 5 results for', name)
        processed += 1
        time.sleep(delay)

    with (DATA.with_suffix('.tmp')).open('w', encoding='utf-8') as f:
        json.dump(herbs, f, ensure_ascii=False, indent=2)
    (DATA.with_suffix('.tmp')).replace(DATA)
    print(f'Done. Processed {processed} herbs (limited). Backup at {BACKUP}')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--delay', type=float, default=1.0)
    args = p.parse_args()
    main(limit=args.limit, delay=args.delay)
