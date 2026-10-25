# Cyber Emergency Black Box — Application Directory

This folder contains the Python application and browser dashboard. The project overview, team placeholders, academic attribution, requirements, and complete Windows quick-start instructions are maintained in the [repository README](../README.md).

## Quick Start

Run these commands from this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe -m backend.main
```

Open <http://127.0.0.1:8000/> and create the local master password on first run. The server is intended to remain bound to localhost. Stop it with **Ctrl+C**.
