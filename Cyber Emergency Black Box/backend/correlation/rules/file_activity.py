"""R-03: unusual volume of destructive or modifying file operations."""

from datetime import timedelta
from .base import BaseRule, RuleResult


class FileActivityRule(BaseRule):
    rule_id = "R-03"
    name = "Unusual File Modification Activity"
    severity = "MEDIUM"
    time_window_seconds = 300

    def evaluate(self, events):
        files = sorted((event for event in events if event.event_type in {"file_created", "file_modified", "file_deleted"}), key=lambda event: event.timestamp)
        for first in files:
            end = first.timestamp + timedelta(seconds=self.time_window_seconds)
            window = [event for event in files if first.timestamp <= event.timestamp <= end]
            if len(window) >= 5:
                return RuleResult(
                    self.rule_id, self.name, self.severity, [event.event_id for event in window],
                    f"{len(window)} file operations occurred within five minutes.",
                    ["Identify the responsible process and preserve affected file metadata.", "Check for expected bulk-update activity before escalating."],
                )
        return None
