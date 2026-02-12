#!/usr/bin/env python3
"""Simple Python scraper for WikiFood.cz 'Kategorie:Bylinky'.
Writes JSON output to data/herbs.json
"""
import json
import time
import re
import unicodedata
from urllib.parse import urljoin, urlparse, unquote
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import os

BASE = 'https://www.wikifood.cz'

def get_crawl_delay():
    try:
        r = requests.get(urljoin(BASE, '/robots.txt'), timeout=5)
        if r.status_code == 200:
            m = re.search(r'(?i)Crawl-delay:\s*(\d+)', r.text)
            if m:
                return int(m.group(1))
    except Exception:
        pass
    return 2

def resolve(href):
    if not href:
        return None
    if href.startswith('//'):
        return 'https:' + href
    if href.startswith('http'):
        return href
    return urljoin(BASE, href)

def normalize_heading(text: str) -> str:
    if not text:
        return ''
    t = text.lower()
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r'\s+', ' ', t).strip()
    mapping = {
        'zdravotní přínosy': 'zdravotni_prinosy',
        'zdravotni přínosy': 'zdravotni_prinosy',
        'skladování': 'skladovani',
        'skladovani': 'skladovani',
        'kde a kdy sbírat': 'kde_kdy_sbirat',
        'kde kdy sbírat': 'kde_kdy_sbirat',
        'použití v kuchyni': 'pouziti_v_kuchyni',
        'použiti v kuchyni': 'pouziti_v_kuchyni',
        'použití': 'pouziti_v_kuchyni',
        'masti': 'masti'
    }
    return mapping.get(t, re.sub(r'[^a-z0-9]+', '_', t).strip('_'))

def first_paragraph(soup: BeautifulSoup) -> str:
    container = soup.select_one('#mw-content-text .mw-parser-output')
    if not container:
        return ''
    for p in container.find_all('p', recursive=False):
        text = p.get_text(strip=True)
        if text:
            return text
    # fallback deeper
    p = container.find('p')
    return p.get_text(strip=True) if p else ''

def parse_herb_page(url: str) -> dict:
    r = requests.get(url, headers={'User-Agent': 'herbar-scraper/0.1'})
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'lxml')
    title_tag = soup.select_one('#firstHeading')
    title = title_tag.get_text(strip=True) if title_tag else url.split('/')[-1]
    summary = first_paragraph(soup)

    # first image anchor
    image_anchor = soup.select_one('#mw-content-text .mw-parser-output a.image')
    thumb_url = None
    image_page = None
    image_file_title = None
    if image_anchor:
        img = image_anchor.find('img')
        if img and img.get('src'):
            thumb_url = resolve(img.get('src'))
        href = image_anchor.get('href')
        if href:
            image_page = resolve(href)
            # extract file title from href like /Soubor:Name.jpg
            # href may be '/Soubor:File_Name.jpg' or similar
            try:
                file_seg = href.split('/')[-1]
                # decode percent-encoding
                image_file_title = unquote(file_seg)
            except Exception:
                image_file_title = None

    # collect sections
    sections = {}
    content_root = soup.select_one('#mw-content-text .mw-parser-output')
    if content_root:
        for heading in content_root.find_all(['h2', 'h3']):
            span = heading.find(class_='mw-headline')
            if not span:
                continue
            key = normalize_heading(span.get_text())
            # gather siblings until next h2/h3
            texts = []
            node = heading.next_sibling
            while node:
                if getattr(node, 'name', None) in ('h2', 'h3'):
                    break
                if getattr(node, 'get_text', None):
                    t = node.get_text(strip=True)
                    if t:
                        texts.append(t)
                node = node.next_sibling
            sections[key] = '\n'.join(texts).strip()

    return {
        'source_url': url,
        'name': title,
        'summary': summary,
        'images': [{'page_url': image_page, 'file_title': image_file_title, 'thumb_url': thumb_url}],
        'sections': sections
    }

def fetch_file_original_url(file_page_url: str):
    if not file_page_url:
        return None
    try:
        r = requests.get(file_page_url, headers={'User-Agent': 'herbar-scraper/0.1'})
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'lxml')
        a = soup.select_one('a[href*="/images/"]')
        if a and a.get('href'):
            return resolve(a.get('href'))
        fb = soup.select_one('.fullImageLink a')
        if fb and fb.get('href'):
            return resolve(fb.get('href'))
    except Exception:
        return None

def fetch_all_herbs():
    cat_url = urljoin(BASE, '/Kategorie:Bylinky')
    delay = get_crawl_delay()
    print('Crawl delay:', delay, 's')
    r = requests.get(cat_url, headers={'User-Agent': 'herbar-scraper/0.1'})
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'lxml')

    links = set()
    # Prefer category member lists under #mw-pages or .mw-category
    container = soup.select_one('#mw-pages') or soup.select_one('.mw-category') or soup.select_one('#mw-content-text .mw-parser-output')
    if container:
        for a in container.select('a[href]'):
            href = a.get('href')
            if not href:
                continue
            # skip namespaces like Soubor:, Kategorie:, Special:
            if re.match(r'^/[^/]+:', href):
                continue
            if href.startswith('/Kategorie'):
                continue
            links.add(resolve(href))
    else:
        # fallback to site-wide anchors
        for a in soup.select('#mw-content-text .mw-parser-output a[href^="/"]'):
            href = a.get('href')
            if not href:
                continue
            if ':' in href:
                continue
            if href.startswith('/Kategorie'):
                continue
            links.add(resolve(href))

    link_list = sorted([u for u in links if u.startswith(BASE + '/')])

    outdir = Path(__file__).resolve().parent.parent / 'data'
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / 'herbs.json'
    logpath = outdir / 'scrape.log'

    def write_log(msg):
        ts = datetime.utcnow().isoformat() + 'Z'
        line = f'[{ts}] {msg}'
        try:
            with open(logpath, 'a', encoding='utf8') as lf:
                lf.write(line + '\n')
        except Exception:
            pass
        print(line)

    # load existing checkpoint into a map by id
    existing = {}
    if outpath.exists():
        try:
            with open(outpath, 'r', encoding='utf8') as f:
                arr = json.load(f)
                for item in arr:
                    if 'id' in item:
                        existing[item['id']] = item
            write_log(f'Loaded existing checkpoint with {len(existing)} records')
        except json.JSONDecodeError:
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            corrupt = outdir / f'herbs.json.corrupt.{ts}'
            try:
                os.replace(outpath, corrupt)
                write_log(f'Corrupt herbs.json moved to {corrupt.name}')
            except Exception as e:
                write_log(f'Failed to backup corrupt herbs.json: {e}')
            existing = {}
        except Exception as e:
            write_log(f'Error loading existing herbs.json: {e}')
            existing = {}

    herbs = list(existing.values())

    def fetch_image_info(file_title):
        if not file_title:
            return None
        params = {
            'action': 'query',
            'titles': f'File:{file_title}',
            'prop': 'imageinfo',
            'iiprop': 'url|size|mime|extmetadata',
            'format': 'json',
            'formatversion': '2'
        }
        for ep in ['/w/api.php', '/api.php']:
            api = urljoin(BASE, ep)
            try:
                r = requests.get(api, params=params, headers={'User-Agent': 'herbar-scraper/0.1'}, timeout=15)
                if r.status_code == 404:
                    continue
                r.raise_for_status()
                j = r.json()
                pages = j.get('query', {}).get('pages', [])
                if pages:
                    p = pages[0]
                    if 'imageinfo' in p and p['imageinfo']:
                        info = p['imageinfo'][0]
                        mm = {}
                        mm['file_url'] = info.get('url')
                        mm['width'] = info.get('width')
                        mm['height'] = info.get('height')
                        mm['size_bytes'] = info.get('size')
                        ext = info.get('extmetadata') or {}
                        lic = None
                        if isinstance(ext, dict):
                            lic_field = ext.get('LicenseShortName') or ext.get('License') or ext.get('Credit')
                            if isinstance(lic_field, dict):
                                lic = lic_field.get('value')
                            else:
                                lic = lic_field
                        mm['license'] = lic
                        return mm
            except Exception as e:
                write_log(f'Error fetching image info for {file_title} via {api}: {e}')
        return None

    def fetch_page_images(page_slug):
        # use MediaWiki API to list images used on a page
        try:
            page_title = unquote(page_slug)
            params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'images',
                'format': 'json',
                'formatversion': '2'
            }
            for ep in ['/w/api.php', '/api.php']:
                api = urljoin(BASE, ep)
                try:
                    r = requests.get(api, params=params, headers={'User-Agent': 'herbar-scraper/0.1'}, timeout=15)
                    if r.status_code == 404:
                        continue
                    r.raise_for_status()
                    j = r.json()
                    pages = j.get('query', {}).get('pages', [])
                    if pages and 'images' in pages[0]:
                        return [img.get('title') for img in pages[0].get('images', [])]
                except Exception as e:
                    write_log(f'Error fetching page images for {page_slug} via {api}: {e}')
            return []
            pages = j.get('query', {}).get('pages', [])
            if pages and 'images' in pages[0]:
                # return list of image titles like 'File:Name.jpg'
                return [img.get('title') for img in pages[0].get('images', [])]
        except Exception as e:
            write_log(f'Error fetching page images for {page_slug}: {e}')
        return []

    def fetch_page_lead_image(page_slug):
        # use pageimages API to get lead image URL (original)
        try:
            page_title = unquote(page_slug)
            params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'pageimages',
                'piprop': 'original',
                'format': 'json',
                'formatversion': '2'
            }
            for ep in ['/w/api.php', '/api.php']:
                api = urljoin(BASE, ep)
                try:
                    r = requests.get(api, params=params, headers={'User-Agent': 'herbar-scraper/0.1'}, timeout=15)
                    if r.status_code == 404:
                        continue
                    r.raise_for_status()
                    j = r.json()
                    pages = j.get('query', {}).get('pages', [])
                    if pages and 'original' in pages[0]:
                        return {'file_url': pages[0]['original'].get('source')}
                except Exception as e:
                    write_log(f'Error fetching lead image for {page_slug} via {api}: {e}')
        except Exception as e:
            write_log(f'Error fetching lead image for {page_slug}: {e}')
        return None

    try:
        for i, url in enumerate(link_list, 1):
            slug = url.split('/')[-1]
            existing_rec = existing.get(slug)
            needs_fetch = True
            if existing_rec:
                imgs = existing_rec.get('images') or []
                if imgs and imgs[0].get('file_url'):
                    write_log(f'SKIP ({i}/{len(link_list)}): {slug} (already has image info)')
                    needs_fetch = False
            if not needs_fetch and existing_rec:
                continue
            try:
                write_log(f'Fetching ({i}/{len(link_list)}): {url}')
                rec = parse_herb_page(url)
                # try to get image info via file_title if available
                if rec.get('images') and rec['images'][0].get('file_title'):
                    info = fetch_image_info(rec['images'][0]['file_title'])
                    if info:
                        rec['images'][0].update(info)
                else:
                    # fallback: try pageimages API (lead image)
                    lead = fetch_page_lead_image(slug)
                    if lead and lead.get('file_url'):
                        rec['images'][0]['file_url'] = lead.get('file_url')
                rec['id'] = slug
                rec['license'] = rec.get('license') or 'CC BY-NC-SA 4.0 (source site)'
                existing[slug] = {**(existing.get(slug) or {}), **rec}
                herbs = list(existing.values())
                tmp = outpath.with_suffix('.json.tmp')
                try:
                    with open(tmp, 'w', encoding='utf8') as f:
                        json.dump(herbs, f, ensure_ascii=False, indent=2)
                    os.replace(tmp, outpath)
                    write_log(f'Checkpoint saved ({len(herbs)} records)')
                    if len(herbs) % 3 == 0:
                        write_log(f'MILESTONE: {len(herbs)} records saved (every 3)')
                except Exception as e:
                    write_log(f'Failed to write checkpoint: {e}')
            except Exception as e:
                write_log(f'Error fetching {url}: {e}')
            time.sleep(delay)
    except KeyboardInterrupt:
        write_log('Interrupted by user — checkpoint saved (if possible). Exiting.')

    return herbs

def main():
    outdir = Path(__file__).resolve().parent.parent / 'data'
    outdir.mkdir(parents=True, exist_ok=True)
    herbs = fetch_all_herbs()
    outpath = outdir / 'herbs.json'
    with open(outpath, 'w', encoding='utf8') as f:
        json.dump(herbs, f, ensure_ascii=False, indent=2)
    print('Wrote', len(herbs), 'records to', outpath)

if __name__ == '__main__':
    main()
