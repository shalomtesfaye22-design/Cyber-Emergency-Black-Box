"""R-02: process start, file activity, then outbound network use."""

from datetime import timedelta
from .base import BaseRule, RuleResult


class SuspiciousProcessRule(BaseRule):
    rule_id = "R-02"
    name = "Suspicious Process Sequence"
    severity = "HIGH"
    time_window_seconds = 600

    def evaluate(self, events):
        ordered = sorted(events, key=lambda event: event.timestamp)
        for process in ordered:
            if process.event_type != "process_start":
                continue
            end = process.timestamp + timedelta(seconds=self.time_window_seconds)
            related = [event for event in ordered if process.timestamp <= event.timestamp <= end]
            files = [event for event in related if event.process_name == process.process_name and event.event_type in {"file_created", "file_modified"}]
            network = next((event for event in related if event.event_type == "network_connection" and (event.process_name == process.process_name or not event.process_name)), None)
            if len(files) >= 2 and network:
                return RuleResult(
                    self.rule_id, self.name, self.severity,
                    [process.event_id, *(event.event_id for event in files), network.event_id],
                    f"Process {process.process_name or process.event_id} started, performed {len(files)} file operations, then opened a network connection.",
                    ["Validate the process path, signer, and parent process.", "Review the network destination and affected files."],
                )
        return None
