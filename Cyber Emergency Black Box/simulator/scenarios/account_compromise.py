import asyncio
from datetime import datetime, timedelta, timezone
class AccountCompromiseScenario:
    name="account_compromise"
    async def run(self, ingest, delay=0.1):
        now=datetime.now(timezone.utc); base={"source":"simulator","is_simulated":True,"user_name":"demo_user"}
        rows=[("login_failure",{}),("login_failure",{}),("login_failure",{}),("login_success",{}),("process_start",{"process_name":"archive-tool.exe"}),("file_modified",{"process_name":"archive-tool.exe","target":"C:/demo/records.csv"}),("network_connection",{"process_name":"archive-tool.exe","destination_ip":"203.0.113.10","destination_port":443,"protocol":"tcp"})]
        for index,(kind,extra) in enumerate(rows):
            await ingest({**base,**extra,"event_type":kind,"action":kind,"timestamp":now+timedelta(seconds=index*30)})
            await asyncio.sleep(delay)
