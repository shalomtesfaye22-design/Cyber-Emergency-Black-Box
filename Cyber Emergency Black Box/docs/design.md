# Cyber Emergency Black Box — Architecture and Design

**Version:** 1.0  
**Date:** 2026-09-15  
**Status:** Draft for approval

---

## 1. System Overview

The Cyber Emergency Black Box is a local application with three logical layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB BROWSER                              │
│                   (Dashboard — localhost)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP (polling / REST)
┌────────────────────────▼────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  API    │  │Correlation│  │Evidence  │  │  Log           │  │
│  │ Routes  │  │ Engine   │  │ Manager  │  │  Interpreter   │  │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       │             │              │                 │           │
│  ┌────▼─────────────▼──────────────▼─────────────────▼──────┐  │
│  │                   DATABASE LAYER (SQLAlchemy/SQLite)      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              EVENT COLLECTION PIPELINE                   │   │
│  │  Collectors → Normaliser → Event Queue → DB Writer       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Descriptions

### 2.1 Event Collection Pipeline

```
Raw OS / WMI / psutil data
          │
    ┌─────▼──────┐
    │ Collector  │  (one per event type, each independently enabled/disabled)
    └─────┬──────┘
          │ raw dict
    ┌─────▼──────┐
    │ Normaliser │  (converts raw → NormalisedEvent schema)
    └─────┬──────┘
          │ NormalisedEvent
    ┌─────▼──────┐
    │Event Queue │  (asyncio.Queue — decouples collection from storage)
    └─────┬──────┘
          │
    ┌─────▼──────┐
    │ DB Writer  │  (consumes queue, writes to SQLite, triggers correlation)
    └────────────┘
```

Collectors run as asyncio background tasks started at application startup via the FastAPI lifespan context manager.

**Implemented collectors (MVP):**

| Collector | Source | Privilege needed |
|---|---|---|
| `LoginCollector` | Windows Security Event Log (Event ID 4624, 4625) | Admin (degrades gracefully) |
| `ProcessCollector` | `psutil.Popen` / WMI | User |
| `FileCollector` | `watchdog` library on configurable paths | User |
| `NetworkCollector` | `psutil.net_connections()` diff | User |
| `USBCollector` | WMI Win32_USBControllerDevice events | Admin (optional) |
| `SystemInfoCollector` | `psutil`, `platform` | User |
| `SimulatorCollector` | Synthetic events | None |

All collectors are registered in `backend/collectors/registry.py`. Disabling a collector in settings removes it from the startup list without code changes.

### 2.2 Event Normaliser

Each collector produces a dict. The normaliser validates it against the `NormalisedEvent` Pydantic model and fills in defaults. The normalised event is the only format written to the database.

### 2.3 Database Layer

SQLAlchemy 2.x (async) with `aiosqlite`. One SQLite file: `data/blackbox.db`.

Two secondary databases considered and rejected: everything in one file is simpler for a prototype.

### 2.4 Correlation Engine

Runs as an asyncio background task on a configurable polling interval (default 10 s). On each tick it:

1. Queries recent events within the correlation look-back window.
2. Evaluates each registered rule against the event set.
3. For any rule that fires: creates an Incident record, links triggering events, triggers evidence preservation, and triggers interpretation generation.
4. De-duplicates: a rule does not fire again for the same event window if an open incident already exists.

### 2.5 Evidence Manager

On incident creation, automatically:

1. Queries events in the ±context window (default ±5 minutes).
2. Serialises to JSON.
3. Generates `timeline.json`.
4. Captures current `system_info.json`.
5. Writes `README.txt` with plain-language description.
6. Calculates SHA-256 for each file.
7. Writes `manifest.json`.
8. Stores the package at `evidence/incident_<ID>/`.
9. Marks the incident record with the package path.

Evidence directories are never overwritten. If an ID collision somehow occurs, a suffix is appended.

### 2.6 Log Interpreter

A pure-function module that receives an Incident object and its linked events and returns a structured `InterpretationResult`:

```
InterpretationResult:
  summary: str
  facts: list[str]
  assessment: str
  recommended_steps: list[str]
  disclaimer: str
```

The interpreter is entirely template-driven. Each correlation rule has a corresponding interpretation template. This keeps the logic explainable and testable.

### 2.7 FastAPI Backend

All routes are under `/api/v1/`. The frontend (static HTML/CSS/JS) is served directly by FastAPI from `frontend/`.

### 2.8 Frontend

Pure HTML + CSS + JavaScript. No build step required. Chart.js loaded from CDN (with a local fallback copy for offline demo). The dashboard polls the REST API every 5 seconds using `fetch()`.

---

## 3. Database Schema

### Table: `events`

```sql
CREATE TABLE events (
    event_id        TEXT PRIMARY KEY,        -- UUID4
    timestamp       DATETIME NOT NULL,       -- UTC ISO-8601
    event_type      TEXT NOT NULL,           -- enum string (see below)
    source          TEXT NOT NULL,           -- collector name or "simulator"
    user_name       TEXT,                    -- OS username involved
    process_name    TEXT,                    -- process name if relevant
    action          TEXT,                    -- "login_success", "file_modified", etc.
    target          TEXT,                    -- file path, hostname, device name, etc.
    source_ip       TEXT,
    destination_ip  TEXT,
    destination_port INTEGER,
    protocol        TEXT,
    metadata        TEXT,                    -- JSON blob for extra fields
    severity        TEXT NOT NULL DEFAULT 'INFO',  -- INFO / LOW / MEDIUM / HIGH / CRITICAL
    raw_hash        TEXT,                    -- SHA-256 of the raw event JSON
    is_simulated    INTEGER NOT NULL DEFAULT 0,    -- 0=real, 1=simulated
    preserved       INTEGER NOT NULL DEFAULT 0     -- 1=part of an evidence package
);

CREATE INDEX idx_events_timestamp  ON events(timestamp);
CREATE INDEX idx_events_type       ON events(event_type);
CREATE INDEX idx_events_severity   ON events(severity);
```

**event_type values:** `login_success`, `login_failure`, `process_start`, `process_stop`, `file_created`, `file_modified`, `file_deleted`, `network_connection`, `usb_connected`, `usb_disconnected`, `system_info`, `application_log`

### Table: `incidents`

```sql
CREATE TABLE incidents (
    incident_id     TEXT PRIMARY KEY,        -- "INC-YYYYMMDD-NNNN"
    detection_time  DATETIME NOT NULL,       -- UTC
    rule_id         TEXT NOT NULL,           -- e.g. "R-01"
    rule_name       TEXT NOT NULL,
    severity        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'OPEN',  -- OPEN / INVESTIGATING / CLOSED
    summary         TEXT NOT NULL,
    interpretation  TEXT,                    -- JSON InterpretationResult
    evidence_path   TEXT,                    -- relative path to evidence directory
    event_count     INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_incidents_detection_time ON incidents(detection_time);
CREATE INDEX idx_incidents_status         ON incidents(status);
```

### Table: `incident_events`

```sql
CREATE TABLE incident_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id     TEXT NOT NULL REFERENCES incidents(incident_id),
    event_id        TEXT NOT NULL REFERENCES events(event_id)
);

CREATE INDEX idx_ie_incident ON incident_events(incident_id);
```

### Table: `system_snapshots`

```sql
CREATE TABLE system_snapshots (
    snapshot_id     TEXT PRIMARY KEY,
    captured_at     DATETIME NOT NULL,
    hostname        TEXT,
    os_name         TEXT,
    os_version      TEXT,
    cpu_count       INTEGER,
    memory_total_gb REAL,
    uptime_seconds  INTEGER,
    metadata        TEXT     -- JSON for extras
);
```

### Table: `settings`

```sql
CREATE TABLE settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);
```

Default rows inserted at startup:

| key | default value |
|---|---|
| `retention_minutes` | `30` |
| `correlation_interval_seconds` | `10` |
| `evidence_context_minutes` | `5` |
| `enabled_collectors` | `["login","process","file","network","system_info"]` |
| `monitored_paths` | `["C:/Users"]` |

---

## 4. Normalised Event Format

```json
{
  "event_id": "uuid4-string",
  "timestamp": "2026-09-15T09:41:00.000Z",
  "event_type": "login_failure",
  "source": "LoginCollector",
  "user_name": "alice",
  "process_name": null,
  "action": "login_failure",
  "target": "WORKSTATION-01",
  "source_ip": "192.168.1.45",
  "destination_ip": null,
  "destination_port": null,
  "protocol": null,
  "metadata": { "logon_type": 3, "failure_reason": "wrong_password" },
  "severity": "MEDIUM",
  "raw_hash": "sha256-of-this-json",
  "is_simulated": false
}
```

---

## 5. API Design

Base URL: `http://localhost:8000/api/v1`

### 5.1 Events

| Method | Path | Description |
|---|---|---|
| GET | `/events` | List events. Query params: `limit`, `offset`, `event_type`, `severity`, `since`, `simulated_only` |
| GET | `/events/{event_id}` | Get single event |
| POST | `/events` | Ingest a single event (used by simulator and internal pipeline) |
| GET | `/events/stats` | Count by type and severity |

### 5.2 Incidents

| Method | Path | Description |
|---|---|---|
| GET | `/incidents` | List incidents. Query params: `status`, `severity`, `limit`, `offset` |
| GET | `/incidents/{incident_id}` | Full incident detail including linked events and interpretation |
| PATCH | `/incidents/{incident_id}` | Update status (OPEN → INVESTIGATING → CLOSED) |

### 5.3 Timeline

| Method | Path | Description |
|---|---|---|
| GET | `/incidents/{incident_id}/timeline` | Ordered event list for a specific incident |

### 5.4 Evidence

| Method | Path | Description |
|---|---|---|
| GET | `/incidents/{incident_id}/evidence` | Evidence package manifest and hash status |
| GET | `/incidents/{incident_id}/evidence/verify` | Re-run hash verification, return pass/fail per file |
| GET | `/incidents/{incident_id}/evidence/download` | Download evidence package as ZIP |

### 5.5 Reports

| Method | Path | Description |
|---|---|---|
| GET | `/incidents/{incident_id}/report` | Generate and return HTML incident report |

### 5.6 System

| Method | Path | Description |
|---|---|---|
| GET | `/system/info` | Latest system snapshot |
| GET | `/system/status` | Monitoring status, uptime, DB size, collector states |

### 5.7 Settings

| Method | Path | Description |
|---|---|---|
| GET | `/settings` | All settings |
| PUT | `/settings` | Update settings (validated) |

### 5.8 Simulator

| Method | Path | Description |
|---|---|---|
| POST | `/simulator/run` | Start a simulation scenario. Body: `{ "scenario": "account_compromise" }` |
| GET | `/simulator/scenarios` | List available scenario names |

### 5.9 Dashboard

| Method | Path | Description |
|---|---|---|
| GET | `/dashboard/summary` | Aggregated overview: event count, incident count, severity, DB size, uptime |

---

## 6. Correlation Rules

Rules are defined as Python classes that inherit from `BaseRule` in `backend/correlation/rules/base.py`.

### BaseRule interface

```python
class BaseRule:
    rule_id: str        # "R-01"
    name: str           # "Possible Account Compromise"
    description: str
    severity: str       # MEDIUM / HIGH / CRITICAL
    time_window_seconds: int

    def evaluate(self, events: list[NormalisedEvent]) -> RuleResult | None:
        """Return RuleResult if rule fires, None otherwise."""
```

### Rule R-01 — Possible Account Compromise

**Trigger condition:**

1. ≥ 3 `login_failure` events for the same `user_name` within `time_window` (default 5 min)
2. followed by ≥ 1 `login_success` for the same `user_name`
3. followed by ≥ 1 event of type `process_start`, `file_modified`, or `network_connection`

**Severity:** HIGH  
**Time window:** 10 minutes

**Explanation template:**  
"Multiple failed login attempts were detected for user `{user}`, followed by a successful login and subsequent activity. This pattern is consistent with a successful brute-force or credential-stuffing attack."

### Rule R-02 — Suspicious Process Sequence

**Trigger condition:**

1. ≥ 1 `process_start` event (any user) within `time_window`
2. followed by ≥ 2 `file_modified` or `file_created` events by the same process
3. followed by ≥ 1 `network_connection` from the same process or host

**Severity:** HIGH  
**Time window:** 10 minutes

**Explanation template:**  
"A new process `{process}` started, created or modified files, and then initiated a network connection. This sequence may indicate data collection and exfiltration behaviour."

### Rule R-03 — Unusual File Modification Activity

**Trigger condition:**

1. ≥ 5 `file_modified` or `file_created` or `file_deleted` events within `time_window`
2. optionally correlated with a recent `process_start`

**Severity:** MEDIUM  
**Time window:** 5 minutes

**Explanation template:**  
"An unusually high volume of file operations was observed in a short period. This may indicate bulk file manipulation, ransomware-like behaviour, or automated scripting."

### Rule R-04 — Off-Hours Activity (bonus, SHOULD HAVE)

**Trigger condition:**

1. Any `login_success` event outside 07:00–20:00 local time
2. followed by `process_start` or `file_modified`

**Severity:** LOW  
**Time window:** 15 minutes

---

## 7. Evidence Package Structure

```
evidence/
└── incident_INC-20260915-0001/
    ├── events.json          ← all events linked to this incident
    ├── timeline.json        ← chronologically ordered event summaries
    ├── system_info.json     ← system snapshot at time of detection
    ├── manifest.json        ← SHA-256 for each file + creation timestamp
    └── README.txt           ← plain-text description of the incident
```

**manifest.json format:**

```json
{
  "incident_id": "INC-20260915-0001",
  "created_at": "2026-09-15T09:47:00Z",
  "created_by": "CyberEmergencyBlackBox v1.0",
  "files": {
    "events.json":     { "sha256": "...", "size_bytes": 4821 },
    "timeline.json":   { "sha256": "...", "size_bytes": 1204 },
    "system_info.json":{ "sha256": "...", "size_bytes": 512  },
    "README.txt":      { "sha256": "...", "size_bytes": 340  }
  },
  "note": "This manifest was generated automatically. Hashes are SHA-256. Verify with: sha256sum <file>"
}
```

---

## 8. Severity Model

| Level | Meaning | Example |
|---|---|---|
| INFO | Normal informational event | Routine process start |
| LOW | Minor anomaly, unlikely threat | Off-hours login with no follow-up |
| MEDIUM | Notable pattern, warrants attention | Multiple file modifications |
| HIGH | Strong indicator of compromise | Brute-force + login + process + network |
| CRITICAL | Active or confirmed serious incident | (Reserved for future rules) |

These values are **prototype classifications** based solely on the correlation rules defined in this document. They do not represent a certified risk score.

---

## 9. Log Interpreter — Output Template

```
╔══════════════════════════════════════════════════════════╗
║  INCIDENT INTERPRETATION — INC-20260915-0001             ║
╚══════════════════════════════════════════════════════════╝

DETECTED RULE:  R-01 — Possible Account Compromise
SEVERITY:       HIGH
DETECTION TIME: 2026-09-15 09:47:00 UTC

──────────────────────────────────────────────────────────
CONFIRMED FACTS
──────────────────────────────────────────────────────────
• 3 failed login attempts for user "alice" between 09:41 and 09:42 UTC.
• 1 successful login for user "alice" at 09:43 UTC.
• Process "cmd.exe" started at 09:44 UTC.
• File "C:/Users/alice/documents/report.docx" modified at 09:45 UTC.
• Outbound network connection to 203.0.113.45:443 at 09:46 UTC.

──────────────────────────────────────────────────────────
ASSESSMENT
──────────────────────────────────────────────────────────
This sequence is potentially suspicious.

Multiple failed login attempts followed by a successful login
may indicate a successful brute-force or credential-guessing attack.
The subsequent process execution, file modification, and network
connection are consistent with post-compromise activity.

This assessment requires human investigation to confirm or dismiss.

──────────────────────────────────────────────────────────
RECOMMENDED INVESTIGATION STEPS
──────────────────────────────────────────────────────────
1. Verify whether the successful login was authorised by the account owner.
2. Review the origin IP of the failed login attempts.
3. Examine what "cmd.exe" executed (check process arguments if available).
4. Inspect the modified file for unexpected changes.
5. Review the network connection destination (203.0.113.45:443).
6. Check for additional accounts targeted around the same time.

──────────────────────────────────────────────────────────
DISCLAIMER
──────────────────────────────────────────────────────────
This interpretation was generated automatically by the Cyber Emergency
Black Box prototype. It is based on pattern-matching rules and does NOT
constitute a confirmed security incident. Human investigation and
verification are required before taking any action.
```

---

## 10. Frontend Layout

### Navigation bar (left sidebar, dark theme)

```
🔒 Cyber Black Box
─────────────────
📊 Dashboard
📋 Events
🚨 Incidents
📅 Timeline
🗂  Evidence
📄 Reports
⚙  Settings
─────────────────
● MONITORING
[Run Simulation]
```

### Dashboard — Overview cards

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  EVENTS      │ │  INCIDENTS   │ │  SEVERITY    │ │  DB SIZE     │
│  1,247       │ │  3           │ │  HIGH        │ │  2.4 MB      │
│  last 30 min │ │  2 open      │ │  current     │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Events table

```
Timestamp (local)  │ Type           │ User   │ Severity │ Source     │ Simulated
────────────────────────────────────────────────────────────────────────────────
09:46:03           │ network_conn   │ alice  │ MEDIUM   │ NetCollect │ No
09:45:12           │ file_modified  │ alice  │ LOW      │ FileWatch  │ No
```

### Incident timeline

```
Timeline — INC-20260915-0001

09:41:00  🔴 login_failure      alice     MEDIUM
    │
09:41:34  🔴 login_failure      alice     MEDIUM
    │
09:42:11  🔴 login_failure      alice     MEDIUM
    │
09:43:05  🟡 login_success      alice     LOW
    │
09:44:02  🟠 process_start      alice     MEDIUM   cmd.exe
    │
09:45:12  🟠 file_modified      alice     LOW      report.docx
    │
09:46:03  🔴 network_conn       alice     HIGH     203.0.113.45:443
    │
         🚨 INCIDENT TRIGGERED
            R-01: Possible Account Compromise
```

---

## 11. Project Directory Structure

```
cyber-emergency-black-box/
│
├── backend/
│   ├── main.py                    ← FastAPI app entry point + lifespan
│   ├── config.py                  ← centralised settings (loads from DB + env)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── events.py
│   │   ├── incidents.py
│   │   ├── evidence.py
│   │   ├── reports.py
│   │   ├── simulator.py
│   │   ├── system.py
│   │   ├── settings.py
│   │   └── dashboard.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── registry.py            ← collector registry and startup
│   │   ├── base.py                ← BaseCollector ABC
│   │   ├── normaliser.py          ← NormalisedEvent + validation
│   │   ├── login_collector.py
│   │   ├── process_collector.py
│   │   ├── file_collector.py
│   │   ├── network_collector.py
│   │   ├── usb_collector.py
│   │   └── system_info_collector.py
│   ├── correlation/
│   │   ├── __init__.py
│   │   ├── engine.py              ← correlation loop
│   │   ├── rules/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── r01_account_compromise.py
│   │   │   ├── r02_suspicious_process.py
│   │   │   ├── r03_file_activity.py
│   │   │   └── r04_off_hours.py
│   ├── interpreter/
│   │   ├── __init__.py
│   │   ├── interpreter.py
│   │   └── templates/
│   │       ├── r01.py
│   │       ├── r02.py
│   │       └── r03.py
│   ├── evidence/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── engine.py              ← SQLAlchemy async engine setup
│   │   ├── models.py              ← ORM models
│   │   ├── crud.py                ← data access functions
│   │   └── retention.py           ← rolling buffer cleanup task
│   ├── reports/
│   │   ├── __init__.py
│   │   └── html_report.py
│   └── models/
│       ├── __init__.py
│       ├── event.py               ← Pydantic schemas
│       ├── incident.py
│       └── settings.py
│
├── frontend/
│   ├── index.html                 ← single-page shell
│   ├── static/
│   │   ├── css/
│   │   │   └── dashboard.css
│   │   ├── js/
│   │   │   ├── app.js             ← main router and polling logic
│   │   │   ├── dashboard.js
│   │   │   ├── events.js
│   │   │   ├── incidents.js
│   │   │   ├── timeline.js
│   │   │   ├── evidence.js
│   │   │   ├── reports.js
│   │   │   └── settings.js
│   │   └── vendor/
│   │       └── chart.min.js       ← Chart.js local copy
│   └── templates/
│       └── report_template.html   ← HTML report template
│
├── simulator/
│   ├── __init__.py
│   └── scenarios/
│       ├── __init__.py
│       └── account_compromise.py
│
├── tests/
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_collectors.py
│   ├── test_normaliser.py
│   ├── test_correlation.py
│   ├── test_evidence.py
│   ├── test_interpreter.py
│   ├── test_api.py
│   └── test_simulator.py
│
├── evidence/                      ← generated evidence packages (git-ignored)
│
├── data/                          ← SQLite DB file (git-ignored)
│
├── docs/
│   ├── requirements.md
│   ├── design.md
│   ├── tasks.md
│   ├── api.md                     ← generated from OpenAPI
│   └── user_guide.md
│
├── scripts/
│   └── init_db.py                 ← standalone DB initialisation
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 12. Technical Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Windows Event Log requires admin rights | High | Medium | Collector degrades gracefully; simulator covers demo |
| `watchdog` misses rapid file events | Low | Low | Acceptable for prototype; note in documentation |
| SQLite write contention under load | Low | Low | asyncio serialises writes; acceptable at prototype scale |
| Evidence directory path traversal | Low | High | Validate all paths with `pathlib`; reject `..` components |
| False positives in correlation rules | Medium | Medium | Rules use conservative thresholds; clearly labelled as prototype |
| `aiosqlite` async complexity | Low | Low | Use synchronous SQLAlchemy if async proves unstable |

---

## 13. Key Design Decisions

1. **Single SQLite file over multiple databases** — simplicity and portability win for a prototype. No multi-database join complexity.

2. **Polling over WebSocket** — reduces frontend complexity significantly. 5-second polling is imperceptible to a human reviewer.

3. **Template-driven interpreter over NLP/ML** — the requirement explicitly prohibits opaque detection. Templates are readable, testable, and explainable.

4. **asyncio background tasks over celery/RQ** — no message broker dependency. FastAPI lifespan tasks are sufficient for one-machine polling.

5. **HTML reports over PDF** — no heavy PDF library. HTML renders well and can be printed to PDF from the browser.

6. **Pydantic v2 + SQLAlchemy 2** — current stable versions at time of writing. Both support async natively.
