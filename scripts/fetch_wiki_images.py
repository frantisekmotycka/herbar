#!/usr/bin/env python3
"""Fetch Wikimedia images for herbs and save to public/images.

Behavior:
- For each herb in data/herbs.json, if images[].file_url is null, try cs then en Wikipedia
  to find a page image (original or thumbnail) via the MediaWiki API.
- If an image URL is found, download it to public/images and update the herb image's
  `file_url` to the local path `/images/<filename>` and `thumb_url` to same.
- If no suitable image is found, leave values as null.

Creates a backup at data/herbs.json.fetch_images.bak
"""
from pathlib import Path
import json, shutil, urllib.request, urllib.parse, re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.fetch_images.bak'
OUT_DIR = ROOT / 'public' / 'images'
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIKI_LANGS = ['cs', 'en']
TIMEOUT = 8

def slugify(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip('-')
    return s or 'img'

def query_pageimage(lang, title):
    api = f'https://{lang}.wikipedia.org/w/api.php'
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'pageimages',
        'piprop': 'original|thumbnail',
        'pithumbsize': '800',
        'format': 'json'
    }
    url = api + '?' + urllib.parse.urlencode(params, safe='|')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'herbar-bot/1.0 (https://example.org)'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None

def query_images_list(lang, title):
    api = f'https://{lang}.wikipedia.org/w/api.php'
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'images',
        'imlimit': '50',
        'format': 'json'
    }
    url = api + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'herbar-bot/1.0 (https://example.org)'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None

def get_imageinfo(lang, file_title):
    api = f'https://{lang}.wikipedia.org/w/api.php'
    params = {
        'action': 'query',
        'titles': file_title,
        'prop': 'imageinfo',
        'iiprop': 'url',
        'format': 'json'
    }
    url = api + '?' + urllib.parse.urlencode(params, safe=':')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'herbar-bot/1.0 (https://example.org)'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None

def extract_image_url_from_query(q):
    if not q or 'query' not in q:
        return None
    pages = q['query'].get('pages', {})
    for pid, page in pages.items():
        # prefer original
        if 'original' in page and isinstance(page['original'], dict):
            return page['original'].get('source')
        if 'thumbnail' in page and isinstance(page['thumbnail'], dict):
            return page['thumbnail'].get('source')
    return None

def download_image(url, outpath):
    try:
        headers = {'User-Agent': 'herbar-bot/1.0 (contact)'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        outpath.write_bytes(data)
        return True
    except Exception:
        return False

def ext_from_url(u):
    p = urllib.parse.urlparse(u).path
    m = re.search(r"\.([a-zA-Z0-9]+)(?:$|[?])", p)
    return (m.group(1).lower() if m else 'jpg')

def ensure_unique(path):
    base = Path(path)
    if not base.exists():
        return base
    i = 1
    while True:
        new = base.with_name(f"{base.stem}-{i}{base.suffix}")
        if not new.exists():
            return new
        i += 1

def main():
    if not DATA.exists():
        print('data/herbs.json not found')
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        herbs = json.load(f)

    downloaded = 0
    updated_entries = 0
    print('Starting fetch_wiki_images; herbs to check:', len(herbs))
    for herb in herbs:
        print('Checking:', herb.get('name'))
        imgs = herb.get('images') or []
        if not imgs:
            continue
        # check first image slot
        img = imgs[0]
        if img.get('file_url'):
            continue

        name = herb.get('name') or herb.get('id')
        title_candidate = urllib.parse.quote(name.replace(' ', '_'))
        found = None
        for lang in WIKI_LANGS:
            q = query_pageimage(lang, name.replace(' ', '_'))
            u = extract_image_url_from_query(q)
            if u:
                found = u
                img['page_url'] = f'https://{lang}.wikipedia.org/wiki/{title_candidate}'
                break
            # fallback: list images on the page and query imageinfo for a suitable file
            li = query_images_list(lang, name.replace(' ', '_'))
            if li and 'query' in li and 'pages' in li['query']:
                pages = li['query']['pages']
                for pid, page in pages.items():
                    for im in page.get('images', []) if isinstance(page.get('images', []), list) else []:
                        title = im.get('title')
                        if not title: 
                            continue
                        if re.search(r"\.(jpg|jpeg|png|svg)$", title, flags=re.I):
                            info = get_imageinfo(lang, title)
                            if info and 'query' in info and 'pages' in info['query']:
                                iu = extract_image_url_from_query(info)
                                if iu:
                                    found = iu
                                    img['page_url'] = f'https://{lang}.wikipedia.org/wiki/{title_candidate}'
                                    break
                    if found:
                        break
            if found:
                break

        if not found:
            # leave null
            continue

        ext = ext_from_url(found)
        filename = f"{slugify(name)}.{ext}"
        outpath = OUT_DIR / filename
        outpath = ensure_unique(outpath)
        ok = download_image(found, outpath)
        if not ok:
            continue

        # set local URLs (served by next.js from /public)
        local_url = f"/images/{outpath.name}"
        img['file_url'] = local_url
        img['thumb_url'] = local_url
        downloaded += 1
        updated_entries += 1

    # write back
    with DATA.with_suffix('.tmp').open('w', encoding='utf-8') as f:
        json.dump(herbs, f, ensure_ascii=False, indent=2)
    DATA.with_suffix('.tmp').replace(DATA)

    print(f'Downloaded images: {downloaded}, updated entries: {updated_entries}. Backup at {BACKUP}')

if __name__ == '__main__':
    main()
