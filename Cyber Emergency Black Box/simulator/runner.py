"""Run simulator scenarios against a callback or the live local API."""
import argparse
import asyncio
import json
import urllib.request
from simulator.scenarios.account_compromise import AccountCompromiseScenario


async def run_scenario(scenario: str, ingest=None, target_url: str | None = None, delay: float = 0.1):
    if scenario != "account_compromise": raise ValueError(f"unknown scenario: {scenario}")
    async def http_ingest(event):
        request = urllib.request.Request(target_url, data=json.dumps(event).encode(), headers={"Content-Type":"application/json"}, method="POST")
        await asyncio.to_thread(urllib.request.urlopen, request, timeout=10)
    if ingest is None and not target_url: raise ValueError("provide an ingestion callback or target URL")
    await AccountCompromiseScenario().run(ingest or http_ingest, delay)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--scenario", default="account_compromise"); parser.add_argument("--target-url", default="http://127.0.0.1:8000/api/v1/events"); parser.add_argument("--delay", type=float, default=0.1)
    args = parser.parse_args(); asyncio.run(run_scenario(args.scenario, target_url=args.target_url, delay=args.delay))
if __name__ == "__main__": main()
