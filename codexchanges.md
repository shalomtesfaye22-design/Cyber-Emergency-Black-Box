# Codex Change Log

## Context

This is the group fork of `shalomtesfaye22-design/Cyber-Emergency-Black-Box`, a
Windows-focused local endpoint-forensics prototype. The intended pipeline is:
collect metadata → normalise → store → correlate → preserve evidence → explain →
report. This log records Codex-authored work; it does not claim ownership of changes
made concurrently by Antigravity or Cursor.

## Codex Contributions

### Forensic correlation

- Added separate R-01, R-02, and R-03 rule modules for account compromise,
  suspicious process sequences, and high-volume file activity.
- Reworked the correlation engine to query only a bounded recent-event window
  (largest rule window plus 60 seconds), rather than loading all historical events.
- Added exact event-ID-set duplicate checking, incident-ID generation, linked-event
  handling, interpreter invocation, and automatic evidence preservation.

### Evidence, interpretation, and reports

- Added evidence-package generation under `evidence/incident_<id>/` with
  `events.json`, `timeline.json`, `system_info.json`, `manifest.json`, and
  `README.txt`.
- Added SHA-256/byte-size manifest creation, integrity verification, ZIP export, and
  incident-ID traversal rejection (`..`, `/`, and `\`).
- Added a chronological timeline formatter and a four-section DFIR interpreter:
  confirmed facts, detection result, interpretation, and recommendations. Output is
  deliberately non-definitive and carries a human-verification disclaimer.
- Replaced the basic report string with a standalone printable Jinja2 HTML report
  containing severity, system metadata, hashes, timeline, interpretation sections,
  and disclaimer.

### Simulator

- Added synthetic-event factories that always set `source="simulator"` and
  `is_simulated=True`.
- Implemented SIM-001: three failed logins, one success, one process start, two file
  modifications, and one network connection.
- Added `python -m simulator.runner` with callback and live-HTTP ingestion support.

### Earlier bootstrap work

- Added initial database, model, collector, service, dashboard, and test scaffolding
  before team ownership was split. These paths now belong to their assigned owners;
  Codex will not modify them further without explicit direction.
- Added `AGENTS.md`, `.env.example`, and this handoff documentation.

## Validation and Remaining Work

- Syntax validation passed for the assigned modules.
- SIM-001 produces eight chronologically ordered, clearly labelled synthetic events.
- Subsequent team integration commits added the service/API layer, SQLite WAL mode,
  hash chaining, and a broader automated test suite. Consult `git log` and
  `analysis_report.md` for the current shared-branch state.
- The remaining operational validation is an end-to-end Windows run with the desired
  collector permissions and optional dependencies installed.
- Real Windows Event Log and WMI collection remain environment-dependent; confirm
  their integration contracts with correlation and evidence before release.
