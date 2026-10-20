# Cyber Emergency Black Box — Project Guide

## Purpose

Cyber Emergency Black Box is a local, single-host digital-forensics and incident
response prototype. It records security-relevant endpoint metadata, detects
explainable suspicious sequences, preserves tamper-evident evidence, and presents
results locally. It is not an antivirus, EDR, SIEM, attack tool, or production
forensic platform. Use it only on endpoints you own or are authorised to monitor.

The application lives in `Cyber Emergency Black Box/`; root Markdown files are
planning, status, and handoff material. The primary specification is in the nested
`docs/requirements.md` and `docs/design.md`.

## Architecture and Data Flow

```text
Collectors / Simulator
        ↓ normalised event
SQLite events table
        ↓ bounded correlation window
Incident + linked events
        ↓
Interpreter + Evidence Manager
        ↓
REST API / HTML report / dashboard
```

Events are timestamped UTC records with a UUID, event type, source, optional user,
process, file/network metadata, severity, SHA-256 raw-event hash, simulation flag,
and preservation flag. Incident evidence is written once under
`evidence/incident_INC-YYYYMMDD-XXXX/`; never edit a generated evidence package.

## Team Ownership

- Antigravity owns `backend/database/`, `backend/services/`, `backend/api/`,
  `backend/main.py`, and the test suite.
- Cursor owns `backend/collectors/`.
- Codex owns `backend/correlation/`, `backend/evidence/`, `backend/interpreter/`,
  `backend/reports/`, and `simulator/`.

Do not modify another owner’s area without coordinating first. The worktree is shared
and currently contains concurrent, uncommitted edits, so inspect `git status` before
editing or committing.

## Running Locally

Use Python 3.11 (the project target) from the nested application directory:

```powershell
cd 'Cyber Emergency Black Box'
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/init_db.py
pytest
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API root is `/api/v1`. The simulator can post a safe account-compromise sequence
to a running server:

```powershell
python -m simulator.runner --scenario account_compromise
```

## Critical Contracts

- Keep all API/database I/O asynchronous where existing interfaces are async.
- All correlation rules must be explainable and return linked event IDs; do not use
  opaque ML detection.
- Query a bounded event window; never load the complete event history for detection.
- Incident lifecycle is `OPEN`, `INVESTIGATING`, then `CLOSED`.
- Interpreter wording must distinguish observed facts from assessment and never
  claim an event is conclusively malicious.
- Evidence IDs and paths must reject traversal input; manifests contain SHA-256 and
  byte size for every evidence file.
- Simulated events must use `source="simulator"` and `is_simulated=True`.

## Current Limitations and Handoff Priorities

Windows login and USB collectors require optional OS integrations and must degrade
without crashing when unavailable. Validate the full pipeline on Windows: SIM-001 →
incident → evidence verification → report. Add integration tests around each API
contract after the concurrent owners finish their changes. See `codexchanges.md` for
the Codex-specific handoff and `AGENTS.md` for repository conventions.
