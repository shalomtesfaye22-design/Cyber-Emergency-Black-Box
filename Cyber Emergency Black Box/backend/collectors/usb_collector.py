from backend.collectors.base import BaseCollector
class USBCollector(BaseCollector):
    name="usb"
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs); self.available=False
        self.logger.warning("USB collection is optional and unavailable without a configured WMI provider")
    async def collect(self): return []
