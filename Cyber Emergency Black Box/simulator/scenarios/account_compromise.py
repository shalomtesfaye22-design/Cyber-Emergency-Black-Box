"""SIM-001: safe synthetic account-compromise sequence."""
import asyncio
from datetime import datetime, timedelta, timezone
from simulator.event_factory import file_modified, login_failure, login_success, network_connection, process_start


class AccountCompromiseScenario:
    name = "account_compromise"
    def events(self):
        start = datetime.now(timezone.utc)
        stamp = lambda seconds: (start + timedelta(seconds=seconds)).isoformat()
        user, process = "demo_user", "archive-tool.exe"
        return [login_failure(user, timestamp=stamp(0)), login_failure(user, timestamp=stamp(30)), login_failure(user, timestamp=stamp(60)), login_success(user, timestamp=stamp(90)), process_start(process, user_name=user, timestamp=stamp(120)), file_modified(process, "C:/demo/records.csv", user_name=user, timestamp=stamp(150)), file_modified(process, "C:/demo/customers.csv", user_name=user, timestamp=stamp(180)), network_connection(process, "203.0.113.10", 443, user_name=user, timestamp=stamp(210))]
    async def run(self, ingest, delay=0.1):
        for item in self.events():
            result = ingest(item)
            if hasattr(result, "__await__"): await result
            await asyncio.sleep(delay)
