import platform, socket, time, uuid, psutil
from datetime import datetime, timezone
from backend.collectors.base import BaseCollector
class SystemInfoCollector(BaseCollector):
    name="system_info"
    async def collect(self): return []
    async def snapshot(self):
        boot=psutil.boot_time(); vm=psutil.virtual_memory()
        return {"snapshot_id":str(uuid.uuid4()),"captured_at":datetime.now(timezone.utc),"hostname":socket.gethostname(),"os_name":platform.system(),"os_version":platform.version(),"cpu_count":psutil.cpu_count(),"memory_total_gb":round(vm.total/1024**3,2),"uptime_seconds":int(time.time()-boot),"metadata":{"python":platform.python_version()}}
