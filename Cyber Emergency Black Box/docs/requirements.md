# Cyber Emergency Black Box — Requirements

**Version:** 1.0  
**Date:** 2026-09-15  
**Status:** Draft for approval

---

## 1. Purpose

This document defines the functional and non-functional requirements for the **Cyber Emergency Black Box** — a lightweight endpoint incident-response and digital-forensics assistant built as a university prototype.

The system continuously collects security-relevant events from a monitored machine, maintains a rolling history, detects suspicious event sequences using rule-based correlation, preserves evidence when an incident is detected, and presents a human-readable incident timeline through a local web dashboard.

---

## 2. Stakeholders

| Role | Responsibility |
|---|---|
| University students (team) | Design, implement, and demonstrate the system |
| Course instructor / examiner | Evaluate the prototype against learning objectives |
| Demo machine owner | Authorise monitoring of the test endpoint |

---

## 3. Functional Requirements

### 3.1 Event Collection

| ID | Requirement |
|---|---|
| F-COL-01 | The system shall collect login events (successes and failures). |
| F-COL-02 | The system shall collect process creation events. |
| F-COL-03 | The system shall collect file creation, modification, and deletion events. |
| F-COL-04 | The system shall collect network connection events (source IP, destination IP, port, protocol). |
| F-COL-05 | The system shall collect USB/removable-device connection events where the OS supports it. |
| F-COL-06 | The system shall collect basic system information (hostname, OS, uptime, CPU, memory). |
| F-COL-07 | The system shall collect application and security log entries where accessible. |
| F-COL-08 | All collectors shall convert raw events into a normalised internal format before storage. |
| F-COL-09 | Each collected event shall be tagged with its source (real collector vs. simulator). |
| F-COL-10 | Collection shall not require elevated privileges for its core function; collectors shall degrade gracefully when a permission is unavailable. |

### 3.2 Event Storage

| ID | Requirement |
|---|---|
| F-DB-01 | Events shall be stored in a local SQLite database. |
| F-DB-02 | Every event record shall contain at minimum: event_id, timestamp (UTC), event_type, source, user, process, action, target, source_ip, destination_ip, metadata (JSON), severity, hash. |
| F-DB-03 | The schema shall support new event types without a structural migration. |
| F-DB-04 | All database access shall use an ORM (SQLAlchemy) to prevent SQL injection. |

### 3.3 Rolling Buffer

| ID | Requirement |
|---|---|
| F-BUF-01 | The system shall maintain a configurable rolling event history (default: 30 minutes). |
| F-BUF-02 | Events older than the retention window shall be removed from the active buffer on a scheduled basis. |
| F-BUF-03 | Events that are part of a preserved incident shall never be deleted by the rolling buffer. |
| F-BUF-04 | The retention period shall be configurable through application settings without code changes. |

### 3.4 Event Correlation Engine

| ID | Requirement |
|---|---|
| F-COR-01 | The system shall implement a rule-based correlation engine. |
| F-COR-02 | Detection logic shall be rule-driven and fully explainable; no opaque ML models shall be used for primary detection. |
| F-COR-03 | Each rule shall have a unique ID, a human-readable name, a description, a time window, and configurable thresholds. |
| F-COR-04 | The engine shall implement at minimum the following three rules (see Section 9 of the project brief):<br>— Rule R-01: Possible Account Compromise<br>— Rule R-02: Suspicious Process Sequence<br>— Rule R-03: Unusual File Modification Activity |
| F-COR-05 | When a rule fires, the engine shall record which specific events triggered it. |
| F-COR-06 | The correlation engine shall run on a configurable polling interval (default: 10 seconds). |

### 3.5 Incident Management

| ID | Requirement |
|---|---|
| F-INC-01 | When a rule fires, the system shall create an Incident record containing: incident_id, detection_time, rule_id, severity, status, summary, and linked event IDs. |
| F-INC-02 | Each incident shall have a status: OPEN, INVESTIGATING, CLOSED. |
| F-INC-03 | Incidents shall be listed on the dashboard with severity, status, and detection time. |

### 3.6 Evidence Preservation

| ID | Requirement |
|---|---|
| F-EVD-01 | When an incident is created, the system shall automatically preserve the relevant event window (configurable pre/post context, default ±5 minutes). |
| F-EVD-02 | The evidence package shall contain: events.json, timeline.json, system_info.json, manifest.json, README.txt. |
| F-EVD-03 | A SHA-256 hash shall be calculated for each file in the evidence package. |
| F-EVD-04 | The manifest.json shall record filenames, sizes, and SHA-256 hashes. |
| F-EVD-05 | Evidence packages shall be stored in a dedicated directory named `evidence/incident_<ID>/`. |
| F-EVD-06 | The application shall not overwrite or delete evidence packages once created. |
| F-EVD-07 | The dashboard shall display evidence integrity status (hash verified / not verified). |

### 3.7 Log Interpreter

| ID | Requirement |
|---|---|
| F-INT-01 | The system shall generate a human-readable interpretation for every incident. |
| F-INT-02 | The interpretation shall clearly separate confirmed facts from rule-based assessment. |
| F-INT-03 | The language shall use qualified terms: "potentially suspicious", "requires investigation", "consistent with", "possible". It shall never state an event is "definitively malicious" unless forensic proof is available. |
| F-INT-04 | The interpretation shall include recommended investigation steps. |
| F-INT-05 | Every interpretation shall include a disclaimer that the output is automated analysis requiring human verification. |

### 3.8 Incident Timeline

| ID | Requirement |
|---|---|
| F-TML-01 | Each incident shall have a chronological event timeline. |
| F-TML-02 | The timeline shall visually distinguish event types (login, process, file, network, etc.). |
| F-TML-03 | Clicking an event in the timeline shall display its full normalised record. |
| F-TML-04 | The timeline shall visually mark the incident trigger point. |

### 3.9 Web Dashboard

| ID | Requirement |
|---|---|
| F-UI-01 | The system shall provide a local web dashboard served by the FastAPI backend. |
| F-UI-02 | The dashboard shall have seven navigation sections: Dashboard, Events, Incidents, Timeline, Evidence, Reports, Settings. |
| F-UI-03 | The dashboard overview shall show: monitoring status, total events, total incidents, current highest severity, database size, and monitoring duration. |
| F-UI-04 | The events view shall list recent events with type, timestamp, severity, source, and user. |
| F-UI-05 | The incidents view shall list all incidents with ID, time, type, severity, and status. |
| F-UI-06 | The incident investigation view shall show: summary, timeline, related events, triggering rule, why it fired, evidence package, hash information, and human-readable interpretation. |
| F-UI-07 | The dashboard shall refresh data via polling (every 5 seconds) without a full page reload. |
| F-UI-08 | The settings view shall allow configuration of: retention window, correlation polling interval, enabled event types. |

### 3.10 Incident Reports

| ID | Requirement |
|---|---|
| F-RPT-01 | The user shall be able to generate an incident report for any incident. |
| F-RPT-02 | The report shall be produced as an HTML file (downloadable). |
| F-RPT-03 | The report shall contain: incident ID, detection time, severity, summary, triggering rule, timeline, related events, evidence files, SHA-256 hashes, interpretation, recommended steps, and disclaimer. |

### 3.11 Demo / Simulation Mode

| ID | Requirement |
|---|---|
| F-SIM-01 | The system shall include a simulation mode that generates a predefined realistic event sequence. |
| F-SIM-02 | Simulated events shall be clearly tagged as `source: "simulator"` in the database. |
| F-SIM-03 | A "Run Security Incident Simulation" button shall be visible on the dashboard. |
| F-SIM-04 | The simulation shall generate the following sequence at minimum:<br>1. 3× failed login attempts<br>2. 1× successful login<br>3. 1× process creation<br>4. 1× file modification<br>5. 1× outbound network connection |
| F-SIM-05 | After simulation, the correlation engine shall detect the sequence and create an incident automatically. |
| F-SIM-06 | Simulated events shall be visually distinguishable from real events in the UI. |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement |
|---|---|
| NF-PRF-01 | The dashboard shall load within 3 seconds on localhost. |
| NF-PRF-02 | Correlation engine polling shall not cause noticeable UI lag. |
| NF-PRF-03 | The SQLite database shall perform adequately for up to 100,000 events (prototype scale). |

### 4.2 Security

| ID | Requirement |
|---|---|
| NF-SEC-01 | All database queries shall use parameterised statements via the ORM. |
| NF-SEC-02 | All API inputs shall be validated with Pydantic models. |
| NF-SEC-03 | File paths used for evidence storage shall be validated to prevent path traversal. |
| NF-SEC-04 | No secrets, API keys, or passwords shall be committed to source code. |
| NF-SEC-05 | The application shall not execute untrusted shell commands with user-supplied input. |
| NF-SEC-06 | Application errors shall be logged safely without exposing stack traces to the browser. |

### 4.3 Reliability

| ID | Requirement |
|---|---|
| NF-REL-01 | The rolling buffer cleanup shall not affect preserved incident evidence. |
| NF-REL-02 | Evidence packages shall be immutable once created (application-level enforcement). |
| NF-REL-03 | The system shall start cleanly from an empty database. |

### 4.4 Maintainability

| ID | Requirement |
|---|---|
| NF-MNT-01 | The architecture shall be modular: each major component (collector, normaliser, correlator, interpreter, evidence, API) shall be independently testable. |
| NF-MNT-02 | Correlation rules shall be defined in a single, clearly documented location. |
| NF-MNT-03 | Configuration values (retention window, polling interval, etc.) shall be centralised in a settings file. |

### 4.5 Privacy

| ID | Requirement |
|---|---|
| NF-PRV-01 | The system shall collect only security-relevant event metadata; it shall not capture message content, passwords, or keystrokes. |
| NF-PRV-02 | A privacy notice shall be displayed in the application (Settings or About page). |
| NF-PRV-03 | The user shall be able to disable individual event type collectors through settings. |

### 4.6 Portability

| ID | Requirement |
|---|---|
| NF-PRT-01 | The system shall run on Windows 10/11 with Python 3.11+. |
| NF-PRT-02 | Platform-specific collectors (Windows Event Log, WMI) shall be optional; the application shall remain functional using the simulator when they are unavailable. |

---

## 5. Constraints

1. **Technology stack is fixed** as specified: Python 3.11+, FastAPI, SQLite, SQLAlchemy, Pydantic, HTML/CSS/JS, Chart.js (optional), pytest.
2. **Scope is fixed at prototype**: no enterprise SIEM features, no multi-host support, no cloud deployment in MVP.
3. **No destructive actions**: the system must not delete files, disable accounts, or block connections automatically.
4. **Runs locally**: the application binds to localhost by default; no external network exposure.
5. **Authorised use only**: the system should be tested only on machines owned or explicitly authorised by the team.

---

## 6. Identified Ambiguities and Resolutions

| Ambiguity | Resolution |
|---|---|
| Login event collection on Windows requires WMI/Event Log access | Windows Event Log collector is implemented as an optional module; falls back to simulator gracefully |
| USB event collection | Implemented via WMI on Windows if available; excluded from MVP critical path |
| PDF vs HTML reports | HTML reports chosen for MVP (lighter, no extra dependency); PDF marked as SHOULD HAVE |
| Evidence tamper prevention | Application-level only (no OS locks); clearly documented as prototype limitation |
| Real-time vs polling dashboard | Polling every 5 seconds; sufficient for prototype, simpler than WebSocket |
| Simulator timestamps | Simulator uses real current UTC time with small synthetic offsets; events flow through the same pipeline as real events |
| ORM choice | SQLAlchemy 2.x with async support via aiosqlite |

---

## 7. Out of Scope (MVP)

- Antivirus or malware scanning
- Vulnerability assessment
- Penetration testing features
- Multi-endpoint monitoring
- Cloud deployment
- Enterprise authentication (LDAP, SSO)
- ML/AI-based anomaly detection
- Real-time push notifications (WebSocket)
- PDF report generation (deferred to SHOULD HAVE)
- Keystroke or clipboard monitoring (explicitly excluded for privacy)
