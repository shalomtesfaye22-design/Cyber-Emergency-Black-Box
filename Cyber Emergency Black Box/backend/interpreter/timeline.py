"""Safe human-readable representations of stored forensic events."""


def event_fact(event) -> str:
    parts = [f"{event.timestamp.isoformat()}: {event.event_type}"]
    if getattr(event, "user_name", None):
        parts.append(f"user={event.user_name}")
    if getattr(event, "process_name", None):
        parts.append(f"process={event.process_name}")
    if getattr(event, "target", None):
        parts.append(f"target={event.target}")
    return " — ".join(parts)


def build_timeline(events) -> list[dict]:
    return [{"event_id": event.event_id, "timestamp": event.timestamp.isoformat(), "event_type": event.event_type, "summary": event_fact(event)} for event in sorted(events, key=lambda item: item.timestamp)]
