"""Safe human-readable representations of stored forensic events."""


def event_fact(event) -> str:
    timestamp = event.timestamp.isoformat()
    parts = [f"{timestamp}: {event.event_type}"]
    if getattr(event, "user_name", None):
        parts.append(f"user={event.user_name}")
    if getattr(event, "process_name", None):
        parts.append(f"process={event.process_name}")
    if getattr(event, "target", None):
        parts.append(f"target={event.target}")
    if getattr(event, "destination_ip", None):
        parts.append(f"destination={event.destination_ip}")
    if getattr(event, "destination_port", None):
        parts.append(f"port={event.destination_port}")
    return " — ".join(parts)


def build_timeline(events) -> list[dict]:
    return [{"event_id": event.event_id, "timestamp": event.timestamp.isoformat(), "event_type": event.event_type, "summary": event_fact(event), "user_name": getattr(event, "user_name", None), "process_name": getattr(event, "process_name", None), "target": getattr(event, "target", None)} for event in sorted(events, key=lambda item: item.timestamp)]
