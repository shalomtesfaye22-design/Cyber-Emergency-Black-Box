# Cyber Emergency Black Box

> A lightweight endpoint incident-response and digital-forensics assistant.  
> University cybersecurity prototype — INSA Summer Camp 2026.

---

## What is it?

Inspired by an aircraft flight recorder, the Cyber Emergency Black Box continuously
collects security-relevant events from a machine, maintains a rolling history, detects
suspicious event sequences using rule-based correlation, preserves evidence when an
incident is detected, and presents a human-readable incident timeline through a local
web dashboard.

**This is NOT an antivirus, vulnerability scanner, or enterprise SIEM.**  
It is a prototype focused on: incident response, digital forensics, endpoint monitoring,
log analysis, event correlation, evidence preservation, and incident reconstruction.

---

## Prerequisites

- Python 3.11 or higher
- pip
- Windows 10/11 (primary target; most features work cross-platform)
- A test machine or virtual machine you own or are authorised to monitor

---

## Installation

```bash
# 1. Clone or download the project
cd cyber-emergency-black-box

# 2. Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialise the database
python scripts/init_db.py
```

### Windows Security Event Log Telemetry

`pywin32` is included in `requirements.txt`. Note that Windows restricts access to `Security.evtx` (Logon event IDs 4624/4625). For real login collection:
- Run your PowerShell terminal as **Administrator**.
- If run without administrator privileges, the application automatically logs a clear warning and disables login telemetry while continuing to monitor processes, network connections, and file system activity normally.

---

## Running the Application

From `Cyber Emergency Black Box/`:

```powershell
# Direct Python module entry point (recommended)
python -m backend.main

# Or via Uvicorn reload:
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The web dashboard is served at: **http://127.0.0.1:8000**  
Interactive API docs are available at: **http://127.0.0.1:8000/docs**

### Real-Time File System Telemetry
The file collector automatically creates and watches the local directory `data/monitored/`. Dropping or editing any files in that folder triggers live file events without needing to touch system folders.

---

## Running the Demo Simulation

1. Open the dashboard at `http://127.0.0.1:8000`.
2. Click **"Run Security Incident Simulation"** on the Dashboard page (or via API: `POST /api/v1/simulator/run`).
3. Watch simulated events appear in the Events view (tagged with purple `SIMULATED` badges).
4. Within ~10 seconds the correlation engine detects the suspicious sequence.
5. An incident appears in the Incidents view (e.g. `INC-20261021-0001`).
6. Click the incident to see the timeline, evidence package, and human-readable interpretation.
7. Click **"Generate Report"** to view or download a standalone HTML incident report with host snapshot metadata.
8. Click **"Verify Integrity"** to validate cryptographic SHA-256 hashes against `manifest.json`.

---

## Running Tests

From `Cyber Emergency Black Box/`:

```powershell
pytest -v
```

All 33 automated tests run against an in-memory SQLite database in ~2 seconds, covering unit, integration, simulation, and collector layers.

---

## Project Structure

```
cyber-emergency-black-box/
├── backend/          ← FastAPI application (API, collectors, correlation, etc.)
├── frontend/         ← HTML/CSS/JS dashboard (served by FastAPI)
├── simulator/        ← Synthetic event scenarios for demo
├── tests/            ← pytest test suite
├── evidence/         ← Generated evidence packages (git-ignored)
├── data/             ← SQLite database file (git-ignored)
├── docs/             ← requirements.md, design.md, tasks.md, user guide
├── scripts/          ← Utility scripts (init_db.py)
├── requirements.txt
└── README.md
```

See [`docs/design.md`](docs/design.md) for the full architecture, database schema,
API design, and correlation rule definitions.

---

## Correlation Rules

| ID | Name | Severity | Trigger |
|----|------|----------|---------|
| R-01 | Possible Account Compromise | HIGH | ≥3 failed logins + success + activity within 10 min |
| R-02 | Suspicious Process Sequence | HIGH | Process start + file ops + network connection within 10 min |
| R-03 | Unusual File Modification Activity | MEDIUM | ≥5 file events within 5 min |
| R-04 | Off-Hours Activity | LOW | Login success outside 07:00–20:00 + follow-up activity |

These rules are **prototype classifications**. They are not a certified risk score.
Every detection includes a full explanation of which events triggered it.

---

## Privacy Notice

This application monitors endpoint activity for security purposes.

It collects:
- Login events (success/failure, username, timestamp)
- Process creation/termination (name, PID, user)
- File system changes (path, type of change — NOT file content)
- Network connections (local/remote address, port, protocol)
- Basic system information (hostname, OS, CPU/memory usage)

It does NOT collect:
- File content
- Keystrokes
- Clipboard content
- Private messages
- Passwords or credentials

**Use this tool only on systems you own or are explicitly authorised to monitor.**
Unauthorised monitoring may be illegal.

---

## Disclaimer

The Cyber Emergency Black Box is an automated analysis prototype.
All detections are based on pattern-matching rules and require human investigation
to confirm or dismiss. Never take action based solely on automated output.

---

## Architecture

See [`docs/design.md`](docs/design.md) for the full architecture diagram,
database schema, API design, and implementation details.

---

## Authors

INSA Summer Camp 2026 — Cybersecurity Project Team
