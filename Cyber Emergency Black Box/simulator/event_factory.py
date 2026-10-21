"""Factories for safe, clearly labelled synthetic events."""
from datetime import datetime, timezone


def event(event_type: str, **fields) -> dict:
    return {"timestamp": fields.pop("timestamp", datetime.now(timezone.utc).isoformat()), "event_type": event_type, "source": "simulator", "is_simulated": True, "severity": fields.pop("severity", "INFO"), "action": fields.pop("action", event_type), **fields}


def login_failure(user_name: str, **fields): return event("login_failure", user_name=user_name, **fields)
def login_success(user_name: str, **fields): return event("login_success", user_name=user_name, **fields)
def process_start(process_name: str, **fields): return event("process_start", process_name=process_name, **fields)
def file_modified(process_name: str, target: str, **fields): return event("file_modified", process_name=process_name, target=target, **fields)
def network_connection(process_name: str, destination_ip: str, destination_port: int, **fields): return event("network_connection", process_name=process_name, destination_ip=destination_ip, destination_port=destination_port, protocol="tcp", **fields)
