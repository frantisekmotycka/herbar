#!/usr/bin/env python3
"""Improved Google-based Wikipedia finder.

For each herb, tries queries in order:
  1) "{name} wiki" (original name)
  2) "{name_without_diacritics} wiki" (normalized)

For each query it examines the first 5 Google results and selects the first
Wikipedia link found. If none found for both queries, leaves wikipedia_url empty.

Use --limit to test only a subset.
"""
from pathlib import Path
import argparse, time, json, shutil, unicodedata
import requests, re
from urllib.parse import quote_plus, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.google.improved.bak'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36'

def strip_diacritics(s):
    nkfd = unicodedata.normalize('NFKD', s)
    return ''.join([c for c in nkfd if not unicodedata.combining(c)])

def extract_google_results(html, max_results=5):
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

def find_wikipedia_for_query(session, query):
    q = quote_plus(query)
    url = f'https://www.google.com/search?q={q}&num=5'
    headers = {'User-Agent': UA, 'Accept-Language': 'cs,en;q=0.9'}
    r = session.get(url, headers=headers, timeout=10)
    html = r.text
    if 'detected unusual traffic' in html or 'Our systems have detected unusual traffic' in html:
        return {'error': 'blocked', 'found': None}
    results = extract_google_results(html, max_results=5)
    for u in results:
        if is_wikipedia_url(u):
            return {'error': None, 'found': u}
    return {'error': None, 'found': None}

def main(limit=None, delay=1.0):
    if not DATA.exists():
        print('data/herbs.json not found')
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        herbs = json.load(f)

    session = requests.Session()
    to_check = [h for h in herbs if not h.get('wikipedia_url')]
    print('To check:', len(to_check))
    processed = 0

    for i, herb in enumerate(to_check):
        if limit and i >= limit:
            break
        name = herb.get('name') or herb.get('id') or ''
        queries = [f'{name} wiki']
        norm = strip_diacritics(name)
        if norm and norm != name:
            queries.append(f'{norm} wiki')

        found = None
        for q in queries:
            print(f'[{i+1}] searching: {q}')
            res = find_wikipedia_for_query(session, q)
            if res['error'] == 'blocked':
                print('Google blocked, aborting.')
                return
            if res['found']:
                print('Found:', res['found'])
                herb['wikipedia_url'] = res['found']
                found = res['found']
                break
            else:
                print('No Wikipedia in first 5 for query:', q)
            time.sleep(delay)

        processed += 1
        time.sleep(delay)

    with (DATA.with_suffix('.tmp')).open('w', encoding='utf-8') as f:
        json.dump(herbs, f, ensure_ascii=False, indent=2)
    (DATA.with_suffix('.tmp')).replace(DATA)
    print('Done. Processed', processed, 'items. Backup at', BACKUP)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--delay', type=float, default=1.0)
    args = p.parse_args()
    main(limit=args.limit, delay=args.delay)
