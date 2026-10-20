from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from backend.collectors.base import BaseCollector
class _Handler(FileSystemEventHandler):
    def __init__(self, output, excluded): self.output=output; self.excluded=excluded
    def _push(self,event,kind):
        if event.is_directory or Path(event.src_path).suffix.lower() in self.excluded: return
        self.output.append({"event_type":kind,"source":"file","action":kind,"target":event.src_path})
    def on_created(self,e): self._push(e,"file_created")
    def on_modified(self,e): self._push(e,"file_modified")
    def on_deleted(self,e): self._push(e,"file_deleted")
class FileCollector(BaseCollector):
    name="file"
    def __init__(self, ingest, paths=(), excluded=(".pyc",".tmp",".swp",".log"), enabled=True):
        super().__init__(ingest,enabled); self.events=[]; self.observer=Observer(); self.handler=_Handler(self.events,set(excluded))
        for path in paths:
            if Path(path).exists(): self.observer.schedule(self.handler,path,recursive=True)
    def start(self):
        if self.enabled and not self.observer.is_alive(): self.observer.start()
    def stop(self):
        if self.observer.is_alive(): self.observer.stop(); self.observer.join(timeout=2)
    async def collect(self):
        events,self.events=self.events,[]; return events
