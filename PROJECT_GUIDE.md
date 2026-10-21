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

## Team Ownership & Source Control

- **Antigravity** owns `backend/database/`, `backend/services/`, `backend/api/`,
  `backend/main.py`, and the test suite (`tests/`).
- **Cursor** owns `backend/collectors/`.
- **Codex** owns `backend/correlation/`, `backend/evidence/`, `backend/interpreter/`,
  `backend/reports/`, and `simulator/`.

The shared branch currently contains integrated work from all three owners. Test
results and commits describe a point in time, so always run `git status`, inspect
`git log --oneline -5`, and rerun the relevant tests before relying on them.

## Running Locally

Use **Python 3.11+** from the application directory. Create an isolated environment
so the pinned project dependencies are used:

```powershell
cd 'Cyber Emergency Black Box'
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/init_db.py
pytest -v
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive API Documentation (Swagger)**: Visit `http://127.0.0.1:8000/docs` (or `/redoc`) in your browser to inspect and test all endpoints interactively.
- **REST API Prefix**: All endpoints are mounted at `/api/v1` (e.g. `/api/v1/events`, `/api/v1/incidents`, `/api/v1/system/status`).
- **Running the Simulator CLI**:
```powershell
python -m simulator.runner --scenario account_compromise
```

## Critical Contracts & Architecture Rules

- **Async I/O**: Keep all API and database operations asynchronous using `AsyncSession`.
- **SQLite Concurrency (WAL Mode)**: The database is configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`). Expect `blackbox.db-wal` and `blackbox.db-shm` files during runtime.
- **Cryptographic Hash Chaining**: Every event links to `previous_hash` forming a tamper-evident audit log.
- **Explainable Correlation**: Correlation rules are deterministic and return linked event IDs; do not use opaque ML detection.
- **Bounded Correlation Windows**: Correlation engines must only query recent sliding windows; never load the full database table into memory.
- **Incident Statuses (FR-023)**: Valid statuses are strictly `OPEN`, `INVESTIGATING`, `RESOLVED`, and `FALSE_POSITIVE`. (Do not use `CLOSED`).
- **DFIR Interpreter Wording**: Distinguish observed facts from assessment. Output must contain the four required sections: `CONFIRMED FACTS`, `DETECTION RESULT`, `INTERPRETATION`, `RECOMMENDATION`, using cautious, non-accusatory language.
- **Evidence Integrity**: Evidence directories under `evidence/incident_<id>/` are immutable and protected against path traversal. Every manifest contains SHA-256 hashes and byte sizes.
- **Simulator Events**: All synthetic events must use `source="simulator"` and `is_simulated=True`.

## OS Telemetry & Permissions

- **Windows Event Log & WMI**: `LoginCollector` (Event IDs 4624/4625) and `USBCollector` (WMI) are Windows-specific and require administrative permissions to read the Windows Security log. Run PowerShell/Terminal **as Administrator** to enable real Security log ingestion.
- **Graceful Fallbacks**: When running without Admin rights or on Linux/macOS, collectors automatically mark themselves `available=False` and log warnings without crashing the application.

## Validation and Agent Handoff

Run focused tests while changing one subsystem, then run the complete suite before
integration:

```powershell
pytest -v
python -m simulator.runner --scenario account_compromise
```

The expected demonstration path is SIM-001 → event ingestion → correlation incident
→ interpreter output → evidence manifest verification → downloadable HTML report.
Do not commit `.env`, databases, `evidence/`, logs, or captured endpoint data. Read
`codexchanges.md` for the forensic-module handoff and `analysis_report.md` for the
latest documented implementation review; treat both as supporting notes, while the
nested requirements and design documents remain the project specification.

