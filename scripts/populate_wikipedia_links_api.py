#!/usr/bin/env python3
"""Populate `wikipedia_url` for herbs using Wikipedia search API (fuzzy matching).

This script queries the MediaWiki API (cs.wikipedia.org then en.wikipedia.org)
using `action=query&list=search` to find the best-matching page for each herb.
It is faster and more robust than checking raw page responses.

Usage:
  python scripts/populate_wikipedia_links_api.py [--limit N] [--delay S]

Defaults:
  --limit: None (process all)
  --delay: 1 (seconds between API queries to avoid throttling)

Backups the original file to `data/herbs.json.wiki_api.bak`.
"""
import argparse
from pathlib import Path
import json, shutil, time, unicodedata, re
import requests
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.wiki_api.bak'

WIKI_APIS = [
    ('cs', 'https://cs.wikipedia.org/w/api.php'),
    ('en', 'https://en.wikipedia.org/w/api.php'),
]

def search_wikipedia(session, api_url, query, limit=3):
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srlimit': limit,
        'format': 'json'
    }
    try:
        r = session.get(api_url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get('query', {}).get('search', [])
    except Exception:
        return []

def best_candidate_from_search(results, name):
    if not results:
        return None
    # pick candidate by simple heuristics: exact title match, title contains name tokens, else top
    name_norm = (name or '').strip().lower()
    name_no_diac = strip_diacritics(name_norm)
    for item in results:
        title = (item.get('title') or '').strip()
        tnorm = title.lower()
        if tnorm == name_norm or strip_diacritics(tnorm) == name_no_diac:
            return title
    # look for title containing any important token
    tokens = [t for t in re_split_tokens(name_norm) if len(t) > 2]
    for item in results:
        title = (item.get('title') or '').strip()
        tnorm = title.lower()
        for tk in tokens:
            if tk in tnorm or strip_diacritics(tnorm).find(strip_diacritics(tk)) != -1:
                return title
    return results[0].get('title')

def strip_diacritics(s):
    if not s:
        return s
    nkfd = unicodedata.normalize('NFKD', s)
    return ''.join([c for c in nkfd if not unicodedata.combining(c)])

def re_split_tokens(s):
    return [p for p in re.split(r"[^\w]+", s) if p]

def main(limit=None, delay=1):
    if not DATA.exists():
        print('data/herbs.json not found')
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        herbs = json.load(f)

    session = requests.Session()
    # set a polite User-Agent so Wikimedia APIs don't reject requests
    session.headers.update({'User-Agent': 'herbar-bot/1.0 (+https://example.org) python-requests'})
    to_check = [h for h in herbs if not h.get('wikipedia_url')]
    total = len(to_check)
    print(f'Total herbs to check via API: {total}')
    processed = 0

    for i, herb in enumerate(to_check):
        if limit and i >= limit:
            break
        name = herb.get('name') or ''
        if not name:
            continue
        found_url = None
        # build query variants
        variants = [name]
        nd = strip_diacritics(name)
        if nd and nd != name:
            variants.append(nd)
        # tokens
        toks = re_split_tokens(name)
        if toks:
            if len(toks) > 1:
                variants.append(' '.join(toks[:2]))
            variants.append(toks[0])

        # try each wiki API and each variant
        for lang, api in WIKI_APIS:
            for q in variants:
                results = search_wikipedia(session, api, q, limit=5)
                title = best_candidate_from_search(results, name)
                if title:
                    url = f'https://{lang}.wikipedia.org/wiki/' + quote_plus(title.replace(' ', '_'))
                    herb['wikipedia_url'] = url
                    herb.setdefault('wikipedia_match', {})
                    herb['wikipedia_match'].update({'lang': lang, 'title': title, 'query': q})
                    found_url = url
                    print(f'Found {herb.get("name")} → {url} (query={q})')
                    break
                time.sleep(delay)
            if found_url:
                break
        if not found_url:
            print('No match for', herb.get('name'))
        processed += 1
        # pause between herbs
        time.sleep(delay)

    with (DATA.with_suffix('.tmp')).open('w', encoding='utf-8') as f:
        json.dump(herbs, f, ensure_ascii=False, indent=2)
    (DATA.with_suffix('.tmp')).replace(DATA)
    print(f'Done. Processed {processed} herbs. Backup: {BACKUP}')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--delay', type=float, default=1.0)
    args = p.parse_args()
    main(limit=args.limit, delay=args.delay)
