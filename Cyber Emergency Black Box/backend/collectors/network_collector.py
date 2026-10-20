import psutil
from backend.collectors.base import BaseCollector
class NetworkCollector(BaseCollector):
    name="network"; previous=set()
    async def collect(self):
        events=[]; current=set()
        for c in psutil.net_connections(kind="inet"):
            if c.status != psutil.CONN_ESTABLISHED or not c.raddr: continue
            key=(c.pid,str(c.laddr),str(c.raddr)); current.add(key)
            if key not in self.previous:
                events.append({"event_type":"network_connection","source":self.name,"action":"network_connection","target":str(c.pid),"source_ip":getattr(c.laddr,"ip",None),"destination_ip":getattr(c.raddr,"ip",None),"destination_port":getattr(c.raddr,"port",None),"protocol":"tcp"})
        self.previous=current; return events
