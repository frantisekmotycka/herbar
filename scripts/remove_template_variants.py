#!/usr/bin/env python3
from pathlib import Path
import json, shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.variants.bak'

variants = [
    'Obrázky jsou pouze ilustrační. Máte vlastní foto receptu? Nahrajte jej pomocí našíaplikace, dostupné pro iOS, iPadOS, macOS a Android.',
    'Obrázky jsou pouze ilustrační. Máte vlastní foto receptu? Nahrajte jej pomocí naší aplikace, dostupné pro iOS, iPadOS, macOS a Android.',
    'Obrázky jsou pouze ilustrační.',
    'Obrazky jsou pouze ilustracni. Mate vlastni foto receptu? Nahrajte jej pomocí nasiaplikace, dostupne pro iOS, iPadOS, macOS a Android.',
    'Obrazky jsou pouze ilustracni. Mate vlastni foto receptu? Nahrajte jej pomoci nasi aplikace, dostupne pro iOS, iPadOS, macOS a Android.',
    'Obrazky jsou pouze ilustracni.'
]

def replace_in_obj(o):
    if isinstance(o, str):
        s = o
        c = 0
        for v in variants:
            if v in s:
                s = s.replace(v, '').strip()
                c += 1
        return s, c
    if isinstance(o, list):
        total = 0
        new = []
        for v in o:
            nv, tc = replace_in_obj(v)
            new.append(nv)
            total += tc
        return new, total
    if isinstance(o, dict):
        total = 0
        new = {}
        for k, v in o.items():
            nv, tc = replace_in_obj(v)
            new[k] = nv
            total += tc
        return new, total
    return o, 0

def main():
    if not DATA.exists():
        print('no data')
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        data = json.load(f)
    new, count = replace_in_obj(data)
    with (DATA.with_suffix('.tmp')).open('w', encoding='utf-8') as f:
        json.dump(new, f, ensure_ascii=False, indent=2)
    (DATA.with_suffix('.tmp')).replace(DATA)
    print('Replacements made (variants):', count)

if __name__=='__main__':
    main()
