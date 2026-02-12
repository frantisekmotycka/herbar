#!/usr/bin/env python3
"""Populate empty `summary` fields in data/herbs.json by extracting
the first paragraph from available `sections` content.

Backs up `data/herbs.json` to `data/herbs.json.populate.bak`.
"""
from pathlib import Path
import json, shutil, re
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.populate.bak'

def strip_tags(html):
    # remove tags
    text = re.sub(r'<[^>]+>', '', html)
    # collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return unescape(text).strip()

def first_paragraph_from_html(html):
    if not html:
        return ''
    # try to grab first <p>..</p>
    m = re.search(r'<p[^>]*>(.*?)</p>', html, flags=re.I|re.S)
    if m:
        return strip_tags(m.group(1))
    # else split by double newlines or <br>
    parts = re.split(r'(?:<br\s*/?>|\n\s*\n)', html, flags=re.I)
    for p in parts:
        t = strip_tags(p)
        if len(t) > 20:
            # truncate to reasonable length
            return t if len(t) <= 400 else (t[:397].rstrip() + '...')
    # fallback: strip all and take first sentence
    alltext = strip_tags(html)
    if not alltext:
        return ''
    # split into sentences naively
    s = re.split(r'(?<=[.!?])\s+', alltext)
    first = s[0]
    return first if len(first) <= 400 else (first[:397].rstrip() + '...')

def replace_summaries(data):
    changed = 0
    for herb in data:
        summary = herb.get('summary') or ''
        if isinstance(summary, str) and summary.strip():
            continue
        sections = herb.get('sections') or {}
        # find first meaningful section content
        # prefer Popis/Vzhled/Popis a vzhled etc.
        keys = list(sections.keys())
        preferred = ['Popis', 'Vzhled', 'Popis a vzhled', 'Popis a použití', 'Úvod']
        candidate = None
        for k in preferred:
            for real in keys:
                if k.lower() in real.lower():
                    candidate = sections.get(real)
                    break
            if candidate:
                break
        if not candidate and keys:
            # pick the first non-empty section
            for real in keys:
                val = sections.get(real)
                if isinstance(val, str) and val.strip():
                    candidate = val
                    break
        if candidate:
            para = first_paragraph_from_html(candidate)
            if para:
                herb['summary'] = para
                changed += 1
    return changed

def main():
    if not DATA.exists():
        print('data/herbs.json not found')
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        data = json.load(f)
    changed = replace_summaries(data)
    with (DATA.with_suffix('.tmp')).open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    (DATA.with_suffix('.tmp')).replace(DATA)
    print(f'Done. Summaries populated for {changed} herbs. Backup at {BACKUP}')

if __name__ == '__main__':
    main()
