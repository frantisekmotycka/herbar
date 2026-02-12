#!/usr/bin/env python3
"""Download images referenced in data/herbs.json, create thumbnails and manifest.
Writes files to public/images/ and manifest to data/images-manifest.json
Logs progress to data/image-download.log
"""
import json
import os
import re
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
PUBLIC_IMAGES = BASE_DIR / 'public' / 'images'
DATA_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_IMAGES.mkdir(parents=True, exist_ok=True)

LOGPATH = DATA_DIR / 'image-download.log'
MANIFEST = DATA_DIR / 'images-manifest.json'

def log(msg):
    line = f'[{__import__("datetime").datetime.utcnow().isoformat()}Z] {msg}'
    print(line)
    try:
        with open(LOGPATH, 'a', encoding='utf8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def slugify(s):
    s = re.sub(r'[^a-zA-Z0-9_\-]', '_', s)
    return s

def download_image(url):
    try:
        resp = requests.get(url, headers={'User-Agent': 'herbar-image-downloader/0.1'}, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        log(f'Failed to download {url}: {e}')
        return None

def save_image_bytes(content, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)

def make_thumbnail(src_bytes, out_path: Path, max_size=400):
    try:
        img = Image.open(BytesIO(src_bytes))
        img.convert('RGB')
        img.thumbnail((max_size, max_size))
        img.save(out_path, format='WEBP', quality=85)
        return True
    except Exception as e:
        log(f'Failed to create thumbnail {out_path}: {e}')
        return False

def process():
    herbs_path = DATA_DIR / 'herbs.json'
    if not herbs_path.exists():
        log('herbs.json not found; run scraper first')
        return
    with open(herbs_path, 'r', encoding='utf8') as f:
        herbs = json.load(f)

    manifest = {}
    total = 0
    for herb in herbs:
        hid = herb.get('id') or slugify(herb.get('name','unknown'))
        images = herb.get('images') or []
        manifest[hid] = []
        for idx, img in enumerate(images):
            src = img.get('file_url') or img.get('thumb_url')
            if not src:
                log(f'{hid}: no image URL')
                continue
            total += 1
            ext = os.path.splitext(src.split('?')[0])[1].lower() or '.jpg'
            fname = f'{slugify(hid)}_{idx}{ext}'
            out_path = PUBLIC_IMAGES / fname
            if out_path.exists():
                size = out_path.stat().st_size
                try:
                    pil = Image.open(out_path)
                    w,h = pil.size
                except Exception:
                    w=h=None
                manifest[hid].append({
                    'original_url': src,
                    'local_path': str(Path('public/images') / fname),
                    'width': w,
                    'height': h,
                    'size_bytes': size,
                    'license': herb.get('license')
                })
                log(f'{hid}: image already exists {fname}')
                continue

            log(f'{hid}: downloading {src}')
            content = download_image(src)
            if not content:
                continue
            save_image_bytes(content, out_path)
            size = out_path.stat().st_size
            try:
                pil = Image.open(out_path)
                w,h = pil.size
            except Exception:
                w=h=None

            # thumbnail
            thumb_name = f'{slugify(hid)}_{idx}_thumb.webp'
            thumb_path = PUBLIC_IMAGES / thumb_name
            made = make_thumbnail(content, thumb_path)
            manifest_entry = {
                'original_url': src,
                'local_path': str(Path('public/images') / fname),
                'thumb_path': str(Path('public/images') / thumb_name) if made else None,
                'width': w,
                'height': h,
                'size_bytes': size,
                'license': herb.get('license')
            }
            manifest[hid].append(manifest_entry)

    with open(MANIFEST, 'w', encoding='utf8') as mf:
        json.dump(manifest, mf, ensure_ascii=False, indent=2)
    log(f'Done. Processed {total} images. Manifest written to {MANIFEST.name}')

if __name__ == '__main__':
    process()
