# Cyber Emergency Black Box

Cyber Emergency Black Box (CEBB) is a local Windows-first endpoint monitoring and
incident investigation prototype. It collects selected security events, stores them in
SQLite, checks them against explainable correlation rules, and packages related events
as evidence when a rule fires. A small browser dashboard and a synthetic incident
simulator support demonstrations.

CEBB is a university prototype. It is not antivirus software, an enterprise SIEM, or a
production endpoint detection and response product. Detections are leads for human
review, not proof of compromise.

## What it does

- Collects process, network, file, system information, and (on Windows, when permitted)
  login telemetry. USB/WMI collection is available as an optional collector.
- Normalizes events, stores them locally, and links event records with SHA-256 hashes.
- Evaluates three rules: R-01 possible account compromise, R-02 suspicious process
  activity, and R-03 unusually frequent file activity.
- Creates incidents with linked events, a chronological timeline, an interpretation,
  and an evidence package containing a hash manifest. Evidence can be verified and
  downloaded as a ZIP archive.
- Provides a FastAPI service, a browser dashboard, and SIM-001 synthetic account
  compromise scenario.

## Requirements

- Windows 10/11 is the primary target. The API and simulator can also run on other
  operating systems, but Windows Event Log and WMI features are Windows-specific.
- Python 3.11 or newer and `pip`.
- An authorized test computer. Run the application only on systems you own or have
  permission to monitor.

Dependencies are listed in [`Cyber Emergency Black Box/requirements.txt`](Cyber%20Emergency%20Black%20Box/requirements.txt).
On Windows, the platform-specific requirement installs `pywin32`. Reading the Windows
Security log may still require an elevated terminal or an account with Security log
read permissions. Without that permission, login telemetry is disabled with a warning;
other available collectors can continue running.

## Quick start on Windows

Clone the project, then open PowerShell in the repository root:

```powershell
git clone https://github.com/shalomtesfaye22-design/Cyber-Emergency-Black-Box.git
Set-Location Cyber-Emergency-Black-Box
```

Create the environment and start the app from the nested application directory:

```powershell
Set-Location 'Cyber Emergency Black Box'
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe -m backend.main
```

The server binds to `127.0.0.1` by default. Once it reports that startup completed,
open:

- Dashboard: <http://127.0.0.1:8000/>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/api/v1/health>

Stop the server with **Ctrl+C** in PowerShell. The database is created at
`Cyber Emergency Black Box/data/blackbox.db`; evidence packages are written under
`Cyber Emergency Black Box/evidence/`.

The application also creates its database tables on startup, so the explicit
`scripts\init_db.py` step is optional for a first run. Do not run the script with
`--reset` unless you intend to delete the existing database contents.

On Linux or macOS, use `python3 -m venv .venv` and `.venv/bin/python` in place of the
Windows `py` launcher and `.venv\Scripts\python.exe`. Windows-only login and USB
collectors will not run on those systems.

### Optional environment configuration

The application reads optional values from `Cyber Emergency Black Box/.env`. Start
with `.env.example` if you need overrides. From the repository root, copy it and edit
the values:

```powershell
Set-Location 'Cyber Emergency Black Box'
Copy-Item .env.example .env
```

For example:

```dotenv
HOST=127.0.0.1
PORT=8000
RETENTION_MINUTES=30
CORRELATION_INTERVAL_SECONDS=10
ENABLED_COLLECTORS=process,file,network,system_info,login
```

The checked-in example omits `login`; add it to `ENABLED_COLLECTORS` if you want the
Windows login collector enabled. Its access still depends on Windows permissions.
The default file watch is the application’s `data/monitored/` directory. Creating or
editing files there is the safest way to demonstrate file telemetry.

## Try the simulator

With the server running, use the dashboard’s **Run attack simulation (SIM-001)** button
or open another PowerShell window in `Cyber Emergency Black Box/` and run:

```powershell
.\.venv\Scripts\python.exe -m simulator.runner `
  --scenario account_compromise `
  --target-url http://127.0.0.1:8000/api/v1/events
```

SIM-001 submits eight clearly labelled events: three failed logins, one successful
login, a process start, two file modifications, and a network connection. The rule
engine should create an incident and preserve evidence. Simulator events are synthetic;
they do not represent actual activity on the computer.

## Frontend status

FastAPI serves `Cyber Emergency Black Box/frontend/index.html` and its static assets.
The interface includes dashboard, event, incident, timeline, evidence, user, and
settings views. The frontend is still under integration with the API:

- The sign-in screen and user list are browser-only demonstrations. They do not create
  accounts or protect API routes; any non-empty sign-in is accepted.
- If the API cannot be reached, the page can display built-in sample data. That sample
  is for layout demonstration only and is not stored as real machine telemetry.
- Some dashboard and collector status fields expect response data in a different shape
  from the API, so counters or status labels may be blank or show zero.
- The settings form includes a collector interval field that the backend does not
  accept. Use the documented backend settings API only for supported settings.
- “Hide simulated” uses a query parameter that the backend does not currently expose.
- `frontend/index().html` is an alternate/duplicate page; FastAPI serves `index.html`
  as the default page.

The API is the reliable way to inspect the current backend behavior. All JSON API
responses use a `data` and `meta` envelope, for example:

```json
{"data":{"status":"ok"},"meta":{}}
```

## API overview

All endpoints are under `/api/v1`:

| Area | Endpoints |
|---|---|
| Health and status | `GET /health`, `GET /system/info`, `GET /system/status`, `GET /dashboard/summary` |
| Events | `POST /events`, `GET /events`, `GET /events/stats`, `GET /events/{event_id}` |
| Incidents | `GET /incidents`, `GET /incidents/{incident_id}`, `PATCH /incidents/{incident_id}`, `GET /incidents/{incident_id}/timeline`, `GET /incidents/{incident_id}/report` |
| Evidence | `GET /incidents/{incident_id}/evidence`, `GET /incidents/{incident_id}/evidence/verify`, `GET /incidents/{incident_id}/evidence/download` |
| Settings | `GET /settings`, `PUT /settings` |
| Simulator | `GET /simulator/scenarios`, `POST /simulator/run` |

See the interactive documentation at `/docs` for request and response details.

## Correlation rules

| Rule | Detection pattern | Severity |
|---|---|---|
| R-01 — Possible account compromise | At least three failed logins, then a successful login and same-user follow-up activity within ten minutes | High |
| R-02 — Suspicious process sequence | A process start, at least two attributed file operations, then an attributed network connection within ten minutes | High |
| R-03 — Unusual file activity | At least five file create/modify/delete events within five minutes | Medium |

The rules are pattern-based and may produce false positives. Review the source events,
account owner, process, and destination before drawing conclusions.

## Tests

Run the automated suite from the application directory:

```powershell
Set-Location 'Cyber Emergency Black Box'
.\.venv\Scripts\python.exe -m pytest -v
```

The tests use an in-memory SQLite database for database/API checks. They cover
normalization, correlation, evidence handling, API workflows, and the simulator.

## Repository layout

```text
.
├── README.md                         # Project setup and user guide
├── AGENTS.md                         # Contributor instructions
├── docs/                             # Requirements, design, and task notes
└── Cyber Emergency Black Box/
    ├── backend/                      # FastAPI, collectors, storage, rules, reports
    ├── frontend/                     # Browser dashboard (served by FastAPI)
    ├── simulator/                    # Synthetic events and CLI runner
    ├── tests/                         # Unit and integration tests
    ├── scripts/init_db.py             # Database initialization
    ├── requirements.txt
    └── .env.example
```

Further design material is in [`docs/design.md`](Cyber%20Emergency%20Black%20Box/docs/design.md),
and the detailed functional requirements are in
[`docs/requirements.md`](Cyber%20Emergency%20Black%20Box/docs/requirements.md).

## Privacy and safe use

CEBB records event metadata such as usernames, process names, file paths, and network
addresses. It does not intentionally collect file contents, keystrokes, passwords, or
private messages. The data and evidence folders may still contain sensitive metadata;
keep them local and do not commit them. The application defaults to localhost and has
no authentication or access control, so do not expose it to a network. Use it only on
systems you own or are authorized to monitor. Automated findings require human review.
