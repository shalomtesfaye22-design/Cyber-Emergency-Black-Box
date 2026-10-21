"""Run simulator scenarios against a callback or the live local API."""
import argparse
import asyncio
import json
from urllib.error import HTTPError, URLError
import urllib.request
from simulator.scenarios.account_compromise import AccountCompromiseScenario


async def run_scenario(scenario: str, ingest=None, target_url: str | None = None, delay: float = 0.1):
    if scenario != "account_compromise":
        raise ValueError(f"unknown scenario: {scenario}")
    if delay < 0:
        raise ValueError("delay must be zero or greater")

    async def http_ingest(event):
        request = urllib.request.Request(target_url, data=json.dumps(event).encode(), headers={"Content-Type":"application/json"}, method="POST")
        try:
            def send():
                with urllib.request.urlopen(request, timeout=10) as response:
                    if not 200 <= response.status < 300:
                        raise RuntimeError(f"ingestion returned HTTP {response.status}")
            await asyncio.to_thread(send)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"failed to submit simulated event {event.get('event_id', '<unknown>')}: {exc}") from exc

    if ingest is None and not target_url:
        raise ValueError("provide an ingestion callback or target URL")
    await AccountCompromiseScenario().run(ingest or http_ingest, delay)
    return 8

def main():
    parser = argparse.ArgumentParser(description="Submit clearly labelled synthetic incident events.")
    parser.add_argument("--scenario", default="account_compromise")
    parser.add_argument("--target-url", default="http://127.0.0.1:8000/api/v1/events")
    parser.add_argument("--delay", type=float, default=0.1)
    args = parser.parse_args()
    try:
        sent = asyncio.run(run_scenario(args.scenario, target_url=args.target_url, delay=args.delay))
    except (RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Submitted {sent} simulated events for scenario '{args.scenario}'.")
if __name__ == "__main__": main()
