#!/usr/bin/env python3
"""Remove a specific templated sentence from all string fields in data/herbs.json.

Usage: python scripts/remove_template_sentence.py
This script makes a backup at data/herbs.json.bak and writes the cleaned file.
"""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.bak'

TARGET = 'Obrázky jsou pouze ilustrační. Máte vlastní foto receptu? Nahrajte jej pomocí našíaplikace, dostupné pro iOS, iPadOS, macOS a Android.'

def replace_in_obj(o):
    """Recursively replace TARGET in all strings inside o. Return (new_obj, count)."""
    if isinstance(o, str):
        if TARGET in o:
            return o.replace(TARGET, '').strip(), 1
        return o, 0
    if isinstance(o, list):
        total = 0
        new = []
        for v in o:
            nv, c = replace_in_obj(v)
            new.append(nv)
            total += c
        return new, total
    if isinstance(o, dict):
        total = 0
        new = {}
        for k, v in o.items():
            nv, c = replace_in_obj(v)
            new[k] = nv
            total += c
        return new, total
    return o, 0

def main():
    if not DATA.exists():
        print('data/herbs.json not found at', DATA)
        return
    print('Backing up', DATA, '→', BACKUP)
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        data = json.load(f)

    newdata, count = replace_in_obj(data)

    with (DATA.with_suffix('.tmp')).open('w', encoding='utf-8') as f:
        json.dump(newdata, f, ensure_ascii=False, indent=2)
    (DATA.with_suffix('.tmp')).replace(DATA)

    print(f'Done. Replacements made: {count}')

if __name__ == '__main__':
    main()
