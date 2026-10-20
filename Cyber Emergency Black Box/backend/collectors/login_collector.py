from backend.collectors.base import BaseCollector
class LoginCollector(BaseCollector):
    name="login"
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        try: import win32evtlog  # noqa: F401
        except ImportError: self.available=False; self.logger.warning("pywin32 unavailable; login collector disabled")
    async def collect(self):
        # Event-log polling is deliberately optional: Windows audit policy governs availability.
        return []
