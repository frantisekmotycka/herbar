#!/usr/bin/env python3
"""Populate missing `summary` and `sections` in data/herbs.json with simple templates.

Creates a backup at data/herbs.json.allfilled.bak and reports how many entries were updated.
"""
from pathlib import Path
import json, shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'herbs.json'
BACKUP = ROOT / 'data' / 'herbs.json.allfilled.bak'

def make_summary(name):
    return f"{name} je běžná bylinka či koření; základní informace o použití, pěstování a sběru."

def make_sections(name):
    return {
        "Popis": f"{name} — stručný popis: vzhled, typ rostliny a typické vlastnosti.",
        "Použití": "Kulinářské a tradiční použití (čaje, koření, léčitelství). Používejte s ohledem na bezpečnost.",
        "Pěstování": "Obecné rady: slunné až polostinné stanoviště, propustná půda; uložte specifika podle druhu.",
        "Sběr": "Sběr listů/květů/semen v optimální fázi — obvykle před nebo během kvetení; sušte rychle ve stínu."
    }

def main():
    if not DATA.exists():
        print('data/herbs.json not found')
        return
    shutil.copy2(DATA, BACKUP)
    with DATA.open('r', encoding='utf-8') as f:
        data = json.load(f)

    changed_summary = 0
    changed_sections = 0

    for herb in data:
        name = herb.get('name') or herb.get('id') or 'Bylinka'
        summary = herb.get('summary')
        if not isinstance(summary, str) or not summary.strip():
            herb['summary'] = make_summary(name)
            changed_summary += 1

        sections = herb.get('sections')
        if not isinstance(sections, dict) or not sections:
            herb['sections'] = make_sections(name)
            changed_sections += 1

    out_path = DATA.with_suffix('.tmp')
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    out_path.replace(DATA)

    print(f'Done. Summaries added: {changed_summary}, Sections added: {changed_sections}. Backup at {BACKUP}')

if __name__ == '__main__':
    main()
