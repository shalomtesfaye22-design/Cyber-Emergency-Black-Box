"""
Cyber Emergency Black Box — Centralised Configuration
------------------------------------------------------
All configurable values live here.
Override any value with an environment variable of the same name (upper-cased).
Example: set RETENTION_MINUTES=60 in your shell before starting the app.

Do NOT hard-code secrets or sensitive paths here.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Resolve project root (two levels up from this file: backend/ -> project/)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # backend/
PROJECT_ROOT = _HERE.parent                       # cyber-emergency-black-box/


class Settings(BaseSettings):
    """Application settings with environment variable override support."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application metadata
    # ------------------------------------------------------------------
    app_name: str = "Cyber Emergency Black Box"
    app_version: str = "1.0.0"
    app_description: str = (
        "A lightweight endpoint incident-response and digital-forensics assistant. "
        "University prototype — for authorised test machines only."
    )

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    host: str = "127.0.0.1"   # localhost only — do not expose externally
    port: int = 8000
    debug: bool = False        # set True only in development

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'blackbox.db'}"
    # Sync URL used for Alembic / scripts (not async)
    database_url_sync: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'blackbox.db'}"

    # ------------------------------------------------------------------
    # Rolling event buffer
    # ------------------------------------------------------------------
    retention_minutes: int = 30          # events older than this are purged
    retention_check_interval: int = 60  # seconds between purge runs

    # ------------------------------------------------------------------
    # Correlation engine
    # ------------------------------------------------------------------
    correlation_interval_seconds: int = 10   # how often the engine polls
    evidence_context_minutes: int = 5        # ± window around an incident

    # ------------------------------------------------------------------
    # Event collectors
    # ------------------------------------------------------------------
    # Comma-separated list of enabled collector names.
    # Valid names: login, process, file, network, usb, system_info
    enabled_collectors: str = "process,file,network,system_info"

    # Paths watched by the file collector (comma-separated)
    monitored_paths: str = str(Path.home())

    # File extensions excluded from file monitoring (comma-separated)
    file_exclude_extensions: str = ".pyc,.pyo,.log,.tmp,.swp,.bak"

    # Interval in seconds for process + network polling collectors
    process_poll_interval: int = 5
    network_poll_interval: int = 10
    system_info_interval: int = 60

    # ------------------------------------------------------------------
    # Simulator
    # ------------------------------------------------------------------
    # Compression factor: 1 real second = N simulated seconds
    # Set to 60 so a 10-minute simulated sequence plays out in ~10 seconds
    simulator_time_compression: int = 60
    simulator_default_user: str = "demo_user"
    simulator_default_host: str = "DEMO-WORKSTATION"

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------
    evidence_dir: Path = PROJECT_ROOT / "evidence"

    # ------------------------------------------------------------------
    # Frontend / static files
    # ------------------------------------------------------------------
    frontend_dir: Path = PROJECT_ROOT / "frontend"

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: str = "INFO"     # DEBUG | INFO | WARNING | ERROR | CRITICAL
    log_file: str = ""          # empty = stdout only

    # ------------------------------------------------------------------
    # Severity levels (informational — do not change without updating rules)
    # ------------------------------------------------------------------
    SEVERITY_LEVELS: list[str] = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # ------------------------------------------------------------------
    # Event types (informational — defines the allowed vocabulary)
    # ------------------------------------------------------------------
    EVENT_TYPES: list[str] = [
        "login_success",
        "login_failure",
        "process_start",
        "process_stop",
        "file_created",
        "file_modified",
        "file_deleted",
        "network_connection",
        "usb_connected",
        "usb_disconnected",
        "system_info",
        "application_log",
    ]


# ---------------------------------------------------------------------------
# Module-level singleton — import this throughout the app
# ---------------------------------------------------------------------------
settings = Settings()


# ---------------------------------------------------------------------------
# Ensure required directories exist at import time
# ---------------------------------------------------------------------------
def ensure_directories() -> None:
    """Create data/ and evidence/ directories if they do not exist."""
    for directory in [
        PROJECT_ROOT / "data",
        settings.evidence_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
