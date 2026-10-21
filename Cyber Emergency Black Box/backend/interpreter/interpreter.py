"""Explainable, non-definitive forensic incident interpretations."""
from backend.interpreter.timeline import event_fact
from backend.models.incident import InterpretationResult


class Interpreter:
    def interpret(self, incident, events, result=None) -> InterpretationResult:
        facts = [event_fact(event) for event in sorted(events, key=lambda item: item.timestamp)]
        rule_name = getattr(result, "name", None) or incident.rule_name
        explanation = getattr(result, "explanation", None) or incident.summary
        recommendations = getattr(result, "recommendations", None) or ["Review the linked events and verify the responsible account or process."]
        return InterpretationResult(
            confirmed_facts=facts,
            detection_result=f"{rule_name}: {explanation}",
            interpretation=("The observed sequence is potentially suspicious and is consistent with a rule-based detection pattern. "
                            "It is not confirmation of malicious activity and requires analyst verification."),
            recommendations=recommendations,
            disclaimer="Automated forensic analysis requires human verification; conclusions are not proof of compromise.",
        )
