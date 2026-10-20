import logging
class BaseCollector:
    name="base"
    def __init__(self, ingest, enabled=True): self.ingest=ingest; self.enabled=enabled; self.available=True; self.logger=logging.getLogger(self.name)
    async def collect(self): raise NotImplementedError
    async def run_once(self):
        if not self.enabled or not self.available: return
        try:
            for raw in await self.collect() or []: await self.ingest(raw)
        except Exception as exc: self.logger.warning("collector unavailable: %s",exc)
