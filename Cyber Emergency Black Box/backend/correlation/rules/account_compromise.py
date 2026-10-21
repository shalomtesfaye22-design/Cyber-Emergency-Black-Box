"""R-01: failed-login burst followed by successful activity."""

from datetime import timedelta
from .base import BaseRule, RuleResult


class AccountCompromiseRule(BaseRule):
    rule_id = "R-01"
    name = "Possible Account Compromise"
    severity = "HIGH"
    time_window_seconds = 600

    def evaluate(self, events):
        ordered = sorted(events, key=lambda event: event.timestamp)
        activity_types = {"process_start", "file_created", "file_modified", "network_connection"}
        for success_index, success in enumerate(ordered):
            if success.event_type != "login_success" or not success.user_name:
                continue
            start = success.timestamp - timedelta(seconds=self.time_window_seconds)
            failures = [
                event for event in ordered[:success_index]
                if event.event_type == "login_failure"
                and event.user_name == success.user_name
                and event.timestamp >= start
            ]
            if len(failures) < 3:
                continue
            # The minimum three failures, success, and follow-up must all fit
            # inside the same ten-minute detection interval.
            qualifying_failures = failures[-3:]
            window_end = qualifying_failures[0].timestamp + timedelta(seconds=self.time_window_seconds)
            follow_up = next((
                event for event in ordered[success_index + 1:]
                if event.event_type in activity_types
                and event.user_name == success.user_name
                and event.timestamp <= window_end
            ), None)
            if follow_up is None:
                continue
            ids = [event.event_id for event in qualifying_failures] + [success.event_id, follow_up.event_id]
            return RuleResult(
                self.rule_id, self.name, self.severity, ids,
                f"At least three failed logins for {success.user_name} were followed by a successful login and {follow_up.event_type} within ten minutes.",
                ["Verify the account owner and source addresses.", "Review the post-login process, file, and network activity."],
            )
        return None
