import psutil
from backend.collectors.base import BaseCollector
class ProcessCollector(BaseCollector):
    name="process"; previous=set()
    async def collect(self):
        current={p.info["pid"]:(p.info.get("name") or "unknown",p.info.get("username")) for p in psutil.process_iter(["pid","name","username"])}
        new=set(current)-self.previous; gone=self.previous-set(current); events=[]
        for pid in new: events.append({"event_type":"process_start","source":self.name,"process_name":current[pid][0],"user_name":current[pid][1],"action":"process_start","target":str(pid)})
        for pid in gone: events.append({"event_type":"process_stop","source":self.name,"action":"process_stop","target":str(pid)})
        self.previous=set(current); return events
