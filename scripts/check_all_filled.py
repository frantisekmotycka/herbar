#!/usr/bin/env python3
from pathlib import Path
import json

DATA = Path('data') / 'herbs.json'
if not DATA.exists():
    print('data/herbs.json not found')
    raise SystemExit(1)

js = json.loads(DATA.read_text(encoding='utf-8'))
total = len(js)
missing_summary = [h.get('name') for h in js if not (isinstance(h.get('summary'), str) and h.get('summary').strip())]
missing_sections = [h.get('name') for h in js if not (isinstance(h.get('sections'), dict) and h.get('sections'))]

print(total)
print(len(missing_summary))
print(len(missing_sections))
if missing_summary:
    print('examples_missing_summary:', missing_summary[:10])
if missing_sections:
    print('examples_missing_sections:', missing_sections[:10])
