# Backend Handoff — Changes Made

## Context

This repository is the group project cloned from
[`shalomtesfaye22-design/Cyber-Emergency-Black-Box`](https://github.com/shalomtesfaye22-design/Cyber-Emergency-Black-Box).
The implementation work below targets the backend of the Windows-focused endpoint
forensics prototype. The intended flow is: collect metadata → normalise → store →
correlate → preserve evidence → explain → expose through a local API.

## Added Backend Components

All application changes are under `Cyber Emergency Black Box/`.

- Database: async SQLAlchemy engine, SQLite models for events, incidents, incident
  links, system snapshots, and settings; CRUD helpers; default settings; and rolling
  retention that preserves incident-linked events.
- Domain and ingestion: Pydantic event and incident models, UTC/type/severity
  validation, normalization, UUID creation, and SHA-256 hashes for raw event data.
- Collectors: process, network, file-system, and system-information collectors,
  plus a collector registry. Login and USB collectors safely mark themselves
  unavailable when their optional Windows dependencies/providers are absent.
- Detection: modular R-01 account-compromise, R-02 suspicious-process, and R-03
  high-volume-file-activity rules, with incident creation, event links, and basic
  duplicate avoidance.
- Evidence and interpretation: immutable per-incident packages containing events,
  timeline, system information, manifest hashes, and README; integrity verification,
  ZIP creation, qualified-language interpretation, and an HTML report generator.
- Service: `backend/main.py` provides FastAPI lifespan tasks, collection/correlation
  scheduling, simulator execution, and versioned event, incident, evidence, report,
  settings, system, and dashboard-summary endpoints. Successful responses use a
  `data`/`meta` envelope.
- Simulator: a safe `account_compromise` scenario generates three failed logins, a
  successful login, process activity, file modification, and network activity via
  the normal ingestion pipeline.

## Supporting Changes

- Added initial pytest coverage for normalization, rule thresholds, and evidence
  path traversal protection.
- Added `.env.example` with local-only defaults.
- Added a minimal `frontend/` shell for manual API demonstration. It is not a
  replacement for the planned frontend work and can be expanded or replaced by the
  frontend owner.
- Added root `AGENTS.md`, a contributor guide.

## Verification and Follow-up

`python -m compileall -q backend simulator scripts tests` passed. Runtime tests were
not run: the available interpreter is Python 3.14 and currently has none of the
pinned project dependencies installed. Before merging, use Python 3.11 (the project
target), create a virtual environment, run `pip install -r requirements.txt`, then
run `pytest` and start Uvicorn.

Important remaining backend hardening: finish real Windows Event Log polling in the
login collector, implement the optional WMI USB collector, add API/database/evidence
integration tests, and verify the full simulator-to-report workflow on Windows.
