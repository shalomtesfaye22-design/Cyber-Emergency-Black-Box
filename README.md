# Cyber Emergency Black Box (CEBB)

> **Academic Project Notice:** Built as a Final Project for the **INSA Cyber Talent Center 5th round summer camp 2026**.

Cyber Emergency Black Box is a local, Windows-first endpoint monitoring and digital forensics prototype. Inspired by an aircraft flight recorder, it collects selected security event metadata, correlates suspicious activity, preserves related evidence, and presents an explainable incident timeline for human review.

CEBB is an academic prototype. It is not antivirus software, a production EDR product, or a replacement for a SIEM. Alerts and MITRE ATT&CK mappings are investigative leads, not proof of compromise or technique use.

## Project Information

**Purpose:** Provide a small, locally operated black box for demonstrating endpoint telemetry, rule-based incident detection, and evidence integrity.

**Main features:**

- Collects process, file, network, system, and (on Windows with required permissions) login telemetry.
- Stores normalized events in SQLite with SHA-256 event chaining.
- Evaluates three explainable rules: account-compromise patterns (R-01), suspicious process activity (R-02), and unusual file activity (R-03).
- Creates incident timelines and human-readable interpretation, then preserves evidence files with a SHA-256 manifest, verification, and ZIP export.
- Provides a FastAPI service, local dashboard, printable HTML report, and synthetic SIM-001 scenario.

## Team Information

The repository does not currently include verified team member names or CTC IDs. Replace the placeholders below with the team's official details before final submission.

| Team member | Full name | CTC ID | Contribution |
|---|---|---|---|
| Member 1 | `[Full name]` | `[CTC ID]` | `[Project role / contribution]` |
| Member 2 | `[Full name]` | `[CTC ID]` | `[Project role / contribution]` |
| Member 3 | `[Full name]` | `[CTC ID]` | `[Project role / contribution]` |
| Member 4 | `[Full name]` | `[CTC ID]` | `[Project role / contribution]` |

Add or remove rows to match the complete project team. Do not publish guessed names or IDs.

## Project Demonstration Video

**Video link:** _Placeholder — add the team's approved demonstration video URL here._

Suggested demo: start CEBB, set up the local master password, run SIM-001 from the dashboard, inspect the resulting incident and timeline, verify the evidence package, then open and print the forensic report.

## Requirements

- Windows 10/11 is the primary target; selected backend and simulator features also work on Linux and macOS.
- Python 3.11 or newer and `pip`.
- An authorized machine or virtual machine. Windows Security Event Log access can require an elevated terminal or explicit log-read permission.
- Dependencies are listed in [`Cyber Emergency Black Box/requirements.txt`](Cyber%20Emergency%20Black%20Box/requirements.txt).

## Quick Start (Windows)

Clone the repository and enter the application directory:

```powershell
git clone https://github.com/shalomtesfaye22-design/Cyber-Emergency-Black-Box.git
Set-Location 'Cyber-Emergency-Black-Box\Cyber Emergency Black Box'
```

Create the virtual environment, install dependencies, and start the local service:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe -m backend.main
```

Open <http://127.0.0.1:8000/>. On first run, create a master password; later visits require that password. The API documentation is at <http://127.0.0.1:8000/docs>. Stop the service with **Ctrl+C**. Startup also initializes database tables, so the explicit `init_db.py` command is optional for a new install. Do not use `--reset` unless you intend to erase the local database.

The server defaults to localhost. Keep it there: this prototype does not provide production-grade account management or deployment security. Collector enablement changes take effect after an application restart.

## Demonstrate an Incident

With the service running and the dashboard unlocked, click **Run attack simulation (SIM-001)**. The simulator submits synthetic events; it does not perform an attack. A detected incident should appear in the Incidents view. Open its timeline, inspect the linked evidence, use **Verify integrity**, and view the HTML report. The safe file-monitoring demonstration directory is `data/monitored/` inside the application folder.

## Detection Rules and ATT&CK References

| Rule | Prototype detection pattern | Suggested ATT&CK references |
|---|---|---|
| R-01 | Three or more failed logins followed by a same-user successful login and follow-up activity within ten minutes | T1110 Brute Force; T1078 Valid Accounts |
| R-02 | A process start followed by attributed file operations and an outbound connection within ten minutes | T1059 Command and Scripting Interpreter |
| R-03 | Five or more file create/modify/delete events within five minutes | T1486 Data Encrypted for Impact; T1083 File and Directory Discovery |

These are triage associations chosen for the project demonstration. The observed event pattern does not establish that the corresponding ATT&CK technique occurred.

## Tests

Run the automated suite from `Cyber Emergency Black Box/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Tests use an in-memory SQLite database and cover API workflows, authentication contracts, collectors, correlation, evidence, and simulation. Automated browser-based visual testing is not currently configured.

## Repository Structure

```text
.
├── README.md                         # Project overview, attribution, team, and setup
├── AGENTS.md                         # Contributor and agent instructions
└── Cyber Emergency Black Box/
    ├── backend/                      # FastAPI, collectors, correlation, evidence, reports
    ├── frontend/                     # Dashboard HTML, CSS, and JavaScript
    ├── simulator/                    # Synthetic event generation and scenarios
    ├── tests/                        # Pytest unit and integration tests
    ├── scripts/init_db.py            # Database initialization utility
    ├── docs/                         # Project design and requirements
    ├── requirements.txt
    └── .env.example
```

## Privacy and Safe Use

CEBB records security metadata such as usernames, process names, file paths, and network addresses; it does not intentionally collect file contents, keystrokes, passwords, or private messages. Keep `data/` and `evidence/` local and out of Git. Use the software only on systems you own or are authorized to monitor. Review automated findings with the account owner and original system records.

## Project Repository

[GitHub — Cyber Emergency Black Box](https://github.com/shalomtesfaye22-design/Cyber-Emergency-Black-Box)
