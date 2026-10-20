# Cyber Emergency Black Box — Requirements

**Document Version:** 1.1  
**Last Updated:** Phase 0 — Complete  
**Status:** Phase 0 complete. No application functionality has been implemented yet.

---

## 1. Introduction

This document defines the requirements for the Cyber Emergency Black Box prototype. Requirements are grouped by category and each carries a unique identifier. Implementation status is tracked separately in `IMPLEMENTATION_STATUS.md`.

Requirement IDs follow the pattern:

| Prefix | Category |
|---|---|
| FR | Functional Requirement |
| NFR | Non-Functional Requirement |
| SEC | Security Requirement |
| USE | Usability Requirement |
| EVI | Evidence Integrity Requirement |
| LIM | Known Limitation |
| AC | Acceptance Criterion |

---

## 2. Functional Requirements

### 2.1 Event Collection

**FR-001** — The system shall collect security-relevant events from the local host.

**FR-002** — The system shall support the following event types: LOGIN, PROCESS, FILE, NETWORK, USB, SYSTEM, APPLICATION, SECURITY.

**FR-003** — Each event shall be normalized into a common schema before storage, regardless of its source (real collector or simulator).

**FR-004** — The system shall record at minimum: event UUID, timestamp, event type, source, severity, hostname, and raw data for every event.

**FR-005** — The system shall record the following optional fields where available: username, process name, process PID, file path, source IP, destination IP, network port.

**FR-006** — A collector that cannot function on the current operating system shall return an empty result and log a warning rather than raise an unhandled exception.

**FR-007** — The system shall collect basic system information (hostname, OS name, OS version, platform, Python version) on startup.

### 2.2 Event Storage and Retention

**FR-008** — The system shall store all normalized events in a local SQLite database.

**FR-009** — The system shall maintain a configurable rolling event history. The default retention window shall be 30 minutes.

**FR-010** — Events older than the retention window shall be eligible for deletion UNLESS they are linked to a preserved incident.

**FR-011** — Events linked to an incident shall never be automatically deleted.

**FR-012** — The system shall support querying events by: time range, event type, severity, hostname, username, and source.

### 2.3 Detection and Correlation

**FR-013** — The system shall evaluate incoming events against a set of correlation rules.

**FR-014** — The correlation engine shall run all registered rules and return all matches, not just the first.

**FR-015** — Rules shall be modular: each rule shall be a separate module that can be added, removed, or updated independently of the engine.

**FR-016** — The system shall implement Rule RULE-001: Possible Account Compromise — detecting multiple failed login events followed by a successful login followed by unusual activity within a configurable time window.

**FR-017** — The system shall implement Rule RULE-002: Suspicious Process Activity — detecting an unusual process event followed by file modification followed by network activity within a configurable time window.

**FR-018** — The system shall implement Rule RULE-003: Unusual File Activity — detecting a suspicious process followed by a large number of file modification events within a configurable time window.

**FR-019** — Each rule shall produce a structured result containing: rule ID, rule name, severity, matched event IDs, explanation text, and recommendations.

**FR-020** — Rules shall use careful, non-definitive language. A rule result describes a suspicious pattern, not a confirmed attack.

### 2.4 Incident Management

**FR-021** — When a correlation rule fires, the system shall create a structured incident record in the database.

**FR-022** — An incident shall contain: incident UUID, creation timestamp, severity, detection rule name, status, summary, start time, end time, related event IDs, explanation, and recommendations.

**FR-023** — Incident status shall support the values: OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE.

**FR-024** — Incident severity shall support the values: INFO, LOW, MEDIUM, HIGH, CRITICAL.

**FR-025** — An analyst shall be able to update the status of an incident through the API.

**FR-026** — Multiple events shall be linked to an incident via a separate join table.

### 2.5 Evidence Preservation

**FR-027** — When an incident is created (or on analyst request), the system shall export a structured evidence package.

**FR-028** — The evidence package shall be written to a dedicated directory under `evidence/<incident_uuid>/`.

**FR-029** — The evidence package shall contain: `events.json`, `timeline.json`, `system_info.json`, `manifest.json`, `README.txt`.

**FR-030** — `events.json` shall contain the raw and normalized data for all events linked to the incident, exactly as stored in the database. The original database records shall not be modified.

**FR-031** — `manifest.json` shall contain the SHA-256 hash of every other file in the evidence package.

**FR-032** — An analyst shall be able to re-verify the integrity of an evidence package by recomputing hashes and comparing to the manifest.

**FR-033** — The evidence directory contents shall be excluded from Git version control.

### 2.6 Log Interpretation

**FR-034** — The system shall generate a human-readable incident timeline from the events linked to an incident.

**FR-035** — The timeline shall be organized chronologically and shall include only events that actually exist in the database.

**FR-036** — The interpreter output shall contain clearly labelled sections: CONFIRMED FACTS, DETECTION RESULT, INTERPRETATION, RECOMMENDATION.

**FR-037** — The interpreter shall never invent events or assert facts not supported by stored data.

**FR-038** — The interpreter output shall be stored in `timeline.json` within the evidence package and shall be accessible via the API.

### 2.7 API

**FR-039** — The system shall expose a RESTful API via FastAPI.

**FR-040** — The API shall provide endpoints for: health check, event listing, event ingestion, incident listing, incident detail, incident status update, incident timeline, evidence export, dashboard statistics, and system information.

**FR-041** — All API responses shall follow a consistent JSON envelope format.

**FR-042** — The API shall support pagination for list endpoints.

**FR-043** — The API shall support filtering events by type, severity, and time range.

**FR-044** — All API request and response bodies shall be validated using Pydantic models.

### 2.8 Dashboard

**FR-045** — The system shall serve a local web dashboard accessible at `http://localhost:<PORT>`.

**FR-046** — The dashboard shall contain the following pages: Overview, Events, Incidents, Incident Investigation, System Information, Evidence/Reports.

**FR-047** — The Overview page shall display: total event count, recent event count, active incident count, severity distribution, and recent suspicious activity.

**FR-048** — The Events page shall display a searchable, filterable, paginated list of events showing timestamp, type, severity, source, and user/process where available.

**FR-049** — The Incidents page shall display: incident ID, creation time, severity, triggering rule, status, and summary.

**FR-050** — The Incident Investigation page shall display: incident summary, human-readable timeline, related events, detection explanation, interpretation, recommendations, and an evidence export button.

**FR-051** — The dashboard shall communicate with the backend exclusively through the defined REST API.

### 2.9 Simulator

**FR-052** — The system shall include a safe event simulator that generates synthetic events without interacting with the real operating system.

**FR-053** — The simulator shall feed events into the same normalization and ingestion pipeline used by real collectors.

**FR-054** — The simulator shall implement scenario SIM-001: Account Compromise — a sequence of three failed login events, one successful login, one process event, two file modification events, and one network event.

**FR-055** — The simulator shall be runnable from the command line independently of the main application.

**FR-056** — The simulator shall clearly label all generated events with source `SIMULATOR` so they can be distinguished from real events.

---

## 3. Non-Functional Requirements

**NFR-001** — The application shall run entirely locally on a single machine. No external network connectivity is required during normal operation.

**NFR-002** — The backend shall start and become responsive within 10 seconds on a standard development machine.

**NFR-003** — The database shall handle at least 100,000 stored events without degraded query performance for typical dashboard queries.

**NFR-004** — The correlation engine shall evaluate a new event against all rules within 1 second under normal load.

**NFR-005** — The codebase shall be structured so that a university-level Python developer can understand each component independently.

**NFR-006** — Each component shall be independently testable using pytest.

**NFR-007** — The application configuration shall be managed through a `.env` file. Defaults shall be provided so the application can run without a `.env` file present.

**NFR-008** — The application shall log meaningful operational messages using Python's standard `logging` module.

**NFR-009** — The project shall include a `requirements.txt` with pinned dependency versions.

**NFR-010** — The application shall be compatible with Python 3.10 and above.

---

## 4. Security Requirements

**SEC-001** — The application shall operate with read-only access to system information. It shall not modify OS configuration, user accounts, firewall rules, or any system file.

**SEC-002** — The simulator shall generate synthetic events only. It shall not execute real processes, open real network connections, modify real files, or simulate real attacks on the host system.

**SEC-003** — The `.env` file shall not be committed to version control. A `.env.example` file shall be provided instead.

**SEC-004** — No passwords, API keys, or credentials shall be hardcoded in any source file.

**SEC-005** — Evidence files shall be written once and not modified after creation. The original database records shall remain unchanged.

**SEC-006** — SHA-256 hashes in `manifest.json` shall be computed immediately after each evidence file is written to prevent manipulation between write and hash.

**SEC-007** — The application shall not implement any automated response actions (no file deletion, no account locking, no network blocking, no process termination).

**SEC-008** — The dashboard shall be accessible only on localhost by default. Binding to a public interface shall require explicit configuration.

**SEC-009** — Input received through the API shall be validated through Pydantic before being processed or stored.

---

## 5. Usability Requirements

**USE-001** — All incident explanations and timeline outputs shall be written in plain English understandable to a non-specialist analyst.

**USE-002** — The dashboard shall clearly distinguish between: confirmed facts (what logs show), detection results (what rule fired), interpretation (what it may mean), and recommendations (what to examine next).

**USE-003** — The dashboard shall indicate the current implementation status clearly so that users do not misinterpret the prototype as a production system.

**USE-004** — Error messages returned by the API shall be human-readable and shall indicate what went wrong without exposing internal stack traces.

**USE-005** — The simulator shall be startable with a single command and shall produce visible output indicating scenario progress.

**USE-006** — Installation shall require only: Python 3.10+, `pip install -r requirements.txt`, and a single startup command.

---

## 6. Evidence Integrity Requirements

**EVI-001** — Evidence packages shall be treated as forensic artefacts. Once written, their contents shall not be modified by the application.

**EVI-002** — Every file in an evidence package shall have a corresponding SHA-256 hash in `manifest.json`.

**EVI-003** — The manifest shall record the exact filename, file size, and SHA-256 hash for each file.

**EVI-004** — The system shall provide a verification function that re-reads each evidence file, recomputes its hash, and compares it against the stored manifest value.

**EVI-005** — The `events.json` file in an evidence package shall contain event data exactly as retrieved from the database with no modification or redaction.

**EVI-006** — Evidence package directories shall be named using the incident UUID to ensure uniqueness.

---

## 7. Known Limitations

**LIM-001** — This is a university prototype. It has not been validated for production use in a live security operations environment.

**LIM-002** — Severity classifications (INFO / LOW / MEDIUM / HIGH / CRITICAL) are prototype labels and have not been calibrated against a formal threat model.

**LIM-003** — The correlation rules detect patterns that *may* indicate suspicious activity. They do not confirm that an attack occurred and will produce false positives.

**LIM-004** — The rolling buffer is a best-effort retention mechanism. Events may be lost if the application is not running when an incident occurs.

**LIM-005** — Real event collectors are OS-dependent. Some collectors may not function on all platforms. The simulator is always available as a fallback.

**LIM-006** — SQLite is appropriate for a single-endpoint prototype. It is not suitable for multi-host or high-volume deployments without migration to PostgreSQL or equivalent.

**LIM-007** — The dashboard has no authentication. It must only be exposed on trusted local networks.

**LIM-008** — The evidence package provides tamper-evidence through SHA-256 hashing but does not use a digital signature or a trusted timestamp service.

---

## 8. Acceptance Criteria

The system shall be considered functionally complete only when all of the following criteria are satisfied by running the actual application:

**AC-001** — The application starts without errors.

**AC-002** — The simulator can be started from the command line.

**AC-003** — Running scenario SIM-001 generates exactly the expected sequence of events in the database.

**AC-004** — The correlation engine detects the account compromise pattern from SIM-001 and creates an incident record.

**AC-005** — The incident record contains the correct severity, rule name, summary, explanation, and linked event IDs.

**AC-006** — An evidence package is created for the incident containing all required files.

**AC-007** — The SHA-256 hashes in `manifest.json` match the actual files in the package.

**AC-008** — The interpreter generates a human-readable timeline that references only events actually present in the database.

**AC-009** — The dashboard Overview page correctly displays total events, active incidents, and severity counts.

**AC-010** — The dashboard Incident Investigation page correctly displays the timeline, explanation, and recommendations for the detected incident.

**AC-011** — The evidence package can be exported through the dashboard.

**AC-012** — All unit tests pass (`pytest tests/unit/`).

**AC-013** — All integration tests pass (`pytest tests/integration/`).

**AC-014** — No test asserts behaviour that has not been implemented.

---

*This document must agree with `PROJECT_STRUCTURE.md` and `IMPLEMENTATION_STATUS.md` at all times.*
