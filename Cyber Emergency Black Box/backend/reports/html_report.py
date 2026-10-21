"""Standalone printable Jinja2 incident report."""
from jinja2 import BaseLoader, Environment, select_autoescape
from backend.interpreter.timeline import build_timeline

_TEMPLATE = """<!doctype html><html><head><meta charset='utf-8'><title>Incident {{ incident.incident_id }}</title><style>body{font:14px Arial;margin:2cm}table{border-collapse:collapse;width:100%}th,td{border:1px solid #aaa;padding:7px;text-align:left}.severity{font-weight:bold;color:#a00}@media print{body{margin:1cm}}</style></head><body><h1>Cyber Emergency Black Box — Incident {{ incident.incident_id }}</h1><p class='severity'>Severity: {{ incident.severity }}</p><p>{{ incident.summary }}</p><h2>System Metadata</h2><pre>{{ system|tojson(indent=2) }}</pre><h2>Structured Timeline</h2><table><tr><th>Time</th><th>Type</th><th>Summary</th></tr>{% for row in timeline %}<tr><td>{{ row.timestamp }}</td><td>{{ row.event_type }}</td><td>{{ row.summary }}</td></tr>{% endfor %}</table><h2>CONFIRMED FACTS</h2><ul>{% for fact in interpretation.confirmed_facts %}<li>{{ fact }}</li>{% endfor %}</ul><h2>DETECTION RESULT</h2><p>{{ interpretation.detection_result }}</p><h2>INTERPRETATION</h2><p>{{ interpretation.interpretation }}</p><h2>RECOMMENDATION</h2><ul>{% for item in interpretation.recommendations %}<li>{{ item }}</li>{% endfor %}</ul><h2>Evidence SHA-256 Hashes</h2><table><tr><th>File</th><th>Bytes</th><th>SHA-256</th></tr>{% for name,file in manifest.files.items() %}<tr><td>{{ name }}</td><td>{{ file.size_bytes }}</td><td>{{ file.sha256 }}</td></tr>{% endfor %}</table><p><strong>DFIR disclaimer:</strong> {{ interpretation.disclaimer }}</p></body></html>"""


def generate_html_report(incident, events, interpretation, manifest, system=None) -> str:
    if isinstance(interpretation, str):
        import json
        interpretation = json.loads(interpretation)
    environment = Environment(loader=BaseLoader(), autoescape=select_autoescape(default_for_string=True))
    return environment.from_string(_TEMPLATE).render(incident=incident, timeline=build_timeline(events), interpretation=interpretation, manifest=manifest, system=system or {})
