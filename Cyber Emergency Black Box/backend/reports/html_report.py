from html import escape
def generate_html_report(incident,events,interpretation,manifest):
    rows=''.join(f"<li>{escape(e.timestamp.isoformat())}: {escape(e.event_type)}</li>" for e in events)
    return f"<!doctype html><title>Incident {escape(incident.incident_id)}</title><h1>Incident {escape(incident.incident_id)}</h1><p>Severity: {escape(incident.severity)}</p><p>{escape(incident.summary)}</p><h2>Timeline</h2><ul>{rows}</ul><h2>Disclaimer</h2><p>Automated analysis requires human verification.</p>"
