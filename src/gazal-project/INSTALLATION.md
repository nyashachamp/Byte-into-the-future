# Gazal Public Service Risk Dashboard — Ubuntu setup

The uploaded prototype source archive contains `agents/`, `data/`, `src/`, `tests/`, `requirements.txt`, `README.md`, and `AUTHORSHIP.md`. **The full source archive has not yet been committed to this branch.** Do not mistake this documentation for a complete installation.

After the original files are added under `src/gazal-project/`, run from that directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python -m src.main
python -m streamlit run src/dashboard.py
```

This is a synthetic, deterministic local proof of concept. Never commit credentials, `.venv/`, or real government data. Attribution: Gazal provided the original implementation and dashboard; repository commits by other members do not change that attribution.
