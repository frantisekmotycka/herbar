#!/usr/bin/env python3
"""Cleanup image links (keep only Wikipedia/Wikimedia) and remove specific license strings.

Backs up `data/herbs.json` to `data/herbs.json.cleanup.bak`.
"""
from pathlib import Path
import json, shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.cleanup.bak'

def is_wiki_url(u: str) -> bool:
    if not isinstance(u, str):
        return False
    u = u.lower()
    return 'wikipedia.org' in u or 'wikimedia.org' in u

def clean_herbs(data):
    removed_image_links = 0
    removed_license = 0
    for herb in data:
        imgs = herb.get('images') or []
        for img in imgs:
            # keys that may contain links
            for key in ('file_url', 'thumb_url', 'page_url'):
                v = img.get(key)
                if v and not is_wiki_url(v):
                    img[key] = None
                    removed_image_links += 1

        # remove license if it exactly matches or contains the phrase
        lic = herb.get('license')
        if isinstance(lic, str) and 'cc by-nc-sa 4.0' in lic.lower():
            herb.pop('license', None)
            removed_license += 1

    return removed_image_links, removed_license

def main():
    if not DATA.exists():
        print('data/herbs.json not found')
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        data = json.load(f)

    removed_images, removed_licenses = clean_herbs(data)

    out = DATA.with_suffix('.tmp')
    with out.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    out.replace(DATA)

    print(f'Done. Removed {removed_images} non-wiki image links and {removed_licenses} license fields. Backup at {BACKUP}')

if __name__ == '__main__':
    main()
