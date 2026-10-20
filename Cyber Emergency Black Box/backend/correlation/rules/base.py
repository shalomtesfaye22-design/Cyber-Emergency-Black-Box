"""Interfaces shared by explainable, modular correlation rules."""

from dataclasses import dataclass
from typing import Protocol, Sequence


class EventLike(Protocol):
    event_id: str
    timestamp: object
    event_type: str
    user_name: str | None
    process_name: str | None


@dataclass(frozen=True, slots=True)
class RuleResult:
    rule_id: str
    name: str
    severity: str
    event_ids: list[str]
    explanation: str
    recommendations: list[str]


class BaseRule:
    rule_id = ""
    name = ""
    severity = "MEDIUM"
    time_window_seconds = 600

    def evaluate(self, events: Sequence[EventLike]) -> RuleResult | None:
        raise NotImplementedError
