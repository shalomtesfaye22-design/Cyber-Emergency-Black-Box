# Cyber Emergency Black Box — Implementation Tasks

**Version:** 1.0  
**Date:** 2026-09-15  
**Status:** Draft for approval

Each task builds on the previous. Complete and verify each phase before moving to the next. Tasks marked **[TEST]** must have corresponding pytest tests passing before the phase is considered done.

---

## Phase 0 — Project Scaffold

> Goal: bare repository with correct structure and working environment.

- [ ] **T-00-01** Create the full directory tree as defined in `design.md §11`.
- [ ] **T-00-02** Create `requirements.txt` with pinned dependencies:
  - `fastapi==0.111.*`
  - `uvicorn[standard]==0.29.*`
  - `sqlalchemy==2.0.*`
  - `aiosqlite==0.20.*`
  - `pydantic==2.7.*`
  - `psutil==5.9.*`
  - `watchdog==4.0.*`
  - `pytest==8.2.*`
  - `pytest-asyncio==0.23.*`
  - `httpx==0.27.*` (for API tests)
  - `jinja2==3.1.*` (HTML report templating)
- [ ] **T-00-03** Create `.gitignore` (exclude `data/`, `evidence/`, `__pycache__/`, `*.pyc`, `.env`).
- [ ] **T-00-04** Create `README.md` with project description, setup instructions, and how to run.
- [ ] **T-00-05** Create `backend/config.py` with all configurable constants (loaded from environment variables with safe defaults).
- [ ] **T-00-06** Verify: `pip install -r requirements.txt` completes without errors.

---

## Phase 1 — Database Layer

> Goal: working SQLite schema, ORM models, and CRUD operations. **[TEST]**

- [ ] **T-01-01** Implement `backend/database/engine.py`:
  - Async SQLAlchemy engine + sessionmaker.
  - `init_db()` function that creates all tables if they do not exist.
  - Default settings rows inserted on first run.
- [ ] **T-01-02** Implement `backend/database/models.py`:
  - `EventModel`, `IncidentModel`, `IncidentEventModel`, `SystemSnapshotModel`, `SettingsModel`.
  - All columns as defined in schema (design.md §3).
- [ ] **T-01-03** Implement `backend/database/crud.py`:
  - `insert_event(session, event) → EventModel`
  - `get_events(session, filters...) → list[EventModel]`
  - `get_event_by_id(session, id) → EventModel | None`
  - `insert_incident(session, incident) → IncidentModel`
  - `get_incidents(session, filters...) → list[IncidentModel]`
  - `get_incident_by_id(session, id) → IncidentModel | None`
  - `update_incident_status(session, id, status)`
  - `link_events_to_incident(session, incident_id, event_ids)`
  - `get_events_for_incident(session, incident_id) → list[EventModel]`
  - `get_settings(session) → dict`
  - `update_setting(session, key, value)`
  - `insert_system_snapshot(session, snapshot)`
  - `get_latest_system_snapshot(session)`
- [ ] **T-01-04** Implement `backend/database/retention.py`:
  - `purge_old_events(session, retention_minutes)` — deletes events older than retention window where `preserved = 0`.
  - Returns count of deleted rows.
- [ ] **T-01-05** Write `scripts/init_db.py` — standalone script to initialise or reset the database.
- [ ] **T-01-06** **[TEST]** Write `tests/test_database.py`:
  - Test event insertion and retrieval.
  - Test incident insertion and status update.
  - Test event–incident linking.
  - Test retention purge (preserved events are not deleted).
  - Test settings read/write.
  - Use in-memory SQLite (`sqlite+aiosqlite:///:memory:`).

---

## Phase 2 — Event Models and Normaliser

> Goal: canonical Pydantic event schema and normaliser. **[TEST]**

- [ ] **T-02-01** Implement `backend/models/event.py`:
  - `NormalisedEvent` Pydantic model (all fields from design.md §4).
  - `EventCreate`, `EventResponse` schemas.
  - Validators: timestamp must be UTC, severity must be in allowed set, event_type must be in allowed set.
- [ ] **T-02-02** Implement `backend/models/incident.py`:
  - `IncidentCreate`, `IncidentResponse`, `InterpretationResult` Pydantic models.
- [ ] **T-02-03** Implement `backend/collectors/normaliser.py`:
  - `normalise(raw: dict) → NormalisedEvent` — validates and fills defaults.
  - Computes `raw_hash` as SHA-256 of the serialised JSON.
  - Raises `NormalisationError` on invalid input.
- [ ] **T-02-04** **[TEST]** Write `tests/test_normaliser.py`:
  - Valid events pass normalisation.
  - Missing required fields raise `NormalisationError`.
  - `raw_hash` is correctly computed.
  - Invalid `severity` or `event_type` values are rejected.

---

## Phase 3 — Event Collectors

> Goal: working collector pipeline that puts events into the database. **[TEST]**

- [ ] **T-03-01** Implement `backend/collectors/base.py`:
  - `BaseCollector` abstract class with `async def collect()` method.
  - `enabled` property.
  - Standard error handling: exceptions in collect() are logged but do not crash the app.
- [ ] **T-03-02** Implement `backend/collectors/system_info_collector.py`:
  - Uses `psutil` and `platform`.
  - Runs once at startup and then every 60 seconds.
  - Inserts a `system_snapshots` row.
- [ ] **T-03-03** Implement `backend/collectors/process_collector.py`:
  - Polls `psutil.process_iter()` every 5 seconds.
  - Detects new PIDs since last poll and emits `process_start` events.
  - Detects gone PIDs and emits `process_stop` events.
- [ ] **T-03-04** Implement `backend/collectors/network_collector.py`:
  - Polls `psutil.net_connections()` every 10 seconds.
  - Detects new `ESTABLISHED` connections since last poll.
  - Emits `network_connection` events with local/remote address and PID.
- [ ] **T-03-05** Implement `backend/collectors/file_collector.py`:
  - Uses `watchdog` to watch configured paths.
  - Emits `file_created`, `file_modified`, `file_deleted` events.
  - Filters out noise (temp files, `.pyc`, etc.) via configurable exclusion list.
- [ ] **T-03-06** Implement `backend/collectors/login_collector.py`:
  - On Windows: reads Windows Security Event Log for Event IDs 4624 (success) and 4625 (failure).
  - Uses `pywin32` if available; otherwise emits a warning and disables itself.
  - Graceful degradation: collector marks itself as unavailable, does not crash.
- [ ] **T-03-07** Implement `backend/collectors/usb_collector.py`:
  - Uses WMI on Windows if available.
  - Optional collector; marks itself unavailable on import error.
- [ ] **T-03-08** Implement `backend/collectors/registry.py`:
  - `get_enabled_collectors(settings) → list[BaseCollector]`.
  - Reads `enabled_collectors` setting and instantiates only enabled ones.
- [ ] **T-03-09** **[TEST]** Write `tests/test_collectors.py`:
  - Test `normalise()` is called for each collector output.
  - Test process collector detects a new mock process.
  - Test network collector detects a new mock connection.
  - Test file collector emits correct event types.
  - Test login collector degrades gracefully when `pywin32` is absent.
  - All tests use mocked OS calls (no real WMI/psutil side effects).

---

## Phase 4 — Simulator

> Goal: working simulation scenario that produces a full suspicious event sequence. **[TEST]**

- [ ] **T-04-01** Implement `simulator/scenarios/account_compromise.py`:
  - `AccountCompromiseScenario` class with `async def run(event_queue)`.
  - Generates: 3 × `login_failure`, 1 × `login_success`, 1 × `process_start`, 1 × `file_modified`, 1 × `network_connection`.
  - Events spaced 30–60 seconds apart (compressed time: 1 second per simulated minute, configurable).
  - All events tagged `is_simulated = True`, `source = "simulator"`.
- [ ] **T-04-02** Implement `backend/collectors/simulator_collector.py` (wraps scenario runner).
- [ ] **T-04-03** **[TEST]** Write `tests/test_simulator.py`:
  - Simulation produces exactly the expected number and types of events.
  - All simulated events have `is_simulated = True`.
  - Events are in chronological order.

---

## Phase 5 — FastAPI Application Core

> Goal: running FastAPI app with database session injection and lifespan tasks.

- [ ] **T-05-01** Implement `backend/main.py`:
  - FastAPI app with lifespan context manager.
  - On startup: `init_db()`, start collector background tasks, start correlation engine task, start retention cleanup task.
  - On shutdown: cancel background tasks cleanly.
- [ ] **T-05-02** Implement database session dependency (`get_db()`) for injection into route handlers.
- [ ] **T-05-03** Mount `frontend/` as static files at root `/`.
- [ ] **T-05-04** Verify: `uvicorn backend.main:app --reload` starts without errors.
- [ ] **T-05-05** Verify: `http://localhost:8000/docs` shows the auto-generated OpenAPI UI.

---

## Phase 6 — API Routes

> Goal: all REST endpoints implemented and returning correct schemas. **[TEST]**

- [ ] **T-06-01** Implement `backend/api/events.py` — GET /events, GET /events/{id}, POST /events, GET /events/stats.
- [ ] **T-06-02** Implement `backend/api/incidents.py` — GET /incidents, GET /incidents/{id}, PATCH /incidents/{id}.
- [ ] **T-06-03** Implement `backend/api/system.py` — GET /system/info, GET /system/status.
- [ ] **T-06-04** Implement `backend/api/settings.py` — GET /settings, PUT /settings.
- [ ] **T-06-05** Implement `backend/api/simulator.py` — POST /simulator/run, GET /simulator/scenarios.
- [ ] **T-06-06** Implement `backend/api/dashboard.py` — GET /dashboard/summary.
- [ ] **T-06-07** Implement `backend/api/evidence.py` — GET manifest, GET verify, GET download.
- [ ] **T-06-08** Implement `backend/api/reports.py` — GET HTML report (placeholder for now).
- [ ] **T-06-09** Add global exception handler: returns `{"error": "..."}` on unhandled exceptions without stack traces.
- [ ] **T-06-10** **[TEST]** Write `tests/test_api.py`:
  - Test each endpoint with `httpx.AsyncClient`.
  - Test 404 responses for missing resources.
  - Test 422 responses for invalid input.
  - Test event creation and retrieval round-trip.
  - Test incident status update.
  - Test settings update with invalid values rejected.

---

## Phase 7 — Correlation Engine

> Goal: engine detects suspicious sequences and creates incidents. **[TEST]**

- [ ] **T-07-01** Implement `backend/correlation/rules/base.py` — `BaseRule`, `RuleResult` dataclass.
- [ ] **T-07-02** Implement `backend/correlation/rules/r01_account_compromise.py`.
- [ ] **T-07-03** Implement `backend/correlation/rules/r02_suspicious_process.py`.
- [ ] **T-07-04** Implement `backend/correlation/rules/r03_file_activity.py`.
- [ ] **T-07-05** Implement `backend/correlation/rules/r04_off_hours.py` (SHOULD HAVE).
- [ ] **T-07-06** Implement `backend/correlation/engine.py`:
  - `CorrelationEngine.run_once(session)` — evaluates all rules against the current event window.
  - Creates `IncidentModel` records and links triggering events.
  - De-duplication: skip rule if an open incident from the same rule exists for overlapping events.
  - Triggers `EvidenceManager.preserve()` and `Interpreter.interpret()` after incident creation.
- [ ] **T-07-07** **[TEST]** Write `tests/test_correlation.py`:
  - R-01 fires on: 3 failures + success + process (within window).
  - R-01 does NOT fire on: 2 failures + success (below threshold).
  - R-01 does NOT fire on: 3 failures with no subsequent success.
  - R-02 fires correctly.
  - R-03 fires correctly.
  - De-duplication: rule does not create duplicate incident.
  - False positive: mixed events below threshold produce no incident.

---

## Phase 8 — Evidence Preservation

> Goal: incident triggers automatic evidence package creation with verified hashes. **[TEST]**

- [ ] **T-08-01** Implement `backend/evidence/manager.py`:
  - `EvidenceManager.preserve(session, incident_id) → str` — returns package path.
  - Generates all 5 files.
  - Computes SHA-256 for each file using `hashlib`.
  - Writes `manifest.json`.
  - Path safety: all paths resolved with `pathlib`, no `..` components allowed.
  - Returns error string if preservation fails; does not crash the application.
- [ ] **T-08-02** Implement `EvidenceManager.verify(incident_id) → dict` — re-hashes all files and compares to manifest.
- [ ] **T-08-03** Implement `EvidenceManager.get_manifest(incident_id) → dict`.
- [ ] **T-08-04** Implement evidence package download (ZIP) in `backend/api/evidence.py`.
- [ ] **T-08-05** **[TEST]** Write `tests/test_evidence.py`:
  - Evidence package is created with all 5 expected files.
  - SHA-256 values in manifest match actual file contents.
  - `verify()` returns all-pass on unmodified package.
  - `verify()` returns fail on modified file.
  - Path traversal attempt (e.g. `incident_id = "../../../etc/passwd"`) is rejected.

---

## Phase 9 — Log Interpreter

> Goal: every incident has a clear human-readable interpretation. **[TEST]**

- [ ] **T-09-01** Implement `backend/interpreter/templates/r01.py` — R-01 interpretation template.
- [ ] **T-09-02** Implement `backend/interpreter/templates/r02.py` — R-02 interpretation template.
- [ ] **T-09-03** Implement `backend/interpreter/templates/r03.py` — R-03 interpretation template.
- [ ] **T-09-04** Implement `backend/interpreter/interpreter.py`:
  - `Interpreter.interpret(incident, events) → InterpretationResult`.
  - Dispatches to the appropriate template based on `rule_id`.
  - Always includes disclaimer.
  - Never uses absolute language ("is malicious", "confirmed attack").
- [ ] **T-09-05** **[TEST]** Write `tests/test_interpreter.py`:
  - R-01 interpretation contains expected facts (user, counts, times).
  - Output contains disclaimer.
  - Output uses qualified language (check for absence of "is malicious", "confirmed").
  - R-02 and R-03 produce distinct, correct outputs.
  - Unknown rule_id returns a safe generic interpretation rather than crashing.

---

## Phase 10 — HTML Report Generator

> Goal: downloadable incident report. **[TEST]**

- [ ] **T-10-01** Create `frontend/templates/report_template.html` — HTML template with Jinja2 placeholders.
  - All required fields from requirements §3.10.
  - Severity colour-coding.
  - Print-friendly CSS.
  - Disclaimer clearly visible.
- [ ] **T-10-02** Implement `backend/reports/html_report.py`:
  - `generate_html_report(incident, events, interpretation, evidence_manifest) → str`
  - Uses Jinja2 to render the template.
- [ ] **T-10-03** Wire up `GET /api/v1/incidents/{id}/report` to return the HTML report as a downloadable file.
- [ ] **T-10-04** **[TEST]** Write basic test in `tests/test_api.py`:
  - Report endpoint returns 200 and `Content-Type: text/html`.
  - Report HTML contains incident ID, severity, and disclaimer text.

---

## Phase 11 — Frontend Dashboard

> Goal: complete working dashboard UI.

- [ ] **T-11-01** Create `frontend/index.html` — single-page shell with sidebar navigation.
- [ ] **T-11-02** Create `frontend/static/css/dashboard.css` — dark security-dashboard theme.
  - CSS variables for colours and severity indicators.
  - Responsive layout (sidebar collapses on narrow screens).
- [ ] **T-11-03** Implement `frontend/static/js/app.js`:
  - Client-side router that shows/hides page sections.
  - Global 5-second polling loop that refreshes the active page data.
  - Toast notification on new incident detected.
- [ ] **T-11-04** Implement `frontend/static/js/dashboard.js`:
  - Overview cards (event count, incident count, severity, DB size, uptime).
  - "Run Simulation" button that calls `POST /api/v1/simulator/run`.
  - Simulation progress feedback (spinner or status message).
- [ ] **T-11-05** Implement `frontend/static/js/events.js`:
  - Events table with pagination.
  - Severity badge colouring.
  - Simulated event indicator.
  - Click row → expand full event JSON.
- [ ] **T-11-06** Implement `frontend/static/js/incidents.js`:
  - Incidents table.
  - Click incident → navigate to incident investigation view.
  - Status badge colouring.
- [ ] **T-11-07** Implement `frontend/static/js/timeline.js`:
  - Vertical event timeline for a selected incident.
  - Event type icons.
  - Incident trigger marker.
  - Click event → show event detail panel.
- [ ] **T-11-08** Implement `frontend/static/js/evidence.js`:
  - Show manifest file list with hash values.
  - "Verify Integrity" button that calls `/evidence/verify`.
  - Colour-coded pass/fail per file.
  - Download evidence ZIP button.
- [ ] **T-11-09** Implement `frontend/static/js/reports.js`:
  - "Generate Report" button per incident.
  - Opens report HTML in new tab.
- [ ] **T-11-10** Implement `frontend/static/js/settings.js`:
  - Form for retention window, polling interval, enabled collectors.
  - Save sends `PUT /api/v1/settings`.
  - Privacy notice section.
- [ ] **T-11-11** Add Chart.js event distribution chart on the Dashboard overview page.
- [ ] **T-11-12** Verify: full end-to-end simulation flow works in browser without console errors.

---

## Phase 12 — Integration and End-to-End Verification

> Goal: the entire pipeline works from simulation click to evidence download.

- [ ] **T-12-01** Run full simulation from the UI:
  - Click "Run Security Incident Simulation".
  - Confirm events appear in Events view (tagged as simulated).
  - Confirm incident is created automatically (within ~15 seconds).
  - Confirm timeline displays correctly.
  - Confirm evidence package is created and hash verification passes.
  - Confirm interpretation is readable and appropriately qualified.
  - Confirm HTML report downloads correctly.
- [ ] **T-12-02** Run full pytest suite: `pytest tests/ -v`.
  - All tests must pass.
  - Fix any failures before proceeding.
- [ ] **T-12-03** Test graceful degradation: disable `pywin32` import, confirm app starts and simulation still works.
- [ ] **T-12-04** Test retention: set retention to 1 minute, generate events, wait, confirm old events are purged while preserved evidence events remain.
- [ ] **T-12-05** Review all API inputs for missing validation. Add any missing Pydantic constraints.
- [ ] **T-12-06** Run basic security check:
  - Confirm no `..` path traversal is possible via evidence endpoints.
  - Confirm settings endpoint rejects invalid values.
  - Confirm no stack traces appear in API error responses.

---

## Phase 13 — Documentation and Final Packaging

> Goal: complete deliverable package.

- [ ] **T-13-01** Complete `README.md`:
  - Project description.
  - Prerequisites and installation steps.
  - How to run.
  - How to run the demo simulation.
  - How to run tests.
  - Architecture summary with link to `design.md`.
  - Privacy notice.
  - Disclaimer (automated analysis, authorised use only).
- [ ] **T-13-02** Write `docs/api.md` — copy key endpoint descriptions from design.md, add example request/response JSON.
- [ ] **T-13-03** Write `docs/user_guide.md` — step-by-step guide for running the demo and interpreting results.
- [ ] **T-13-04** Create architecture diagram (in `docs/`) — can be ASCII art as in design.md or exported from a diagramming tool.
- [ ] **T-13-05** Create database schema diagram (in `docs/`) — ER diagram showing all tables and relationships.
- [ ] **T-13-06** Review correlation rule documentation — ensure each rule has: ID, name, condition, time window, severity, explanation template.
- [ ] **T-13-07** Final README review: ensure setup instructions work on a clean Python environment.

---

## Summary — Phase Completion Checklist

| Phase | Description | Tests Required | Status |
|---|---|---|---|
| 0 | Project scaffold | No | ☐ |
| 1 | Database layer | Yes | ☐ |
| 2 | Event models + normaliser | Yes | ☐ |
| 3 | Event collectors | Yes | ☐ |
| 4 | Simulator | Yes | ☐ |
| 5 | FastAPI core | No | ☐ |
| 6 | API routes | Yes | ☐ |
| 7 | Correlation engine | Yes | ☐ |
| 8 | Evidence preservation | Yes | ☐ |
| 9 | Log interpreter | Yes | ☐ |
| 10 | HTML report generator | Yes | ☐ |
| 11 | Frontend dashboard | No (manual) | ☐ |
| 12 | Integration verification | Full suite | ☐ |
| 13 | Documentation | No | ☐ |

**Total implementation tasks: ~75**  
**Phases with automated tests: 10 of 14**

---

## Notes on Ordering and Dependencies

- Phases 1 and 2 can be done in parallel (no dependency between schema and Pydantic models).
- Phase 3 requires Phase 2 (normaliser).
- Phase 4 requires Phase 2 (event models).
- Phase 6 requires Phases 1, 2, 5.
- Phase 7 requires Phases 1, 2, 6.
- Phase 8 requires Phase 7.
- Phase 9 requires Phase 7.
- Phase 11 requires Phase 6 (APIs must exist to be called).
- Phase 12 requires all previous phases.
