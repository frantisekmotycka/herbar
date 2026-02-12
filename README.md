# Herbář — MVP

Repo scaffold for the Herbář web app. Contains a server-side scraper that exports a structured JSON dataset from WikiFood.cz category "Bylinky" and a place for a Next.js frontend.

Quick start

1. Install deps:

```powershell
Python 3.10+ recommended. Create a virtualenv and install Python deps:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run scraper (respects robots.txt, be patient):

```powershell
python scripts/fetch_herbs.py
```

Outputs: `data/herbs.json` and `data/images-manifest.json` (when scraper is extended).

License: respect CC BY-NC-SA content from source; verify image licenses individually.
