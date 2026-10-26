# Gazal's Public Service Risk Dashboard — Ubuntu setup

This directory contains the original source files from the uploaded **public-service-risk-dashboard-starter-v2** prototype. Files are preserved under their original relative paths. `AUTHORSHIP.md` attributes the source to Gazal.

## Requirements

- Ubuntu Linux
- Python 3.10 or newer (the pipeline uses modern Python type annotations)
- Internet access to install dependencies with pip the first time
- No IBM BOB credits are required for these local synthetic-data tests

## Install and run

From the repository root:

```bash
cd src/gazal-project
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.main
python -m streamlit run src/dashboard.py
```

If Ubuntu reports that the `venv` module is unavailable, install the matching `python3-venv` system package, then retry. Run the final Streamlit command in its own terminal session; open the local URL it prints (usually http://localhost:8501).

## Scope and verification

This is a deterministic Python and Streamlit demonstration driven by fictional files in `data/`. The five YAML files in `agents/` describe agent responsibilities, but do not themselves establish IBM-hosted autonomous-agent integrations. The local tests cover selected scenarios only and do not validate the separate 12-case dataset from the main repository.

The current repository branch is `gazal-initial-code`; this prototype should be reviewed and tested before merging into `main`.

Never commit credentials, `.env`, or `.venv`; no live government systems or personal data should be used.
