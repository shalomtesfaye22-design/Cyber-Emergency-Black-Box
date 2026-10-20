# Repository Guidelines

## Project Structure & Module Organization

This repository has a documentation layer at the root and the Python application in
`Cyber Emergency Black Box/`. Work from that directory for application commands.
`backend/` contains the FastAPI service, domain models, collectors, correlation rules,
database code, reporting, and configuration. Put synthetic demo scenarios in
`simulator/`; place tests in `tests/`; use `scripts/` for maintenance utilities; and
keep design and requirements material in `docs/`. Generated `data/` databases and
`evidence/` packages are intentionally ignored by Git.

## Build, Test, and Development Commands

```powershell
cd 'Cyber Emergency Black Box'
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/init_db.py
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pytest
```

The initialization script creates the local SQLite store. Run the server only on
`127.0.0.1`; `pytest` uses the configured test suite and verbose short tracebacks.

## Coding Style & Naming Conventions

Use Python 3.11+ with four-space indentation, standard-library imports first, and
type hints for public functions. Follow the existing `snake_case` for modules,
functions, settings, and fixtures; use `PascalCase` for classes. Keep backend modules
focused by layer (for example, `backend/correlation/rules/account_compromise.py`).
Add concise docstrings to public classes and functions. No formatter or linter is
currently configured; preserve the surrounding style and avoid unrelated rewrites.

## Testing Guidelines

Write pytest tests as `tests/test_<feature>.py`, with test functions named
`test_<behavior>`. Use the async fixtures in `tests/conftest.py` for database work;
they create a fresh in-memory SQLite database per test. Cover normal behavior,
boundary conditions, and rule-triggering evidence sequences. Run `pytest` before
opening a pull request.

## Commit & Pull Request Guidelines

Existing history uses short imperative subjects such as `First commit`; continue with
clear summaries like `Add process correlation rule`. Keep commits narrowly scoped.
Pull requests should explain the operational impact, list test commands and results,
link relevant issues or task documents, and include dashboard screenshots when UI
behavior changes.

## Security & Configuration

Never commit `.env`, `secrets.json`, databases, evidence, or endpoint-derived logs.
Configuration belongs in `backend/config.py` and environment overrides, not hard-coded
secrets. Collect or simulate activity only on systems you own or are authorized to
monitor.
