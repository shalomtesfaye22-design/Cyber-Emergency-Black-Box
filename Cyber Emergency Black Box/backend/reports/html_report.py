"""Standalone, printable executive incident report rendered with Jinja2."""

import json
from typing import Any

from jinja2 import BaseLoader, Environment, select_autoescape

from backend.interpreter.timeline import build_timeline

ACADEMIC_ATTRIBUTION = "Final Project for INSA Cyber Talent Center 5th round summer camp 2026"
ATTACK_MAPPINGS: dict[str, list[dict[str, str]]] = {
    "R-01": [
        {"id": "T1078", "name": "Valid Accounts", "url": "https://attack.mitre.org/techniques/T1078/"},
        {"id": "T1110", "name": "Brute Force", "url": "https://attack.mitre.org/techniques/T1110/"},
    ],
    "R-02": [
        {"id": "T1059", "name": "Command and Scripting Interpreter", "url": "https://attack.mitre.org/techniques/T1059/"},
    ],
    "R-03": [
        {"id": "T1486", "name": "Data Encrypted for Impact", "url": "https://attack.mitre.org/techniques/T1486/"},
        {"id": "T1083", "name": "File and Directory Discovery", "url": "https://attack.mitre.org/techniques/T1083/"},
    ],
}

_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Incident {{ incident.incident_id }} | Cyber Emergency Black Box</title>
  <style>
    :root{color-scheme:light;--ink:#17233a;--muted:#58677d;--line:#d8e0eb;--navy:#10264a;--blue:#245bd6;--purple:#7046a8;--paper:#fff;--wash:#f3f6fa}
    *{box-sizing:border-box}body{margin:0;background:#e9eef5;color:var(--ink);font:14px/1.55 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
    .sheet{max-width:1040px;margin:32px auto;background:var(--paper);box-shadow:0 12px 40px #1a2b491a}.masthead{padding:28px 44px;background:var(--navy);color:#fff;display:flex;justify-content:space-between;align-items:center;gap:20px}
    .brand{font-size:18px;font-weight:700;letter-spacing:.02em}.brand small{display:block;font-size:11px;color:#b9c9e2;font-weight:500;letter-spacing:.12em;text-transform:uppercase}.academic{font-size:12px;color:#dce7f8;text-align:right}
    main{padding:34px 44px}.eyebrow{color:var(--blue);font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}h1{font-size:28px;line-height:1.2;margin:6px 0 10px}h2{font-size:16px;margin:28px 0 12px;padding-bottom:7px;border-bottom:1px solid var(--line)}h3{font-size:13px;margin:0 0 8px}.summary{font-size:15px;color:#35445b;max-width:850px}
    .metadata{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:22px 0}.meta-card,.finding{border:1px solid var(--line);border-radius:8px;padding:12px;background:#fff;min-width:0}.meta-card span,.label{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.08em}.meta-card strong{display:block;margin-top:5px;overflow-wrap:break-word;word-break:normal;font-size:12px}.severity{display:inline-block;padding:3px 9px;border-radius:20px;background:#fce7e9;color:#a92f40;font-size:11px;font-weight:800}.severity.medium{background:#fff1d6;color:#8a5b00}.severity.low,.severity.info{background:#e2f4ec;color:#21734c}
    .attack-list{display:flex;flex-wrap:wrap;gap:7px}.attack{display:inline-block;padding:4px 9px;border:1px solid #d8c8ef;border-radius:20px;background:#f4effa;color:var(--purple);font-size:11px;font-weight:700;text-decoration:none}.note{color:var(--muted);font-size:11px}
    .timeline-wrap{overflow-x:auto}.timeline-report{min-width:880px;table-layout:fixed}.timeline-report th:nth-child(1){width:175px}.timeline-report th:nth-child(2){width:135px}.timeline-report th:nth-child(3){width:145px}.timeline-report th:nth-child(4){width:160px}.timeline-report td{overflow-wrap:break-word;word-break:normal;white-space:normal}
    table{width:100%;border-collapse:collapse;font-size:12px}thead{background:#eaf0f8}th{text-align:left;color:#34445e;font-size:10px;letter-spacing:.06em;text-transform:uppercase}th,td{border-bottom:1px solid var(--line);padding:9px 10px;vertical-align:top}tbody tr:nth-child(even){background:var(--wash)}.mono{font:11px ui-monospace,"Cascadia Mono",Consolas,monospace;overflow-wrap:anywhere}
    .findings{display:grid;grid-template-columns:1fr 1fr;gap:12px}.finding p{margin:0}.finding ul{padding-left:18px;margin:6px 0 0}.facts{grid-column:1/-1}.disclaimer{margin-top:24px;padding:14px 16px;border-left:4px solid #d18a2a;background:#fff8e9;color:#644c27;font-size:11px}.footer{padding:15px 44px;border-top:1px solid var(--line);color:var(--muted);font-size:10px;display:flex;justify-content:space-between;gap:12px}
    @media(max-width:760px){.sheet{margin:0}.masthead{padding:22px;align-items:flex-start;flex-direction:column}.academic{text-align:left}main{padding:24px}.metadata{grid-template-columns:repeat(2,minmax(0,1fr))}.findings{grid-template-columns:1fr}.facts{grid-column:auto}.footer{padding:14px 24px;flex-direction:column}}
    @media print{body{background:#fff;font-size:10pt}.sheet{max-width:none;margin:0;box-shadow:none}.masthead{-webkit-print-color-adjust:exact;print-color-adjust:exact;padding:18px 28px}main{padding:22px 28px}.meta-card,.finding,table,.disclaimer{break-inside:avoid}.timeline-wrap{overflow:visible}.timeline-report{min-width:0;table-layout:auto;font-size:9pt}thead,tbody tr:nth-child(even),.severity,.attack,.disclaimer{-webkit-print-color-adjust:exact;print-color-adjust:exact}h2{break-after:avoid}a{color:inherit;text-decoration:none}.footer{padding:12px 28px}}
  </style>
</head>
<body>
<article class="sheet">
  <header class="masthead"><div class="brand">CYBER EMERGENCY BLACK BOX<small>Executive Forensic Incident Report</small></div><div class="academic">INSA Cyber Talent Center<br><strong>5th Round Summer Camp 2026</strong></div></header>
  <main>
    <div class="eyebrow">Incident response record · {{ incident.rule_id }}</div>
    <h1>{{ incident.rule_name }}</h1>
    <p class="summary">{{ incident.summary }}</p>
    <section class="metadata" aria-label="Incident metadata">
      <div class="meta-card"><span>Incident ID</span><strong class="mono">{{ incident.incident_id }}</strong></div>
      <div class="meta-card"><span>Severity</span><strong><span class="severity {{ incident.severity|lower }}">{{ incident.severity }}</span></strong></div>
      <div class="meta-card"><span>Workflow status</span><strong>{{ incident.status }}</strong></div>
      <div class="meta-card"><span>Monitored host</span><strong>{{ system.hostname or "Not available" }}</strong></div>
      <div class="meta-card"><span>Detected (UTC)</span><strong>{{ incident.detection_time }}</strong></div>
    </section>

    <section><h2>MITRE ATT&amp;CK investigative hypotheses</h2>
      {% if techniques %}<div class="attack-list">{% for technique in techniques %}<a class="attack" href="{{ technique.url }}">{{ technique.id }} · {{ technique.name }}</a>{% endfor %}</div>{% else %}<p class="note">No technique mapping is currently defined for this detection rule.</p>{% endif %}
      <p class="note">These rule-to-technique associations guide triage only. They do not confirm that a technique was used.</p>
    </section>

    <section><h2>System metadata</h2><div class="metadata">
      <div class="meta-card"><span>Operating system</span><strong>{{ system.os_name or "Not available" }}</strong></div>
      <div class="meta-card"><span>OS version</span><strong>{{ system.os_version or "Not available" }}</strong></div>
      <div class="meta-card"><span>Snapshot captured</span><strong>{{ system.captured_at or "Not available" }}</strong></div>
      <div class="meta-card"><span>Uptime (seconds)</span><strong>{{ system.uptime_seconds if system.uptime_seconds is not none else "Not available" }}</strong></div>
    </div></section>

    <section><h2>Structured event timeline</h2><div class="timeline-wrap"><table class="timeline-report"><thead><tr><th>Timestamp (UTC)</th><th>Event</th><th>Account</th><th>Process</th><th>Observed details</th></tr></thead><tbody>
      {% for row in timeline %}<tr><td class="mono">{{ row.timestamp }}</td><td>{{ row.event_type }}</td><td>{{ row.user_name or "—" }}</td><td>{{ row.process_name or "—" }}</td><td>{{ row.summary }}</td></tr>{% else %}<tr><td colspan="5">No linked events were available.</td></tr>{% endfor %}
    </tbody></table></div></section>

    <section><h2>Forensic interpretation</h2><div class="findings">
      <div class="finding facts"><h3>Confirmed facts</h3><ul>{% for fact in interpretation.confirmed_facts %}<li>{{ fact }}</li>{% else %}<li>No structured facts were recorded.</li>{% endfor %}</ul></div>
      <div class="finding"><h3>Detection result</h3><p>{{ interpretation.detection_result or incident.summary }}</p></div>
      <div class="finding"><h3>Interpretation</h3><p>{{ interpretation.interpretation or "No additional interpretation was recorded." }}</p></div>
      <div class="finding facts"><h3>Recommended next steps</h3><ul>{% for item in interpretation.recommendations %}<li>{{ item }}</li>{% else %}<li>Review the linked evidence and validate the activity with the system owner.</li>{% endfor %}</ul></div>
    </div></section>

    <section><h2>Evidence package · SHA-256 manifest</h2><div style="overflow-x:auto"><table><thead><tr><th>File</th><th>Size (bytes)</th><th>SHA-256</th></tr></thead><tbody>
      {% for name,file in manifest.files.items() %}<tr><td>{{ name }}</td><td class="mono">{{ file.size_bytes }}</td><td class="mono">{{ file.sha256 }}</td></tr>{% else %}<tr><td colspan="3">No evidence manifest is available.</td></tr>{% endfor %}
    </tbody></table></div></section>

    <aside class="disclaimer"><strong>DFIR disclaimer:</strong> {{ interpretation.disclaimer }} Automated classifications and ATT&amp;CK mappings are investigative leads, not proof of compromise, attribution, or legal conclusions. Verify findings against original system records and with authorized personnel.</aside>
  </main>
  <footer class="footer"><span>{{ academic_attribution }}</span><span>Generated by Cyber Emergency Black Box · Preserve this report with its evidence package.</span></footer>
</article>
</body></html>"""


def generate_html_report(
    incident: Any,
    events: list[Any],
    interpretation: str | dict[str, Any],
    manifest: dict[str, Any],
    system: dict[str, Any] | None = None,
) -> str:
    """Render a self-contained printable report without changing the API contract."""
    if isinstance(interpretation, str):
        try:
            interpretation = json.loads(interpretation)
        except json.JSONDecodeError:
            interpretation = {}
    interpretation = interpretation if isinstance(interpretation, dict) else {}
    manifest = dict(manifest) if isinstance(manifest, dict) else {}
    manifest["files"] = manifest.get("files") or {}
    report_interpretation = {
        "confirmed_facts": interpretation.get("confirmed_facts") or [],
        "detection_result": interpretation.get("detection_result") or "",
        "interpretation": interpretation.get("interpretation") or "",
        "recommendations": interpretation.get("recommendations") or [],
        "disclaimer": interpretation.get("disclaimer") or (
            "Automated forensic analysis is a prototype assessment and requires human verification."
        ),
    }
    environment = Environment(
        loader=BaseLoader(),
        autoescape=select_autoescape(default_for_string=True),
    )
    return environment.from_string(_TEMPLATE).render(
        incident=incident,
        timeline=build_timeline(events),
        interpretation=report_interpretation,
        manifest=manifest,
        system=system or {},
        techniques=ATTACK_MAPPINGS.get(getattr(incident, "rule_id", ""), []),
        academic_attribution=ACADEMIC_ATTRIBUTION,
    )
