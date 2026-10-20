from backend.models.incident import InterpretationResult
class Interpreter:
    def interpret(self, incident, events):
        facts=[f"{e.timestamp.isoformat()} — {e.event_type} ({e.source})" for e in events]
        return InterpretationResult(confirmed_facts=facts,detection_result=incident.summary,interpretation="This pattern is potentially suspicious and requires investigation; it is not proof of malicious activity.",recommendations=["Review linked events and verify the relevant account or process." ])
