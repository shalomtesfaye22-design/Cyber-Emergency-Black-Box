# Cyber Emergency Black Box — Authoritative Project Structure

**Document Version:** 1.1  
**Last Updated:** Phase 0 — Complete  
**Status:** Phase 0 complete. Specification and documentation exist. No application code has been implemented yet. Phase 1 (database foundation) is the next step.

---

## 1. Project Overview

Cyber Emergency Black Box is a defensive cybersecurity and incident-response system inspired by an aircraft flight data recorder ("black box"). The system continuously records security-relevant activity from a local computer, maintains a rolling event history, identifies potentially suspicious sequences of events using explainable rule-based correlation, preserves relevant evidence when an incident is detected, and converts raw technical logs into a clear human-readable incident timeline.

The core pipeline:

```
COLLECT → NORMALIZE → STORE → CORRELATE → PRESERVE → EXPLAIN → REPORT
```

---

## 2. Project Purpose

To provide a focused, explainable, evidence-preserving incident reconstruction capability for a single endpoint. The system is designed so that after any potential security incident, an analyst can answer:

> "What happened on this computer before, during, and after this event?"

---

## 3. Goals

- Continuously record security-relevant events from the local system.
- Store events in a local SQLite database with a configurable rolling buffer.
- Detect suspicious event sequences using transparent, rule-based correlation.
- Create structured incident records when detection rules fire.
- Preserve relevant events as tamper-evident evidence (SHA-256 verified).
- Generate human-readable incident timelines and interpretations.
- Expose all data through a local FastAPI backend.
- Display information through a clean local web dashboard.
- Allow export of an evidence package for offline investigation.
- Provide a safe event simulator for development and demonstrations.

---

## 4. Non-Goals

- This is NOT a commercial SIEM or full EDR platform.
- No machine learning or AI-based detection in the initial implementation.
- No cloud infrastructure, distributed systems, or external services.
- No automated response actions (no file deletion, no account blocking, no network blocking).
- No collection of unnecessary personal information.
- The simulator does NOT perform real attacks on the system.

---

## 5. Target Users

- SOC analysts
- Incident responders and DFIR teams
- Small organizations without enterprise SIEM budgets
- Universities and cybersecurity training environments
- Banks and financial institutions (prototype scale)
- Government and research institutions

---

## 6. Technology Stack

| Layer | Technology |
|---|---|
| Backend language | Python 3.10+ |
| Web framework | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (PostgreSQL-compatible design) |
| Data validation | Pydantic v2 |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Charting | Chart.js (overview statistics) |
| Hashing/integrity | hashlib (SHA-256) |
| Testing | pytest |
| Configuration | python-dotenv, .env file |
| HTTP client (frontend) | fetch API |

---

## 7. Complete Project Tree

The tree below shows the intended final structure. Each item is marked with its current implementation status.

```
cyber-emergency-black-box/
│
├── backend/                          📋 PLANNED
│   ├── __init__.py                   📋 PLANNED
│   ├── main.py                       📋 PLANNED  — FastAPI application entry point
│   ├── config.py                     📋 PLANNED  — Settings loader (python-dotenv)
│   │
│   ├── api/                          📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   ├── routes/                   📋 PLANNED
│   │   │   ├── __init__.py           📋 PLANNED
│   │   │   ├── events.py             📋 PLANNED  — Event endpoints
│   │   │   ├── incidents.py          📋 PLANNED  — Incident endpoints
│   │   │   ├── evidence.py           📋 PLANNED  — Evidence export endpoints
│   │   │   ├── statistics.py         📋 PLANNED  — Dashboard statistics endpoints
│   │   │   └── system.py             📋 PLANNED  — System information endpoints
│   │   └── schemas/                  📋 PLANNED
│   │       ├── __init__.py           📋 PLANNED
│   │       ├── event_schema.py       📋 PLANNED  — Pydantic request/response models
│   │       ├── incident_schema.py    📋 PLANNED
│   │       └── evidence_schema.py    📋 PLANNED
│   │
│   ├── collectors/                   📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   ├── base_collector.py         📋 PLANNED  — Abstract base class for all collectors
│   │   ├── system_collector.py       📋 PLANNED  — Safe system information collector
│   │   ├── login_collector.py        📋 PLANNED  — Login/auth event collector (OS-specific)
│   │   └── process_collector.py      📋 PLANNED  — Process event collector (OS-specific)
│   │
│   ├── correlation/                  📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   ├── engine.py                 📋 PLANNED  — Correlation engine (rule runner)
│   │   └── rules/                    📋 PLANNED
│   │       ├── __init__.py           📋 PLANNED
│   │       ├── base_rule.py          📋 PLANNED  — Abstract base class for rules
│   │       ├── account_compromise.py 📋 PLANNED  — Rule 1: Possible account compromise
│   │       ├── suspicious_process.py 📋 PLANNED  — Rule 2: Suspicious process activity
│   │       └── file_activity.py      📋 PLANNED  — Rule 3: Unusual file activity
│   │
│   ├── database/                     📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   ├── engine.py                 📋 PLANNED  — SQLAlchemy engine and session factory
│   │   ├── models.py                 📋 PLANNED  — ORM table definitions
│   │   ├── crud.py                   📋 PLANNED  — Create/Read/Update/Delete operations
│   │   └── init_db.py                📋 PLANNED  — Database initialization script
│   │
│   ├── evidence/                     📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   ├── manager.py                📋 PLANNED  — Evidence package creation and export
│   │   └── integrity.py              📋 PLANNED  — SHA-256 hashing and verification
│   │
│   ├── interpreter/                  📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   └── timeline.py               📋 PLANNED  — Human-readable timeline and explanation
│   │
│   ├── models/                       📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   ├── event.py                  📋 PLANNED  — Pydantic domain model for Event
│   │   └── incident.py               📋 PLANNED  — Pydantic domain model for Incident
│   │
│   ├── reports/                      📋 PLANNED
│   │   ├── __init__.py               📋 PLANNED
│   │   └── generator.py              📋 PLANNED  — Report assembly (combines interpreter + evidence)
│   │
│   └── services/                     📋 PLANNED
│       ├── __init__.py               📋 PLANNED
│       ├── event_service.py          📋 PLANNED  — Event ingestion and normalization logic
│       ├── incident_service.py       📋 PLANNED  — Incident lifecycle management
│       └── rolling_buffer.py         📋 PLANNED  — Rolling buffer / event retention manager
│
├── frontend/                         📋 PLANNED
│   ├── index.html                    📋 PLANNED  — Main SPA shell
│   ├── css/
│   │   └── style.css                 📋 PLANNED  — Main stylesheet
│   └── js/
│       ├── app.js                    📋 PLANNED  — Router and app bootstrap
│       ├── api.js                    📋 PLANNED  — Fetch wrapper for backend API
│       ├── overview.js               📋 PLANNED  — Overview page logic
│       ├── events.js                 📋 PLANNED  — Events page logic
│       ├── incidents.js              📋 PLANNED  — Incidents list page logic
│       ├── investigation.js          📋 PLANNED  — Incident investigation page logic
│       └── system.js                 📋 PLANNED  — System information page logic
│
├── simulator/                        📋 PLANNED
│   ├── __init__.py                   📋 PLANNED
│   ├── runner.py                     📋 PLANNED  — Simulator entry point and CLI
│   ├── event_factory.py              📋 PLANNED  — Synthetic event builder
│   └── scenarios/
│       ├── __init__.py               📋 PLANNED
│       └── account_compromise.py     📋 PLANNED  — Scenario 1: Account compromise sequence
│
├── tests/                            📋 PLANNED
│   ├── conftest.py                   📋 PLANNED  — Shared pytest fixtures
│   ├── unit/
│   │   ├── test_database.py          📋 PLANNED
│   │   ├── test_event_model.py       📋 PLANNED
│   │   ├── test_correlation.py       📋 PLANNED
│   │   ├── test_evidence.py          📋 PLANNED
│   │   └── test_interpreter.py       📋 PLANNED
│   └── integration/
│       ├── test_api.py               📋 PLANNED
│       └── test_simulator.py         📋 PLANNED
│
├── scripts/                          📋 PLANNED
│   └── init_db.py                    📋 PLANNED  — Standalone DB initialization helper
│
├── evidence/                         ✅ IMPLEMENTED — Directory tracked by Git; runtime package contents are git-ignored
│   └── .gitkeep                      ✅ IMPLEMENTED
│
├── docs/
│   ├── REQUIREMENTS.md               ✅ IMPLEMENTED — 56 requirements across FR/NFR/SEC/USE/EVI/LIM/AC
│   ├── DESIGN.md                     ✅ IMPLEMENTED — Architecture, component design, all pipeline flows, Mermaid diagrams
│   ├── IMPLEMENTATION_STATUS.md      ✅ IMPLEMENTED — Per-component status tracking
│   ├── API.md                        ✅ IMPLEMENTED — Stub; will be completed in Phase 7
│   └── TESTING.md                    ✅ IMPLEMENTED — Stub; will be completed progressively from Phase 1
│
├── .env.example                      ✅ IMPLEMENTED — All configuration keys documented with defaults
├── .gitignore                        ✅ IMPLEMENTED — Covers Python, venv, DB files, secrets, evidence output
├── README.md                         ✅ IMPLEMENTED — Professional README; no false claims
├── requirements.txt                  📋 PLANNED — Phase 1
├── pytest.ini                        📋 PLANNED — Phase 1
└── PROJECT_STRUCTURE.md              ✅ IMPLEMENTED (this file)
```

---

## 8. Directory Descriptions

### `backend/`
The entire Python backend. Contains the FastAPI application, all data models, business logic, and supporting services. Every subdirectory represents a distinct architectural concern.

### `backend/api/`
FastAPI router definitions and Pydantic API schemas. Routes are split by resource (events, incidents, evidence, statistics, system). Schemas define the exact shape of API request and response bodies.

### `backend/collectors/`
Event collectors that pull security-relevant data from the operating system. Each collector extends `base_collector.py`. Collectors are OS-aware: if a collector cannot function on the current OS, it returns an empty result and logs a warning rather than crashing. The simulator bypasses collectors entirely.

### `backend/correlation/`
The detection and correlation engine. `engine.py` runs all registered rules against the current event window. Each rule lives in `rules/` as a separate module extending `base_rule.py`. Rules examine sequences of events and return an incident candidate when a suspicious pattern is detected.

### `backend/database/`
All database concerns. `models.py` defines SQLAlchemy ORM tables. `engine.py` manages the connection and session factory. `crud.py` provides all Create/Read/Update/Delete operations used by services. `init_db.py` creates all tables on first run.

### `backend/evidence/`
Evidence preservation logic. `manager.py` builds a structured evidence package (JSON files + README + manifest) from an incident's related events. `integrity.py` computes and verifies SHA-256 hashes so an investigator can confirm files have not changed since export.

### `backend/interpreter/`
Converts a sequence of stored events into a human-readable timeline and explanation. Does NOT invent events. Outputs clearly labelled sections: CONFIRMED FACTS, DETECTION RESULT, INTERPRETATION, RECOMMENDATION.

### `backend/models/`
Pydantic domain models (distinct from ORM models). Used internally for data passing between services.

### `backend/reports/`
Assembles a complete investigation report from interpreter output and evidence metadata.

### `backend/services/`
Business logic layer. `event_service.py` normalizes and ingests events. `incident_service.py` manages incident lifecycle. `rolling_buffer.py` enforces the configurable retention window.

### `frontend/`
A single-page web application served by FastAPI's static file hosting. No build step required. Uses vanilla JavaScript with a fetch-based API client. Chart.js is loaded from CDN only on pages that use charts.

### `simulator/`
A safe synthetic event generator. Generates realistic-looking event sequences WITHOUT touching the real OS, launching real processes, or performing any network activity. Feeds events into the same ingestion pipeline as real collectors so the entire detection chain can be demonstrated without a real incident.

### `tests/`
pytest test suite. Unit tests cover individual components in isolation. Integration tests cover the API and the simulator-to-detection pipeline end-to-end.

### `evidence/`
Runtime output directory where exported evidence packages are written. The directory itself is tracked by Git (via `.gitkeep`) but its contents are excluded via `.gitignore`.

### `docs/`
All project documentation. Must agree with actual source code at all times.

---

## 9. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        EVENT SOURCES                            │
│  ┌──────────────────┐          ┌──────────────────────────────┐ │
│  │  Real Collectors  │          │  Simulator (synthetic only)  │ │
│  │  (OS-specific)    │          │                              │ │
│  └────────┬─────────┘          └──────────────┬───────────────┘ │
└───────────┼──────────────────────────────────┼─────────────────┘
            │                                  │
            ▼                                  ▼
┌───────────────────────────────────────────────────────────────┐
│                    EVENT NORMALIZATION                         │
│              (event_service.py — common schema)               │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                      SQLite DATABASE                           │
│         events | incidents | incident_events | snapshots      │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│               ROLLING BUFFER MANAGER                          │
│      Enforces retention window, protects incident evidence    │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                   CORRELATION ENGINE                          │
│         Runs rules against recent event window               │
│   Rule 1: Account Compromise                                  │
│   Rule 2: Suspicious Process Activity                         │
│   Rule 3: Unusual File Activity                               │
└───────────────────────────────┬───────────────────────────────┘
                                │ (incident candidate)
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                  INCIDENT SERVICE                             │
│         Creates incident record, links related events        │
└──────────┬────────────────────┬───────────────────────────────┘
           │                    │
           ▼                    ▼
┌─────────────────┐   ┌──────────────────────────────────────┐
│ EVIDENCE MANAGER│   │           LOG INTERPRETER            │
│ Builds package  │   │  Generates human-readable timeline   │
│ SHA-256 hashes  │   │  FACTS / DETECTION / INTERPRETATION  │
└────────┬────────┘   └──────────────────┬───────────────────┘
         │                               │
         └──────────────┬────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                      FastAPI BACKEND                          │
│  /events  /incidents  /evidence  /statistics  /system        │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                    WEB DASHBOARD                              │
│  Overview | Events | Incidents | Investigation | Evidence    │
└───────────────────────────────────────────────────────────────┘
```

---

## 10. Database Design

### Tables (planned, not yet created)

#### `events`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| event_uuid | VARCHAR | UUID, unique |
| timestamp | DATETIME | Event occurrence time |
| received_at | DATETIME | When system received it |
| event_type | VARCHAR | LOGIN, PROCESS, FILE, NETWORK, USB, SYSTEM, APPLICATION, SECURITY |
| source | VARCHAR | Collector or simulator name |
| severity | VARCHAR | INFO, LOW, MEDIUM, HIGH, CRITICAL |
| hostname | VARCHAR | |
| username | VARCHAR | Nullable |
| process_name | VARCHAR | Nullable |
| process_pid | INTEGER | Nullable |
| file_path | VARCHAR | Nullable |
| network_src_ip | VARCHAR | Nullable |
| network_dst_ip | VARCHAR | Nullable |
| network_port | INTEGER | Nullable |
| raw_data | TEXT | JSON string of original event |
| normalized_data | TEXT | JSON string of normalized form |

#### `incidents`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| incident_uuid | VARCHAR | UUID, unique |
| created_at | DATETIME | |
| severity | VARCHAR | INFO / LOW / MEDIUM / HIGH / CRITICAL |
| status | VARCHAR | OPEN / INVESTIGATING / RESOLVED / FALSE_POSITIVE |
| rule_name | VARCHAR | Which rule triggered |
| summary | TEXT | Short human-readable summary |
| start_time | DATETIME | Earliest related event |
| end_time | DATETIME | Latest related event |
| explanation | TEXT | Why this sequence was flagged |
| recommendations | TEXT | JSON list of next steps |

#### `incident_events`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| incident_id | INTEGER FK → incidents.id | |
| event_id | INTEGER FK → events.id | |

#### `system_snapshots`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| captured_at | DATETIME | |
| hostname | VARCHAR | |
| os_name | VARCHAR | |
| os_version | VARCHAR | |
| platform | VARCHAR | |
| python_version | VARCHAR | |
| app_version | VARCHAR | |

#### `settings`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| key | VARCHAR UNIQUE | |
| value | TEXT | |
| updated_at | DATETIME | |

---

## 11. Event Model

Events are normalized into a common schema regardless of source (collector or simulator). The normalization step converts OS-specific or simulator-specific raw data into a standard `Event` object before storage.

Supported event types:
- `LOGIN` — Authentication events (success and failure)
- `PROCESS` — Process start/stop events
- `FILE` — File create/modify/delete events
- `NETWORK` — Network connection events
- `USB` — USB device events (OS-dependent)
- `SYSTEM` — System state changes (startup, shutdown)
- `APPLICATION` — Application-level events
- `SECURITY` — Security-specific events (privilege escalation etc.)

Important: Not every event type is collectable on every OS. Collectors declare what they support. The simulator supports all types unconditionally.

---

## 12. Detection Rules (planned)

Rules use explainable, deterministic logic only. No machine learning.

| Rule ID | Name | Trigger Pattern | Severity |
|---|---|---|---|
| RULE-001 | Possible Account Compromise | Multiple failed logins → successful login → unusual activity | HIGH |
| RULE-002 | Suspicious Process Activity | Unusual process → file modification → network activity | MEDIUM |
| RULE-003 | Unusual File Activity | Suspicious process → large volume of file modifications | MEDIUM |

Rules must use careful language. They flag patterns that *may* indicate suspicious activity. They do not confirm attacks.

---

## 13. Evidence Package Structure (planned)

When an incident is preserved, the evidence package written to `evidence/<incident_uuid>/` will contain:

```
evidence/<incident_uuid>/
├── events.json          — All related events (from DB, unmodified)
├── timeline.json        — Structured timeline from interpreter
├── system_info.json     — System snapshot at time of export
├── manifest.json        — SHA-256 hashes of all files in package
└── README.txt           — Plain-text summary for non-technical reviewers
```

The manifest allows an investigator to verify that no file was altered after export.

---

## 14. API Endpoints (planned)

| Method | Path | Description |
|---|---|---|
| GET | /health | Application health and status |
| GET | /api/v1/events | List events (paginated, filterable) |
| POST | /api/v1/events | Ingest a new event |
| GET | /api/v1/events/{id} | Get single event |
| GET | /api/v1/incidents | List incidents |
| GET | /api/v1/incidents/{id} | Get incident details |
| PATCH | /api/v1/incidents/{id}/status | Update incident status |
| GET | /api/v1/incidents/{id}/timeline | Get human-readable timeline |
| POST | /api/v1/incidents/{id}/evidence | Export evidence package |
| GET | /api/v1/statistics | Dashboard statistics |
| GET | /api/v1/system | System information |

---

## 15. Simulator Scenarios (planned)

| Scenario | ID | Description |
|---|---|---|
| Account Compromise | SIM-001 | Failed logins × 3 → successful login → new process → file modifications → network event |

Additional scenarios will be added in later phases.

---

## 16. Implementation Status Summary

> This section is updated at the end of every implementation phase.

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Project specification and documentation | ✅ COMPLETE |
| Phase 1 | Database foundation | 📋 PLANNED — next step |
| Phase 2 | Event model and normalization | 📋 PLANNED |
| Phase 3 | Simulator | 📋 PLANNED |
| Phase 4 | Correlation engine | 📋 PLANNED |
| Phase 5 | Evidence preservation | 📋 PLANNED |
| Phase 6 | Log interpreter | 📋 PLANNED |
| Phase 7 | FastAPI backend | 📋 PLANNED |
| Phase 8 | Web dashboard | 📋 PLANNED |
| Phase 9 | Real collectors | 📋 PLANNED |
| Phase 10 | Final integration | 📋 PLANNED |

---

## 17. Security Considerations

- The application runs entirely locally. No data is sent to external services.
- The simulator generates synthetic data only. It does not execute real attacks.
- Evidence files are read-only after export. The original database is never modified by the evidence system.
- SHA-256 hashes provide tamper-evidence for exported packages.
- The `.env` file is excluded from Git. Secrets are never committed.
- Collectors operate with read-only access to system information.
- No automated response actions are implemented (no file deletion, no account locking, no network blocking).

---

## 18. Language and Interpretation Policy

The system must distinguish between:

| Label | Meaning |
|---|---|
| **CONFIRMED FACTS** | What the stored log events actually show |
| **DETECTION RESULT** | Which rule was triggered and why |
| **INTERPRETATION** | What the sequence *may* indicate |
| **RECOMMENDATION** | What an investigator should examine next |

Required phrasing examples:
- "Potentially suspicious"
- "Requires investigation"
- "Consistent with"
- "Possible account compromise"
- "The available evidence indicates..."
- "This sequence may indicate..."

The system must never state that an attack definitively occurred unless the evidence actually proves it.

---

## 19. Update Log

| Version | Phase | Change |
|---|---|---|
| 1.0 | Phase 0 | Initial document created. Workspace was empty. Clean start confirmed. |
| 1.1 | Phase 0 | Phase 0 marked complete. Status labels corrected: all existing documentation files marked ✅ IMPLEMENTED. Phase 0 row in implementation table updated from 🔶 IN PROGRESS to ✅ COMPLETE. No application code exists. Phase 1 is the next step. |

---

*This document is the authoritative reference for the Cyber Emergency Black Box project. It must be updated whenever the architecture or implementation status changes.*
